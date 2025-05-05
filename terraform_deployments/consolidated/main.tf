
module "consolidated_website" {
  source = "../../modules/aws_s3_cloudfront_consolidated"

  bucket_name         = "agentx-websites-1746424372"
  environment         = "prod"
  default_root_object = "index.html"
  error_document      = "error.html"
  domain_name         = null
  zone_id             = null
  website_folders     = ["website_happy_graduation"]
  price_class         = "PriceClass_100"
  region              = "us-east-1"
  tags                = {
    "Provisioned" = "AgentX"
    "Description" = "Consolidated static website hosting"
  }
}

# Use a consistent IAM user name for all consolidated deployments
locals {
  iam_user_name = "agentx-website-deployer"
}

# Create IAM user for website content management (with handling for existing user)
resource "aws_iam_user" "website_deployer" {
  name = local.iam_user_name
  path = "/system/"

  tags = {
    Name = local.iam_user_name
    Provisioned = "AgentX"
  }

  # Prevent errors if the user already exists
  lifecycle {
    ignore_changes = [tags]
  }
}

# Create access key for the IAM user (only if not already exists)
resource "aws_iam_access_key" "website_deployer" {
  user = aws_iam_user.website_deployer.name

  # This prevents the access key from being recreated on subsequent runs
  lifecycle {
    ignore_changes = all
  }
}

# Create policy for the IAM user to manage the S3 bucket
resource "aws_iam_user_policy" "website_deployer_policy" {
  name = "website-deployer-policy-agentx-websites-1746424372"
  user = aws_iam_user.website_deployer.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          module.consolidated_website.website_bucket_arn,
          "${module.consolidated_website.website_bucket_arn}/*"
        ]
      },
      {
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Effect   = "Allow"
        Resource = module.consolidated_website.cloudfront_distribution_arn
      }
    ]
  })
}
