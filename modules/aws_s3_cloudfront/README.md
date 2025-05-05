# AWS S3 and CloudFront Website Module

This Terraform module creates an S3 bucket for static website hosting and a CloudFront distribution that serves the content securely. It includes support for custom domains with SSL certificates.

## Features

- S3 bucket configured with proper security settings for website hosting
- CloudFront distribution with Origin Access Control (OAC) for secure S3 access
- Optional custom domain support with ACM certificate and Route53 record
- Custom error page handling
- IPv6 support
- Versioning enabled on the S3 bucket
- Server-side encryption for the S3 bucket

## Usage

```hcl
module "static_website" {
  source = "./modules/aws_s3_cloudfront"

  bucket_name         = "my-static-website"
  environment         = "prod"
  default_root_object = "index.html"
  error_document      = "error.html"
  
  # Optional: For custom domain
  domain_name         = "example.com"
  zone_id             = "Z1234567890ABCDEF"
}
```

### Uploading content to the S3 bucket

After deploying this module, you can upload your website content to the S3 bucket:

```bash
aws s3 sync ./website s3://my-static-website/
```

## Required Permissions

To deploy this module, you need IAM permissions for:

- S3 bucket creation and management
- CloudFront distribution creation and management
- ACM certificate creation (if using a custom domain)
- Route53 record creation (if using a custom domain)

## Inputs

| Name                | Description                                          | Type         | Default        | Required |
|---------------------|------------------------------------------------------|--------------|----------------|----------|
| bucket_name         | Name of the S3 bucket that will host the website     | string       | -              | yes      |
| environment         | Environment name (e.g., dev, staging, prod)          | string       | "dev"          | no       |
| domain_name         | Optional custom domain name for the website          | string       | null           | no       |
| zone_id             | Route53 zone ID for the domain                       | string       | null           | no       |
| default_root_object | Object that CloudFront returns for root URL requests | string       | "index.html"   | no       |
| error_document      | Error document to serve for 404/403 errors           | string       | "error.html"   | no       |
| price_class         | CloudFront distribution price class                  | string       | "PriceClass_100"| no      |
| region              | AWS region for resources that require a region       | string       | "us-east-1"    | no       |
| tags                | Additional tags to apply to resources                | map(string)  | {}             | no       |

## Outputs

| Name                                | Description                                                   |
|-------------------------------------|---------------------------------------------------------------|
| website_bucket_name                 | Name of the S3 bucket hosting the website                     |
| website_bucket_arn                  | ARN of the S3 bucket hosting the website                      |
| website_bucket_regional_domain_name | Regional domain name of the S3 bucket                         |
| cloudfront_distribution_id          | The identifier for the CloudFront distribution                |
| cloudfront_distribution_arn         | The ARN of the CloudFront distribution                        |
| cloudfront_distribution_domain_name | The domain name of the CloudFront distribution                |
| website_url                         | URL for accessing the website via CloudFront                  |
| custom_domain_url                   | URL for accessing the website via the custom domain           |
| certificate_validation_options      | DNS records required for certificate validation               | 