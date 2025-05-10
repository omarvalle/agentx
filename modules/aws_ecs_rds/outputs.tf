output "vpc_id" {
  description = "ID of the VPC created"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.app.dns_name
}

output "alb_url" {
  description = "URL for accessing the application via the load balancer"
  value       = "http://${aws_lb.app.dns_name}"
}

output "db_instance_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = var.has_database ? aws_db_instance.postgres[0].endpoint : "No database configured"
}

output "db_instance_address" {
  description = "Address of the RDS instance"
  value       = var.has_database ? aws_db_instance.postgres[0].address : "No database configured"
}

output "db_name" {
  description = "Name of the database"
  value       = var.has_database ? aws_db_instance.postgres[0].db_name : "No database configured"
}

output "db_username" {
  description = "Username for the database"
  value       = var.has_database ? aws_db_instance.postgres[0].username : "No database configured"
}

output "db_secret_name" {
  description = "Name of the secret in AWS Secrets Manager containing database credentials"
  value       = var.has_database ? aws_secretsmanager_secret.db_credentials[0].name : "No database configured"
}

output "db_secret_arn" {
  description = "ARN of the secret in AWS Secrets Manager containing database credentials"
  value       = var.has_database ? aws_secretsmanager_secret.db_credentials[0].arn : "No database configured"
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.app.arn
}

output "task_execution_role_arn" {
  description = "ARN of the task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "deployment_instructions" {
  description = "Instructions for managing and updating the deployment"
  value = var.has_database ? (
<<-EOT
Application is successfully deployed to AWS!

Application URL: http://${aws_lb.app.dns_name}

RDS PostgreSQL Database:
- Endpoint: ${aws_db_instance.postgres[0].endpoint}
- Database Name: ${aws_db_instance.postgres[0].db_name}
- Username: ${aws_db_instance.postgres[0].username}
- Password: <stored in AWS Secrets Manager>

To get database credentials:
aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_credentials[0].name} --query 'SecretString' --output text

ECS Service Information:
- Cluster: ${aws_ecs_cluster.main.name}
- Service: ${aws_ecs_service.app.name}

To update the application:
1. Build and push a new Docker image to the repository
2. Update the ECS service with the new image:
   aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --force-new-deployment

To view logs:
aws logs get-log-events --log-group-name ${aws_cloudwatch_log_group.ecs.name} --log-stream-name <log-stream-name>

To scale the service:
aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --desired-count <count>
EOT
  ) : (
<<-EOT
Application is successfully deployed to AWS!

Application URL: http://${aws_lb.app.dns_name}

ECS Service Information:
- Cluster: ${aws_ecs_cluster.main.name}
- Service: ${aws_ecs_service.app.name}

To update the application:
1. Build and push a new Docker image to the repository
2. Update the ECS service with the new image:
   aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --force-new-deployment

To view logs:
aws logs get-log-events --log-group-name ${aws_cloudwatch_log_group.ecs.name} --log-stream-name <log-stream-name>

To scale the service:
aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --desired-count <count>
EOT
  )
} 