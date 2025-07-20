module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 4.0"

  domain_name = "www.${var.domain_name}"
  zone_id     = aws_route53_zone.novi_labs.zone_id

  validation_method = "DNS"

  wait_for_validation = true

  tags = merge(
    module.naming.tags,
    {
      Name = var.domain_name
    }
  )
  validation_record_fqdns = module.route53_records.validation_route53_record_fqdns
}

module "route53_records" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 4.0"

  create_certificate          = false
  create_route53_records_only = true

  validation_method = "DNS"

  distinct_domain_names = module.acm.distinct_domain_names
  zone_id               = aws_route53_zone.novi_labs.zone_id

  acm_certificate_domain_validation_options = module.acm.acm_certificate_domain_validation_options
}