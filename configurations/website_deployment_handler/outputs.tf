output "website_url" {
  description = "URL for accessing the website via CloudFront"
  value       = module.s3_cloudfront_website.website_url
}

output "custom_domain_url" {
  description = "URL for accessing the website via the custom domain (if provided)"
  value       = module.s3_cloudfront_website.custom_domain_url
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the website"
  value       = module.s3_cloudfront_website.website_bucket_name
}

output "cloudfront_distribution_id" {
  description = "The identifier for the CloudFront distribution"
  value       = module.s3_cloudfront_website.cloudfront_distribution_id
}

output "website_deployer_user" {
  description = "IAM user name for website content management"
  value       = aws_iam_user.website_deployer.name
}

output "website_deployer_access_key" {
  description = "Access key ID for the website deployer IAM user"
  value       = aws_iam_access_key.website_deployer.id
  sensitive   = true
}

output "website_deployer_secret_key" {
  description = "Secret access key for the website deployer IAM user"
  value       = aws_iam_access_key.website_deployer.secret
  sensitive   = true
}

output "deployment_instructions" {
  description = "Instructions for deploying content to the website"
  value       = <<EOT
To deploy content to your static website:

1. Set up AWS CLI credentials for the deployment user:
   aws configure --profile website-deployer
   # When prompted, enter the access key and secret key from the Terraform outputs

2. Upload website content:
   aws s3 sync ./my-website/ s3://${module.s3_cloudfront_website.website_bucket_name}/ --profile website-deployer

3. Invalidate CloudFront cache:
   aws cloudfront create-invalidation --distribution-id ${module.s3_cloudfront_website.cloudfront_distribution_id} --paths "/*" --profile website-deployer

Your website is accessible at: ${module.s3_cloudfront_website.website_url}
EOT
} 