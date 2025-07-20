variable "project_name" {
    description = "The name of the project."
    type        = string
}

variable "environment" {
    description = "The environment for which resources are being created."
    type        = string
}

variable "repository" {
    description = "The repository URL for this terraform template."
    type        = string
}

locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    Repository = var.repository
  }
  naming_prefix = "${var.project_name}-${var.environment}"
}

output "prefix" {
  value = local.naming_prefix
}

output "tags" {
  value = local.tags
}

output "env" {
  value = var.environment
}


data "aws_caller_identity" "current" {}

output "current_account_id" {
  value = data.aws_caller_identity.current.account_id
}

resource "aws_resourcegroups_group" "base" {
  name = local.naming_prefix
    description = "Resource group for ${var.project_name} in ${var.environment} environment"
    resource_query {
        query = jsonencode({
            ResourceTypeFilters = ["AWS::AllSupported"],
            TagFilters          = [
                {
                    Key    = "Project",
                    Values = [var.project_name] 
                },
                {
                    Key    = "Environment",
                    Values = [var.environment]
                }
            ]
        })
    }
}



