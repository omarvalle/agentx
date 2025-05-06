# AWS S3 and CloudFront Consolidated Deployment Module
# This module uses a single bucket with folders for each website

# Create a single S3 bucket for all websites
resource "aws_s3_bucket" "website_bucket" {
  bucket        = var.bucket_name
  force_destroy = true

  tags = merge({
    Name        = var.bucket_name
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "shared-infrastructure"
  }, var.tags)
}

resource "aws_s3_bucket_ownership_controls" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudFront OAC (Origin Access Control)
resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "oac-${var.bucket_name}"
  description                       = "OAC for ${var.bucket_name}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# S3 Bucket Policy - allow CloudFront to access content
resource "aws_s3_bucket_policy" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipalReadOnly"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website_bucket.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.website.arn
          }
        }
      }
    ]
  })
}

# SSL Certificate for custom domain (optional)
resource "aws_acm_certificate" "website" {
  count             = var.domain_name != null ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "website" {
  origin {
    domain_name              = aws_s3_bucket.website_bucket.bucket_regional_domain_name
    origin_id                = "S3-${var.bucket_name}"
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
    
    # Optional: You can use origin path to point to a specific folder in the bucket
    # origin_path              = "/${var.website_folder_name}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = var.default_root_object
  
  # Optional custom domain
  aliases = var.domain_name != null ? [var.domain_name] : []

  # Default cache behavior
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3-${var.bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    
    cache_policy_id          = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # CORS-S3Origin
    
    min_ttl     = 0
    default_ttl = 86400    # 1 day
    max_ttl     = 31536000 # 1 year
  }

  # Create additional cache behaviors for each website folder
  dynamic "ordered_cache_behavior" {
    for_each = var.website_folders
    content {
      path_pattern           = "${ordered_cache_behavior.value}/*"
      allowed_methods        = ["GET", "HEAD", "OPTIONS"]
      cached_methods         = ["GET", "HEAD", "OPTIONS"]
      target_origin_id       = "S3-${var.bucket_name}"
      viewer_protocol_policy = "redirect-to-https"
      
      cache_policy_id          = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
      origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # CORS-S3Origin
      
      min_ttl     = 0
      default_ttl = 86400    # 1 day
      max_ttl     = 31536000 # 1 year
    }
  }

  # Display custom error pages
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/${var.error_document}"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/${var.error_document}"
    error_caching_min_ttl = 10
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate configuration
  viewer_certificate {
    acm_certificate_arn      = var.domain_name != null ? aws_acm_certificate.website[0].arn : null
    ssl_support_method       = var.domain_name != null ? "sni-only" : null
    cloudfront_default_certificate = var.domain_name == null
    minimum_protocol_version       = var.domain_name != null ? "TLSv1.2_2021" : "TLSv1"
  }

  # Price class
  price_class = var.price_class

  tags = merge({
    Name        = "cf-${var.bucket_name}"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "shared-infrastructure"
  }, var.tags)
}

# Route53 DNS Record - only if domain name is provided
resource "aws_route53_record" "website" {
  count   = var.domain_name != null && var.zone_id != null ? 1 : 0
  zone_id = var.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.website.domain_name
    zone_id                = aws_cloudfront_distribution.website.hosted_zone_id
    evaluate_target_health = false
  }
} 