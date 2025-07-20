output "zone_ns_servers" {
  value       = aws_route53_zone.novi_labs.name_servers
  description = "The name servers for the Route 53 zone."
}