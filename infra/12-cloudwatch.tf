resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${module.naming.prefix}/logs"
  retention_in_days = 7

  tags = {
    Name        = "ECS Fargate Logs"
    Environment = module.naming.env
  }
}