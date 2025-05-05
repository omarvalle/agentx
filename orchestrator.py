import os
import json
import logging
import subprocess
import time
from typing import Dict, Any

# Configure logging
logger = logging.getLogger('AgentX')

class WebsiteDeploymentOrchestrator:
    """Orchestrator for deploying static websites to AWS using S3 and CloudFront."""
    
    def __init__(self, aws_region="us-east-1"):
        """Initialize the website deployment orchestrator.
        
        Args:
            aws_region (str): The AWS region to deploy to
        """
        self.aws_region = aws_region
        self.terraform_base_dir = "./terraform_deployments"
        os.makedirs(self.terraform_base_dir, exist_ok=True)
    
    def deploy_website(self, website_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a static website to AWS using Terraform.
        
        Args:
            website_config (dict): Configuration for the website deployment
                Required keys:
                - bucket_name: Name of the S3 bucket to create
                - environment: Deployment environment (dev, staging, prod)
                
                Optional keys:
                - domain_name: Custom domain name
                - zone_id: Route53 zone ID for custom domain
                - content_dir: Directory containing website content
        
        Returns:
            dict: Result of the deployment operation
        """
        logger.info(f"Starting deployment of website: {website_config.get('bucket_name')}")
        
        # Validate the required configuration
        if not website_config.get('bucket_name'):
            error_msg = "Missing required configuration: bucket_name"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Set defaults for optional parameters
        website_config.setdefault("environment", "dev")
        
        # Create a directory for this deployment
        deployment_dir = os.path.join(self.terraform_base_dir, website_config['bucket_name'])
        if not os.path.exists(deployment_dir):
            os.makedirs(deployment_dir)
        
        # Generate Terraform configuration
        try:
            self._generate_terraform_config(deployment_dir, website_config)
            logger.info(f"Generated Terraform configuration in {deployment_dir}")
        except Exception as e:
            error_msg = f"Failed to generate Terraform configuration: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Initialize Terraform
        try:
            init_result = self._run_terraform_command(deployment_dir, "init", capture_output=True)
            if init_result["returncode"] != 0:
                error_msg = f"Terraform initialization failed: {init_result.get('stderr', '')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            logger.info("Terraform initialization successful")
        except Exception as e:
            error_msg = f"Error during Terraform initialization: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Apply Terraform configuration
        try:
            apply_result = self._run_terraform_command(deployment_dir, "apply", args=["-auto-approve"], capture_output=True)
            if apply_result["returncode"] != 0:
                error_msg = f"Terraform apply failed: {apply_result.get('stderr', '')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            logger.info("Terraform apply successful")
        except Exception as e:
            error_msg = f"Error during Terraform apply: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Get Terraform outputs
        try:
            output_result = self._run_terraform_command(deployment_dir, "output", args=["-json"], capture_output=True)
            if output_result["returncode"] == 0:
                outputs = json.loads(output_result["stdout"])
            else:
                outputs = {}
                logger.warning(f"Failed to get Terraform outputs: {output_result.get('stderr', '')}")
        except Exception as e:
            logger.warning(f"Error getting Terraform outputs: {str(e)}")
            outputs = {}
        
        # Format the success result
        result = {
            "success": True,
            "website_url": outputs.get("website_url", {}).get("value", ""),
            "custom_domain_url": outputs.get("custom_domain_url", {}).get("value", ""),
            "s3_bucket": outputs.get("s3_bucket_name", {}).get("value", ""),
            "cloudfront_distribution": outputs.get("cloudfront_distribution_id", {}).get("value", ""),
            "deployment_instructions": outputs.get("deployment_instructions", {}).get("value", ""),
            "deployment_dir": deployment_dir
        }
        
        # If content_dir was provided, upload the content
        if website_config.get("content_dir") and os.path.exists(website_config["content_dir"]):
            try:
                self._upload_website_content(
                    content_dir=website_config["content_dir"],
                    s3_bucket=result["s3_bucket"],
                    cloudfront_distribution_id=result["cloudfront_distribution"]
                )
                logger.info(f"Uploaded website content from {website_config['content_dir']}")
            except Exception as e:
                logger.warning(f"Failed to upload website content: {str(e)}")
        
        logger.info(f"Website deployment completed successfully: {result['website_url']}")
        return result
    
    def destroy_website(self, bucket_name: str) -> Dict[str, Any]:
        """Destroy a previously deployed website.
        
        Args:
            bucket_name (str): Name of the S3 bucket/deployment to destroy
        
        Returns:
            dict: Result of the destruction operation
        """
        logger.info(f"Starting destruction of website deployment: {bucket_name}")
        
        # Check if the deployment directory exists
        deployment_dir = os.path.join(self.terraform_base_dir, bucket_name)
        if not os.path.exists(deployment_dir):
            error_msg = f"Deployment directory not found: {deployment_dir}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Run terraform destroy
        try:
            destroy_result = self._run_terraform_command(deployment_dir, "destroy", args=["-auto-approve"], capture_output=True)
            if destroy_result["returncode"] != 0:
                error_msg = f"Terraform destroy failed: {destroy_result.get('stderr', '')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            logger.info("Terraform destroy successful")
            
            return {
                "success": True,
                "message": f"Website deployment {bucket_name} successfully destroyed"
            }
        except Exception as e:
            error_msg = f"Error during Terraform destroy: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _run_terraform_command(self, working_dir: str, command: str, args=None, capture_output=False) -> Dict[str, Any]:
        """Run a Terraform command in the specified directory.
        
        Args:
            working_dir (str): Directory to run the command in
            command (str): Terraform command to run (init, apply, destroy, etc.)
            args (list): Additional arguments for the command
            capture_output (bool): Whether to capture the command output
        
        Returns:
            dict: Command result including returncode, stdout, stderr
        """
        if args is None:
            args = []
        
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to the terraform directory
            os.chdir(working_dir)
            
            # Prepare the command
            cmd = ["terraform", command] + args
            logger.info(f"Running Terraform command: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True
            )
            
            # Prepare result dictionary
            cmd_result = {
                "returncode": result.returncode
            }
            
            if capture_output:
                cmd_result["stdout"] = result.stdout
                cmd_result["stderr"] = result.stderr
            
            return cmd_result
        finally:
            # Restore original directory
            os.chdir(original_dir)
    
    def _generate_terraform_config(self, deployment_dir: str, website_config: Dict[str, Any]) -> None:
        """Generate Terraform configuration files for the website deployment.
        
        Args:
            deployment_dir (str): Directory to create the files in
            website_config (dict): Website configuration
        """
        # Main Terraform file
        main_tf = f"""
module "static_website" {{
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
}}

# Create IAM user for website content management
resource "aws_iam_user" "website_deployer" {{
  name = "website-deployer-${{var.bucket_name}}"
  path = "/system/"

  tags = merge(
    {{
      Name = "website-deployer-${{var.bucket_name}}"
    }},
    var.tags
  )
}}

# Create access key for the IAM user
resource "aws_iam_access_key" "website_deployer" {{
  user = aws_iam_user.website_deployer.name
}}

# Create policy for the IAM user to manage the S3 bucket
resource "aws_iam_user_policy" "website_deployer_policy" {{
  name = "website-deployer-policy-${{var.bucket_name}}"
  user = aws_iam_user.website_deployer.name

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          module.static_website.website_bucket_arn,
          "${{module.static_website.website_bucket_arn}}/*"
        ]
      }},
      {{
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Effect   = "Allow"
        Resource = module.static_website.cloudfront_distribution_arn
      }}
    ]
  }})
}}

