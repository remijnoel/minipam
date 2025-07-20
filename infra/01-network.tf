module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${module.naming.prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = var.azs
  public_subnets  = var.public_subnets

  enable_nat_gateway = false
  enable_vpn_gateway = false

  tags = module.naming.tags
}