# AWS ECS Fargate with RDS PostgreSQL Module

This module deploys a containerized application on AWS ECS using Fargate with a PostgreSQL RDS database. It's designed for applications that require both compute and database resources, such as web applications with a database backend.

## Features

- **ECS Fargate**: Serverless container orchestration without managing EC2 instances
- **RDS PostgreSQL**: Managed PostgreSQL database with automatic backups
- **VPC Configuration**: Creates a complete networking setup with public, private, and database subnets
- **Auto Scaling**: Automatically adjusts container instances based on CPU and memory usage
- **Load Balancer**: Distributes traffic across container instances
- **Secrets Management**: Securely stores database credentials in AWS Secrets Manager
- **Security**: Properly configured security groups and network access controls
- **Logging**: Container logs sent to CloudWatch Logs

## Usage

```hcl
module "todo_app" {
  source = "../../modules/aws_ecs_rds"

  project_name    = "todo-app"
  project_id      = "agentx-project-123456789"
  environment     = "dev"
  
  # Container settings
  container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/todo-app:latest"
  container_port  = 3000
  
  # Database settings
  db_name         = "todo_db"
  db_username     = "todo_user"
  
  # Add any custom tags
  tags = {
    Department = "Engineering"
    Owner      = "AgentX"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Name of the project, used as a prefix for all resources | string | n/a | yes |
| project_id | Project ID for tagging resources | string | null | no |
| environment | Environment (e.g., dev, staging, prod) | string | "dev" | no |
| region | AWS region to deploy resources | string | "us-east-1" | no |
| vpc_cidr | CIDR block for the VPC | string | "10.0.0.0/16" | no |
| availability_zones | List of availability zones to use | list(string) | ["us-east-1a", "us-east-1b"] | no |
| public_subnet_cidrs | List of CIDR blocks for public subnets | list(string) | ["10.0.1.0/24", "10.0.2.0/24"] | no |
| private_subnet_cidrs | List of CIDR blocks for private subnets | list(string) | ["10.0.3.0/24", "10.0.4.0/24"] | no |
| database_subnet_cidrs | List of CIDR blocks for database subnets | list(string) | ["10.0.5.0/24", "10.0.6.0/24"] | no |
| db_name | Name of the database to create | string | "app" | no |
| db_username | Username for the database | string | "postgres" | no |
| postgres_version | Version of PostgreSQL to use | string | "14" | no |
| db_instance_class | Instance class for the RDS instance | string | "db.t3.micro" | no |
| db_allocated_storage | Allocated storage for the RDS instance in GB | number | 20 | no |
| db_max_allocated_storage | Maximum storage for the RDS instance in GB (for autoscaling) | number | 100 | no |
| container_image | Docker image to use for the container | string | n/a | yes |
| container_port | Port the container listens on | number | 3000 | no |
| container_cpu | CPU units for the container (1024 = 1 vCPU) | number | 256 | no |
| container_memory | Memory for the container in MB | number | 512 | no |
| desired_count | Desired number of container instances | number | 1 | no |
| min_capacity | Minimum number of container instances for autoscaling | number | 1 | no |
| max_capacity | Maximum number of container instances for autoscaling | number | 5 | no |
| health_check_path | Path for health checks | string | "/" | no |
| container_environment | Environment variables for the container | list(object) | [] | no |
| certificate_arn | ARN of the SSL certificate for HTTPS (optional) | string | null | no |
| tags | Additional tags to apply to all resources | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC created |
| alb_dns_name | DNS name of the load balancer |
| alb_url | URL for accessing the application via the load balancer |
| db_instance_endpoint | Endpoint of the RDS instance |
| db_instance_address | Address of the RDS instance |
| db_name | Name of the database |
| db_username | Username for the database |
| db_secret_name | Name of the secret in AWS Secrets Manager containing database credentials |
| db_secret_arn | ARN of the secret in AWS Secrets Manager containing database credentials |
| ecs_cluster_name | Name of the ECS cluster |
| ecs_cluster_arn | ARN of the ECS cluster |
| ecs_service_name | Name of the ECS service |
| task_definition_arn | ARN of the task definition |
| task_execution_role_arn | ARN of the task execution role |
| deployment_instructions | Instructions for managing and updating the deployment |

## Notes

- The database password is automatically generated and stored in AWS Secrets Manager
- The application container gets the database connection information from Secrets Manager
- All resources are properly tagged with the project name, environment, and provided tags
- For production environments, consider increasing the instance sizes and enabling multi-AZ for RDS 