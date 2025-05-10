module "s3_cloudfront_website" {
  source = "../../modules/aws_s3_cloudfront"

  bucket_name         = var.bucket_name
  environment         = var.environment
  default_root_object = var.default_root_object
  error_document      = var.error_document
  domain_name         = var.domain_name
  zone_id             = var.zone_id
  price_class         = var.price_class
  region              = var.region
  tags                = var.tags
}

# Create IAM user for website content management
resource "aws_iam_user" "website_deployer" {
  name = "website-deployer-${var.bucket_name}"
  path = "/system/"

  tags = merge(
    {
      Name = "website-deployer-${var.bucket_name}"
    },
    var.tags
  )
}

# Create access key for the IAM user
resource "aws_iam_access_key" "website_deployer" {
  user = aws_iam_user.website_deployer.name
}

# Create policy for the IAM user to manage the S3 bucket
resource "aws_iam_user_policy" "website_deployer_policy" {
  name = "website-deployer-policy-${var.bucket_name}"
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
          module.s3_cloudfront_website.website_bucket_arn,
          "${module.s3_cloudfront_website.website_bucket_arn}/*"
        ]
      },
      {
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Effect   = "Allow"
        Resource = module.s3_cloudfront_website.cloudfront_distribution_arn
      }
    ]
  })
}

# Create sample website content
resource "local_file" "sample_index" {
  content  = <<-EOT
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Static Website - AgentX Deployed</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background: linear-gradient(135deg, #6e8efb, #a777e3);
          color: white;
        }
        .container {
          text-align: center;
          padding: 2rem;
          background-color: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
          margin-bottom: 1rem;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Welcome to Your Static Website!</h1>
        <p>Successfully deployed with AgentX using AWS S3 and CloudFront.</p>
      </div>
    </body>
    </html>
  EOT
  filename = "${path.module}/sample_website/index.html"
}

resource "local_file" "sample_error" {
  content  = <<-EOT
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Error - Page Not Found</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background-color: #f5f5f5;
          color: #333;
        }
        .container {
          text-align: center;
          padding: 2rem;
          background-color: white;
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          max-width: 90%;
          width: 500px;
        }
        h1 {
          color: #e74c3c;
        }
        .back-link {
          margin-top: 1rem;
          display: inline-block;
          color: #3498db;
          text-decoration: none;
        }
        .back-link:hover {
          text-decoration: underline;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for does not exist or has been moved.</p>
        <a href="/" class="back-link">Return to Homepage</a>
      </div>
    </body>
    </html>
  EOT
  filename = "${path.module}/sample_website/error.html"
}

# Upload sample content to S3
resource "null_resource" "upload_website" {
  depends_on = [
    module.s3_cloudfront_website,
    local_file.sample_index,
    local_file.sample_error
  ]

  provisioner "local-exec" {
    command = <<EOT
      aws s3 sync ${path.module}/sample_website/ s3://${module.s3_cloudfront_website.website_bucket_name}/ --region ${var.region}
    EOT
  }
}

# Create CloudFront cache invalidation after content upload
resource "null_resource" "invalidate_cache" {
  depends_on = [null_resource.upload_website]

  provisioner "local-exec" {
    command = <<EOT
      aws cloudfront create-invalidation --distribution-id ${module.s3_cloudfront_website.cloudfront_distribution_id} --paths "/*" --region ${var.region}
    EOT
  }
}