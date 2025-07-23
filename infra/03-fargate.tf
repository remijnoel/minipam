resource "aws_ecs_cluster" "cs_cluster" {
  name = "${module.naming.prefix}-cluster"

  tags = merge(module.naming.tags, {
    Name    = "${module.naming.prefix}-ecs-cluster"
    Service = "ecs"
  })
}

resource "aws_ecs_cluster_capacity_providers" "cs_cluster_capacity_providers" {
  cluster_name = aws_ecs_cluster.cs_cluster.name

  capacity_providers = ["FARGATE_SPOT", "FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
  }
}

locals {
  container_name = module.naming.prefix
  default_container_definition = jsonencode(
    [
      {
        dnsSearchDomains = null,
        entryPoint       = null,
        portMappings = [
          {
            hostPort      = 8000
            protocol      = "tcp"
            containerPort = 8000
          }
        ]
        command = null,
        linuxParameters = {
          capabilities = {
            drop = ["NET_RAW"]
            add  = []
          },
          "initProcessEnabled" : true
        },
        environment    = [],
        systemControls = [],
        secrets        = [],
        logConfiguration = {
          logDriver = "awslogs",
          options = {
            awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name,
            awslogs-region        = var.aws_region,
            awslogs-stream-prefix = "ecs"
          }
        },
        ulimits                = null,
        dnsServers             = null,
        mountPoints            = [],
        dockerSecurityOptions  = null,
        memoryReservation      = null,
        volumesFrom            = [],
        image                  = "${aws_ecr_repository.ecr.repository_url}:latest",
        disableNetworking      = null,
        healthCheck            = null
        essential              = true,
        links                  = null,
        hostname               = null,
        extraHosts             = null,
        user                   = "root",
        readonlyRootFilesystem = null,
        dockerLabels           = null,
        privileged             = false,
        name                   = local.container_name,
        memory                 = 2048,
        cpu                    = 1024
      }
    ]
  )
}

resource "aws_ecs_task_definition" "task" {
  family             = "${module.naming.prefix}-task-def"
  execution_role_arn = aws_iam_role.task_execution.arn
  task_role_arn      = aws_iam_role.task.arn
  network_mode       = "awsvpc"

  tags = merge(module.naming.tags, {
    Name    = "${module.naming.prefix}-task-def"
    Service = "ecs"
  })

  requires_compatibilities = ["FARGATE"]

  # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#task_size
  cpu    = 1024
  memory = 2048

  container_definitions = local.default_container_definition
}

# Task execution

data "aws_iam_policy_document" "task_execution_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${module.naming.prefix}-ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.task_execution_role.json
}

data "aws_iam_policy_document" "task_execution_iam_policy" {
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "ssm:GetParameters",
    ]

    resources = ["*"]
  }
  statement {
    actions = [
      "iam:CreateServiceLinkedRole",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "task_execution" {
  name        = "${module.naming.prefix}-ecsExec"
  description = "Task execution policy"
  policy      = data.aws_iam_policy_document.task_execution_iam_policy.json
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = aws_iam_policy.task_execution.arn
}

## Task role

resource "aws_iam_role" "task" {
  name               = "${module.naming.prefix}-ecsTaskRole"
  assume_role_policy = data.aws_iam_policy_document.task_execution_role.json
}

# Additional permissions for the task role

resource "aws_ecs_service" "main" {
  name                   = "${module.naming.prefix}-service"
  cluster                = aws_ecs_cluster.cs_cluster.id
  task_definition        = aws_ecs_task_definition.task.arn
  launch_type            = "FARGATE"
  desired_count          = 1
  platform_version       = "LATEST"
  enable_execute_command = false

  health_check_grace_period_seconds = 120
  #   deployment_minimum_healthy_percent = 0

  load_balancer {
    target_group_arn = aws_lb_target_group.nginx.arn
    container_name   = local.container_name
    container_port   = 8000
  }

  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.service.id]
  }
  tags = merge(module.naming.tags, {
    Name    = "${module.naming.prefix}-nginx-service"
    Service = "ecs"
  })

  lifecycle {
    ignore_changes = [
      task_definition,
    ]
  }
}

resource "aws_security_group" "service" {
  name        = "${module.naming.prefix}-service"
  description = "Security group for the minipam service"
  vpc_id      = module.vpc.vpc_id
  tags = merge(module.naming.tags, {
    Name    = "${module.naming.prefix}-service"
    Service = "ecs"
  })
}

resource "aws_security_group_rule" "service_ingress_alb" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_public.id
  security_group_id        = aws_security_group.service.id
  description              = "Allow traffic from ALB to ECS service"
}

# HTTP/S
resource "aws_security_group_rule" "egress_allow_all_https_from_app" {
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow egress all HTTPS"
  from_port         = 443
  to_port           = 443
  protocol          = "TCP"
  security_group_id = aws_security_group.service.id
  type              = "egress"
}

resource "aws_security_group_rule" "egress_allow_all_http_from_app" {
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow egress all HTTP"
  from_port         = 80
  to_port           = 80
  protocol          = "TCP"
  security_group_id = aws_security_group.service.id
  type              = "egress"
}