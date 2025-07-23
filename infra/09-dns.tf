# resource "aws_route53_zone" "dns" {
#   name = var.domain_name

#   tags = merge(
#     module.naming.tags,
#     {
#       Name = var.domain_name
#     }
#   )
# }

resource "aws_route53_record" "service" {
  allow_overwrite = true
  name            = var.domain_name
  records         = [aws_lb.alb.dns_name]
  ttl             = 30
  type            = "CNAME"
  zone_id         = var.route53_zone_id
}