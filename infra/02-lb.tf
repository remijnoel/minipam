# resource "aws_lb" "alb" {
#   name                       = "${module.naming.prefix}-alb"
#   internal                   = false
#   load_balancer_type         = "application"
#   enable_deletion_protection = false

#   subnets = module.vpc.public_subnets

#   security_groups = [
#     aws_security_group.alb_public.id,
#   ]

#   access_logs {
#     bucket  = module.log_bucket.s3_bucket_id
#     prefix  = module.naming.prefix
#     enabled = true
#   }

#   tags = merge(module.naming.tags, {
#     Name    = "${module.naming.prefix}-alb"
#     Service = "alb"
#   })
# }

# resource "aws_lb_listener" "alb_http" {
#   load_balancer_arn = aws_lb.alb.arn
#   port              = "80"
#   protocol          = "HTTP"

#   # Redirect HTTP to HTTPS
#   default_action {
#     type = "redirect"
#     redirect {
#       port        = "443"
#       protocol    = "HTTPS"
#       status_code = "HTTP_301"
#     }
#   }
# }

# resource "aws_lb_listener" "alb_https" {
#   load_balancer_arn = aws_lb.alb.arn
#   port              = "443"
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
#   certificate_arn   = module.acm.acm_certificate_arn

#   default_action {
#     type = "fixed-response"
#     fixed_response {
#       content_type = "text/plain"
#       message_body = "Denied"
#       status_code  = 403
#     }
#   }

#   tags = merge(module.naming.tags, {
#     Name    = "${module.naming.prefix}-alb-https"
#     Service = "alb"
#   })

#   lifecycle {
#     create_before_destroy = true
#   }
# }

# resource "aws_lb_target_group" "nginx" {
#   name                 = "${module.naming.prefix}-nginx"
#   port                 = 80
#   protocol             = "HTTP"
#   vpc_id               = module.vpc.vpc_id
#   target_type          = "ip"
#   deregistration_delay = 15

#   health_check {
#     interval            = 30
#     path                = "/"
#     port                = "traffic-port"
#     protocol            = "HTTP"
#     timeout             = 5
#     healthy_threshold   = 3
#     unhealthy_threshold = 5
#     matcher             = "200-299"
#   }

#   tags = merge(module.naming.tags, {
#     Name    = "${module.naming.prefix}-nginx-tg"
#     Service = "elb"
#   })

#   lifecycle {
#     create_before_destroy = true
#   }
# }

# resource "aws_lb_listener_rule" "this" {
#   listener_arn = aws_lb_listener.alb_https.arn
#   priority     = 1

#   action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.nginx.arn
#   }

#   condition {
#     host_header {
#       values = ["www.${var.domain_name}"]
#     }
#   }
# }

# resource "aws_security_group" "alb_public" {
#   name        = "${module.naming.prefix}-alb-public"
#   description = "Security group protecting the ALB"
#   vpc_id      = module.vpc.vpc_id
# }

# resource "aws_security_group_rule" "all_all_https" {
#   security_group_id = aws_security_group.alb_public.id
#   from_port         = 443
#   to_port           = 443
#   protocol          = "tcp"
#   type              = "ingress"
#   cidr_blocks       = ["0.0.0.0/0"]
# }

# resource "aws_security_group_rule" "all_all_http" {
#   security_group_id = aws_security_group.alb_public.id
#   from_port         = 80
#   to_port           = 80
#   protocol          = "tcp"
#   type              = "ingress"
#   cidr_blocks       = ["0.0.0.0/0"]
# }

# resource "aws_security_group_rule" "egress_allow_all_http" {
#   cidr_blocks       = ["0.0.0.0/0"]
#   description       = "Allow egress all HTTPS"
#   from_port         = 80
#   to_port           = 80
#   protocol          = "TCP"
#   security_group_id = aws_security_group.alb_public.id
#   type              = "egress"
# }