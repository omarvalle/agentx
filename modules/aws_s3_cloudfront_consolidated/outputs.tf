output "website_bucket_name" {
  description = "Name of the S3 bucket hosting the websites"
  value       = aws_s3_bucket.website_bucket.bucket
}

output "website_bucket_arn" {
  description = "ARN of the S3 bucket hosting the websites"
  value       = aws_s3_bucket.website_bucket.arn
}

output "website_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.website_bucket.bucket_regional_domain_name
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
  description = "The URL for accessing the websites via the custom domain (if provided)"
  value       = var.domain_name != null ? "https://${var.domain_name}" : null
}

output "certificate_validation_options" {
  description = "DNS records required for certificate validation (if a custom domain is used)"
  value       = var.domain_name != null ? aws_acm_certificate.website[0].domain_validation_options : null
}

output "website_urls_by_folder" {
  description = "Map of folder names to their CloudFront URLs"
  value       = {
    for folder in var.website_folders :
    folder => var.domain_name != null ? "https://${var.domain_name}/${folder}/" : "https://${aws_cloudfront_distribution.website.domain_name}/${folder}/"
  }
}

output "certificate_arn" {
  description = "ARN of the ACM certificate (if custom domain was provided)"
  value       = var.domain_name != null ? aws_acm_certificate.website[0].arn : null
}

output "deployment_instructions" {
  description = "Instructions for deploying content to the websites"
  value       = <<-EOT
    To deploy content to your static websites in this consolidated deployment:

    1. Set up AWS CLI credentials for the deployment user
       aws configure --profile website-deployer
       # When prompted, enter the access key and secret key from the IAM user created

    2. Upload website content to the appropriate folder:
       aws s3 sync ./website-content/ s3://${aws_s3_bucket.website_bucket.bucket}/FOLDER_NAME/ --profile website-deployer

    3. Invalidate CloudFront cache:
       aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.website.id} --paths "/FOLDER_NAME/*" --profile website-deployer

    Your websites are accessible at:
    ${join("\n    ", [for folder in var.website_folders : "- ${folder}: https://${aws_cloudfront_distribution.website.domain_name}/${folder}/"])}
    ${var.domain_name != null ? join("\n    ", [for folder in var.website_folders : "- ${folder}: https://${var.domain_name}/${folder}/"]) : ""}
  EOT
} 