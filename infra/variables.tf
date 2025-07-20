variable "domain_name" {
  description = "The domain name for which the ACM certificate will be created."
  type        = string
  default     = "minipam-dev.infra.rnoel.net"
}

variable "aws_region" {
  description = "The AWS region where the resources will be created."
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

# variable "private_subnets" {
#   description = "List of CIDR blocks for private subnets."
#   type        = list(string)
#   default     = ["10.0.0.0/24", "10.0.1.0/24"]
# }

variable "public_subnets" {
  description = "List of CIDR blocks for public subnets."
  type        = list(string)
  default     = ["10.0.0.0/24"]
}

variable "azs" {
  description = "List of availability zones to use for the VPC."
  type        = list(string)
  default     = ["us-west-2a"]
}