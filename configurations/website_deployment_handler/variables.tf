variable "bucket_name" {
  description = "Name of the S3 bucket that will host the website"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "domain_name" {
  description = "Optional custom domain name for the website"
  type        = string
  default     = null
}

variable "zone_id" {
  description = "Route53 zone ID for the domain (required if domain_name is provided)"
  type        = string
  default     = null
}

variable "default_root_object" {
  description = "Object that CloudFront returns when an end user requests the root URL"
  type        = string
  default     = "index.html"
}

variable "error_document" {
  description = "Error document to serve when a 404 or 403 error occurs"
  type        = string
  default     = "error.html"
}

variable "price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_100" # Use only North America and Europe
}

variable "region" {
  description = "AWS region for resources that require a region setting"
  type        = string
  default     = "us-east-1" # North Virginia for CloudFront certificates
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
} 