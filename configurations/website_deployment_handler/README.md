# Static Website Deployment Handler for AgentX

This configuration implements a handler for deploying static websites to AWS using S3 and CloudFront through the AgentX platform. It leverages the aws_s3_cloudfront module to create all necessary infrastructure and provides deployment capabilities.

## Architecture

![Website Architecture Diagram](architecture.png)

This setup includes:

1. **Amazon S3 Bucket**: For storing the static website files securely
2. **Amazon CloudFront**: Content delivery network for fast global access
3. **Origin Access Control**: For secure S3 bucket access from CloudFront
4. **Optional Custom Domain**: With SSL certificate via ACM (if provided)
5. **IAM User**: Dedicated user for website content management

## Features

- Automatic deployment of sample website content
- CloudFront cache invalidation after content updates
- IAM user with limited permissions for content management
- Custom domain support with automatic SSL (optional)
- Detailed deployment instructions for website updates

## Usage

### Basic Usage

```hcl
module "my_website" {
  source = "./configurations/website_deployment_handler"

  bucket_name = "my-awesome-website"
  environment = "prod"
}
```

### With Custom Domain

```hcl
module "my_website" {
  source = "./configurations/website_deployment_handler"

  bucket_name = "my-awesome-website"
  environment = "prod"
  domain_name = "www.example.com"
  zone_id     = "Z1234567890ABCDEF"
}
```

## Integration with AgentX

When a user requests a static website through AgentX, the system can:

1. Generate a unique bucket name based on the user's requirements
2. Deploy the infrastructure using this configuration
3. Return the deployment instructions and website URL to the user
4. Optionally handle custom domain configuration if requested

## Updating Website Content

After initial deployment, users can update the website content using the dedicated IAM user credentials. The system generates specific deployment instructions that include:

1. Setting up AWS CLI with the provided credentials
2. Uploading files to the S3 bucket
3. Invalidating the CloudFront cache to ensure the latest content is served

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

| Name                      | Description                                             |
|---------------------------|---------------------------------------------------------|
| website_url               | URL for accessing the website via CloudFront            |
| custom_domain_url         | URL for accessing the website via the custom domain     |
| s3_bucket_name            | Name of the S3 bucket hosting the website               |
| cloudfront_distribution_id| The identifier for the CloudFront distribution          |
| website_deployer_user     | IAM user name for website content management            |
| website_deployer_access_key| Access key ID for the website deployer IAM user        |
| website_deployer_secret_key| Secret access key for the website deployer IAM user    |
| deployment_instructions   | Instructions for deploying content to the website       | 