# AWS ECS Fargate and RDS PostgreSQL Deployment Module

# Generate a timestamp for resource names
locals {
  timestamp = formatdate("MMDDhhmmss", timestamp())
}

# Generate a random password for the database
resource "random_password" "db_password" {
  count = var.has_database ? 1 : 0
  
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store the password in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  count = var.has_database ? 1 : 0
  
  name        = "${var.project_name}-db-creds-${local.timestamp}"
  description = "Database credentials for ${var.project_name} ${var.environment}"
  
  tags = merge({
    Name        = "${var.project_name}-db-credentials"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  count = var.has_database ? 1 : 0
  
  secret_id = aws_secretsmanager_secret.db_credentials[0].id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password[0].result
    engine   = var.db_type
    host     = aws_db_instance.postgres[0].address
    port     = aws_db_instance.postgres[0].port
    dbname   = var.db_name
  })
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge({
    Name        = "${var.project_name}-vpc"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge({
    Name        = "${var.project_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  tags = merge({
    Name        = "${var.project_name}-private-subnet-${count.index + 1}"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Database Subnets
resource "aws_subnet" "database" {
  count = var.has_database ? length(var.database_subnet_cidrs) : 0
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  tags = merge({
    Name        = "${var.project_name}-database-subnet-${count.index + 1}"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge({
    Name        = "${var.project_name}-igw"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = merge({
    Name        = "${var.project_name}-nat-eip"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  
  tags = merge({
    Name        = "${var.project_name}-nat"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge({
    Name        = "${var.project_name}-public-route-table"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  
  tags = merge({
    Name        = "${var.project_name}-private-route-table"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for application load balancer"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge({
    Name        = "${var.project_name}-alb-sg"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge({
    Name        = "${var.project_name}-ecs-sg"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

resource "aws_security_group" "database" {
  count = var.has_database ? 1 : 0
  
  name        = "${var.project_name}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = var.db_type == "postgres" ? 5432 : var.db_type == "mysql" ? 3306 : 27017
    to_port         = var.db_type == "postgres" ? 5432 : var.db_type == "mysql" ? 3306 : 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge({
    Name        = "${var.project_name}-db-sg"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# RDS Database Subnet Group
resource "aws_db_subnet_group" "database" {
  count = var.has_database ? 1 : 0
  
  name       = "${var.project_name}-subnet-${local.timestamp}"
  subnet_ids = aws_subnet.database[*].id
  
  tags = merge({
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  count = var.has_database && var.db_type == "postgres" ? 1 : 0
  
  identifier             = "${var.project_name}-db-${local.timestamp}"
  engine                 = "postgres"
  engine_version         = var.postgres_version
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_max_allocated_storage
  storage_type           = "gp2"
  storage_encrypted      = true
  
  db_name                = replace(var.db_name, "-", "_")
  username               = var.db_username
  password               = random_password.db_password[0].result
  
  vpc_security_group_ids = [aws_security_group.database[0].id]
  db_subnet_group_name   = aws_db_subnet_group.database[0].name
  
  backup_retention_period = 7
  deletion_protection     = var.environment == "prod" ? true : false
  skip_final_snapshot     = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-final-snapshot" : null
  
  tags = merge({
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Application Load Balancer
resource "aws_lb" "app" {
  name               = "${var.project_name}-alb-${local.timestamp}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  tags = merge({
    Name        = "${var.project_name}-alb"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# ALB Target Group
resource "aws_lb_target_group" "app" {
  name        = "${var.project_name}-tg-${local.timestamp}"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = var.health_check_path
    matcher             = "200-399"
  }
  
  tags = merge({
    Name        = "${var.project_name}-target-group"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# HTTPS Listener (optional, if SSL certificate is provided)
resource "aws_lb_listener" "https" {
  count             = var.certificate_arn != null ? 1 : 0
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = merge({
    Name        = "${var.project_name}-ecs-cluster"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-exec-${local.timestamp}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge({
    Name        = "${var.project_name}-task-execution-role"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Attach policies to the task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "secrets_manager_access" {
  count = var.has_database ? 1 : 0
  
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.secrets_manager_access[0].arn
}

# Policy for Secrets Manager access
resource "aws_iam_policy" "secrets_manager_access" {
  count = var.has_database ? 1 : 0
  
  name        = "${var.project_name}-${var.environment}-secrets-manager-access"
  description = "Allow access to Secrets Manager for retrieving database credentials"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.db_credentials[0].arn
      }
    ]
  })
  
  tags = merge({
    Name        = "${var.project_name}-secrets-manager-policy"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Initialize variables for environment and secrets
locals {
  base_environment = var.container_environment
  
  # Database environment variables to add if database is enabled
  db_environment = var.has_database ? [
    {
      name  = "DB_HOST"
      value = var.db_type == "postgres" ? aws_db_instance.postgres[0].address : ""
    },
    {
      name  = "DB_PORT"
      value = var.db_type == "postgres" ? "5432" : var.db_type == "mysql" ? "3306" : "27017"
    },
    {
      name  = "DB_NAME"
      value = var.db_name
    },
    {
      name  = "DB_USER"
      value = var.db_username
    },
    {
      name  = "DB_PASSWORD"
      value = random_password.db_password[0].result
    },
    {
      name  = "POSTGRES_USER"
      value = var.db_username
    },
    {
      name  = "POSTGRES_PASSWORD"
      value = random_password.db_password[0].result
    },
    {
      name  = "DATABASE_URL"
      value = "postgres://${var.db_username}:${random_password.db_password[0].result}@${aws_db_instance.postgres[0].address}:5432/${var.db_name}"
    }
  ] : []
  
  # Secret values
  db_secrets = var.has_database ? [
    {
      name      = "DB_CONNECTION_STRING"
      valueFrom = aws_secretsmanager_secret.db_credentials[0].arn
    }
  ] : []
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  
  container_definitions = jsonencode([
    {
      name      = var.project_name
      image     = var.container_image
      essential = true
      
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      
      # Combine base environment with database environment if enabled
      environment = concat(local.base_environment, local.db_environment)
      
      # Add secrets if database is enabled
      secrets = local.db_secrets
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = var.project_name
        }
      }
    }
  ])
  
  tags = merge({
    Name        = "${var.project_name}-task-definition"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}-${local.timestamp}"
  retention_in_days = 30
  
  tags = merge({
    Name        = "${var.project_name}-logs"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-${var.environment}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  launch_type     = "FARGATE"
  desired_count   = var.desired_count
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.project_name
    container_port   = var.container_port
  }
  
  # Ensure the ALB's target group is attached only when a service is created
  depends_on = [aws_lb_listener.http]
  
  tags = merge({
    Name        = "${var.project_name}-ecs-service"
    Environment = var.environment
    Managed     = "AgentX"
    Project     = var.project_id != null ? var.project_id : "unknown"
  }, var.tags)
}

# Auto Scaling for ECS
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "${var.project_name}-${var.environment}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

resource "aws_appautoscaling_policy" "ecs_memory" {
  name               = "${var.project_name}-${var.environment}-memory-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    
    target_value = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
} 