# Create sample website content
resource "local_file" "sample_index" {{
  content  = <<-EOT
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{website_config.get('description', 'Static Website')}</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background: linear-gradient(135deg, #6e8efb, #a777e3);
          color: white;
        }}
        .container {{
          text-align: center;
          padding: 2rem;
          background-color: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
          margin-bottom: 1rem;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Welcome to {website_config.get('description', 'Static Website')}!</h1>
        <p>Successfully deployed with AgentX using AWS S3 and CloudFront.</p>
      </div>
    </body>
    </html>
  EOT
  filename = "${{path.module}}/sample_website/index.html"
}}

resource "local_file" "sample_error" {{
  content  = <<-EOT
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Error - Page Not Found</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background-color: #f5f5f5;
          color: #333;
        }}
        .container {{
          text-align: center;
          padding: 2rem;
          background-color: white;
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          max-width: 90%;
          width: 500px;
        }}
        h1 {{
          color: #e74c3c;
        }}
        .back-link {{
          margin-top: 1rem;
          display: inline-block;
          color: #3498db;
          text-decoration: none;
        }}
        .back-link:hover {{
          text-decoration: underline;
        }}
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
  filename = "${{path.module}}/sample_website/error.html"
}}

# Upload sample content to S3
resource "null_resource" "upload_website" {{
  depends_on = [
    module.static_website,
    local_file.sample_index,
    local_file.sample_error
  ]

  provisioner "local-exec" {{
    command = <<EOT
      aws s3 sync ${{path.module}}/sample_website/ s3://${{module.static_website.website_bucket_name}}/ --region ${{var.region}}
    EOT
  }}
}}

