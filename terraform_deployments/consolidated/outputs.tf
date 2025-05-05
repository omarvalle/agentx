
output "website_bucket_name" {
  description = "Name of the S3 bucket hosting the websites"
  value       = module.consolidated_website.website_bucket_name
}

output "cloudfront_distribution_id" {
  description = "The identifier for the CloudFront distribution"
  value       = module.consolidated_website.cloudfront_distribution_id
}

output "cloudfront_domain" {
  description = "The domain name of the CloudFront distribution"
  value       = module.consolidated_website.cloudfront_distribution_domain_name
}

output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = module.consolidated_website.custom_domain_url
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
