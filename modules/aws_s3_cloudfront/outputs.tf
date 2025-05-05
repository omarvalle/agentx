output "website_bucket_name" {
  description = "Name of the S3 bucket hosting the website"
  value       = aws_s3_bucket.website.id
}

output "website_bucket_arn" {
  description = "ARN of the S3 bucket hosting the website"
  value       = aws_s3_bucket.website.arn
}

output "website_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.website.bucket_regional_domain_name
}

output "cloudfront_distribution_id" {
  description = "The identifier for the CloudFront distribution"
  value       = aws_cloudfront_distribution.website.id
}

output "cloudfront_distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.website.arn
}

output "cloudfront_distribution_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "website_url" {
  description = "URL for accessing the website via CloudFront"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "custom_domain_url" {
  description = "URL for accessing the website via the custom domain (if provided)"
  value       = var.domain_name != null ? "https://${var.domain_name}" : null
}

output "certificate_validation_options" {
  description = "DNS records required for certificate validation (if a custom domain is used)"
  value       = var.domain_name != null ? aws_acm_certificate.website[0].domain_validation_options : null
} 