variable "project_name" {
  description = "Name of the project, used as a prefix for all resources"
  type        = string
}

variable "project_id" {
  description = "Project ID for tagging resources, used to identify all resources created for the project"
  type        = string
  default     = null
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "database_subnet_cidrs" {
  description = "List of CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.5.0/24", "10.0.6.0/24"]
}

# RDS PostgreSQL settings
variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "app"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "postgres"
}

variable "postgres_version" {
  description = "Version of PostgreSQL to use"
  type        = string
  default     = "14"
}

variable "db_instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for the RDS instance in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum storage for the RDS instance in GB (for autoscaling)"
  type        = number
  default     = 100
}

variable "has_database" {
  description = "Whether the application needs a database"
  type        = bool
  default     = false
}

variable "db_type" {
  description = "Type of database to use (postgres, mysql, etc.)"
  type        = string
  default     = "postgres"
}

# ECS and Container settings
variable "container_image" {
  description = "Docker image to use for the container"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 3000
}

variable "container_cpu" {
  description = "CPU units for the container (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for the container in MB"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 1
}

variable "min_capacity" {
  description = "Minimum number of container instances for autoscaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of container instances for autoscaling"
  type        = number
  default     = 5
}

variable "health_check_path" {
  description = "Path for health checks"
  type        = string
  default     = "/"
}

variable "container_environment" {
  description = "Environment variables for the container"
  type        = list(object({
    name  = string
    value = string
  }))
  default     = []
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
} 