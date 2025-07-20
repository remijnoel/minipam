module "naming" {
  source       = "./naming"
  project_name = "minipam"
  environment  = terraform.workspace == "default" ? "dev" : terraform.workspace
  repository   = "github.com/remijnoel/minipam/infra"
}