# Create CloudFront cache invalidation after content upload
resource "null_resource" "invalidate_cache" {{
  depends_on = [null_resource.upload_website]

  provisioner "local-exec" {{
    command = <<EOT
      aws cloudfront create-invalidation --distribution-id ${{module.static_website.cloudfront_distribution_id}} --paths "/*" --region ${{var.region}}
    EOT
  }}
}}
"""

        # Variables file
        variables_tf = """
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
"""

        # Outputs file
        outputs_tf = """
output "website_url" {
  description = "URL for accessing the website via CloudFront"
  value       = module.static_website.website_url
}

output "custom_domain_url" {
  description = "URL for accessing the website via the custom domain (if provided)"
  value       = module.static_website.custom_domain_url
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the website"
  value       = module.static_website.website_bucket_name
}

output "cloudfront_distribution_id" {
  description = "The identifier for the CloudFront distribution"
  value       = module.static_website.cloudfront_distribution_id
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
   aws s3 sync ./my-website/ s3://${module.static_website.website_bucket_name}/ --profile website-deployer

3. Invalidate CloudFront cache:
   aws cloudfront create-invalidation --distribution-id ${module.static_website.cloudfront_distribution_id} --paths "/*" --profile website-deployer

Your website is accessible at: ${module.static_website.website_url}
EOT
}
"""

        # Terraform variables file
        terraform_tfvars = f"""
bucket_name         = "{website_config['bucket_name']}"
environment         = "{website_config.get('environment', 'dev')}"
domain_name         = {f'"{website_config["domain_name"]}"' if website_config.get('domain_name') else "null"}
zone_id             = {f'"{website_config["zone_id"]}"' if website_config.get('zone_id') else "null"}
default_root_object = "index.html"
error_document      = "error.html"
price_class         = "{website_config.get('price_class', 'PriceClass_100')}"
region              = "{website_config.get('region', self.aws_region)}"
tags                = {{
  "Provisioned" = "AgentX"
  "Description" = "{website_config.get('description', 'Static Website')}"
}}
"""

        # Write the files to the deployment directory
        with open(os.path.join(deployment_dir, "main.tf"), "w") as f:
            f.write(main_tf)
            
        with open(os.path.join(deployment_dir, "variables.tf"), "w") as f:
            f.write(variables_tf)
            
        with open(os.path.join(deployment_dir, "outputs.tf"), "w") as f:
            f.write(outputs_tf)
            
        with open(os.path.join(deployment_dir, "terraform.tfvars"), "w") as f:
            f.write(terraform_tfvars)
    
    def _upload_website_content(self, content_dir: str, s3_bucket: str, cloudfront_distribution_id: str) -> None:
        """Upload website content to S3 and invalidate CloudFront cache.
        
        Args:
            content_dir (str): Directory containing website content
            s3_bucket (str): S3 bucket to upload to
            cloudfront_distribution_id (str): CloudFront distribution ID
        """
        # Upload content to S3
        upload_cmd = f"aws s3 sync {content_dir} s3://{s3_bucket}/ --region {self.aws_region}"
        logger.info(f"Uploading website content: {upload_cmd}")
        
        upload_result = subprocess.run(
            upload_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if upload_result.returncode != 0:
            error_msg = f"Failed to upload website content: {upload_result.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Invalidate CloudFront cache
        invalidate_cmd = f"aws cloudfront create-invalidation --distribution-id {cloudfront_distribution_id} --paths \"/*\" --region {self.aws_region}"
        logger.info(f"Invalidating CloudFront cache: {invalidate_cmd}")
        
        invalidate_result = subprocess.run(
            invalidate_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if invalidate_result.returncode != 0:
            error_msg = f"Failed to invalidate CloudFront cache: {invalidate_result.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg) 