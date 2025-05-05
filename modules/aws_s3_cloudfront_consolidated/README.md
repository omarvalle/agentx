# AWS S3 and CloudFront Consolidated Module

This Terraform module creates infrastructure for hosting multiple static websites using a single S3 bucket with folder separation and a single CloudFront distribution with path patterns.

## Key Features

- Single S3 bucket with folders for multiple websites
- Private S3 bucket with CloudFront Origin Access Control (OAC)
- Single CloudFront distribution with path patterns for each website folder
- Support for custom domains with auto-managed SSL certificates
- Secure defaults including HTTPS redirection and S3 server-side encryption
- Shared infrastructure for cost-effective hosting of multiple sites

## Architecture

```
┌─────────────┐     ┌───────────────┐     ┌────────────────┐
│  CloudFront │     │   S3 Bucket   │     │ ACM Certificate│
│ Distribution │←───→│ (Private)     │     │ (Optional)     │
└─────────────┘     └───────────────┘     └────────────────┘
       ↑                    ↑                     ↑
       │                    │                     │
       │                    │                     │
┌──────────────────────────────────────────────────────┐
│                   OAC & IAM Policy                    │
└──────────────────────────────────────────────────────┘
```

## Usage

```hcl
module "consolidated_website" {
  source = "./modules/aws_s3_cloudfront_consolidated"

  bucket_name     = "my-websites-bucket"
  environment     = "prod"
  website_folders = ["site1", "site2", "blog"]
  
  # Optional custom domain
  domain_name     = "cdn.example.com"
  zone_id         = "Z1234567890ABC"
}
```

## Accessing Your Websites

Once deployed, your websites will be accessible at:

- Primary CloudFront URL: `https://<cloudfront-domain>/<folder-name>/`
- Custom domain (if configured): `https://<custom-domain>/<folder-name>/`

## Adding New Website Folders

To add a new website folder:

1. Update the `website_folders` variable to include the new folder name
2. Apply the Terraform changes
3. Upload content to the new folder in the S3 bucket

## Requirements

- AWS provider >= 4.0
- Terraform >= 1.0
- AWS CLI for deployments

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| bucket_name | Name of the S3 bucket for the websites | `string` | n/a | yes |
| environment | Deployment environment (dev, staging, prod) | `string` | `"dev"` | no |
| website_folders | List of folder names for each website | `list(string)` | `[]` | no |
| domain_name | Custom domain name for CloudFront | `string` | `null` | no |
| zone_id | Route53 zone ID for the domain | `string` | `null` | no |
| default_root_object | Default root object for CloudFront | `string` | `"index.html"` | no |
| error_document | Error document for 404/403 errors | `string` | `"error.html"` | no |
| price_class | CloudFront price class | `string` | `"PriceClass_100"` | no |
| region | AWS region for resources | `string` | `"us-east-1"` | no |
| tags | Additional tags for resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| website_bucket_name | S3 bucket name for the websites |
| website_bucket_arn | ARN of the S3 bucket |
| cloudfront_distribution_id | CloudFront distribution ID |
| cloudfront_domain_name | CloudFront domain name |
| cloudfront_distribution_arn | CloudFront distribution ARN |
| custom_domain_url | Custom domain URL (if configured) |

## Deployment Instructions

To deploy content to your website folders:

```bash
# Upload content to a specific folder
aws s3 sync ./site1-content/ s3://my-websites-bucket/site1/ --profile website-deployer

# Invalidate CloudFront cache for that folder
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/site1/*" --profile website-deployer
```

## Security Considerations

This module implements several security best practices:

- S3 bucket is private with all public access blocked
- CloudFront OAC for secure S3 access
- HTTPS enforcement with TLS 1.2
- Server-side encryption for S3 objects
- IAM permissions follow least privilege principle

## Cost Optimization

The consolidated approach offers cost savings by:

1. Using a single S3 bucket instead of multiple buckets
2. Sharing a CloudFront distribution across multiple websites
3. Reducing the number of Route53 records needed
4. Minimizing CloudFront invalidation costs 