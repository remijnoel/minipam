provider "aws" {
  region = var.aws_region
}


# Workspaces:
# - dev
terraform {
  backend "s3" {
    bucket         = "rno-sandbox-terraform-state"
    key            = "minipam-dev/terraform.tfstate"
    encrypt        = true
    region         = "us-west-2"
    dynamodb_table = "rno-prod-terraform-state-lock"
  }
}
