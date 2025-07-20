module "log_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.2.0"

  bucket                                = "${module.naming.prefix}-logs"
  attach_elb_log_delivery_policy        = true
  attach_lb_log_delivery_policy         = true
  attach_access_log_delivery_policy     = true
  attach_deny_insecure_transport_policy = true
  attach_require_latest_tls_policy      = true
}