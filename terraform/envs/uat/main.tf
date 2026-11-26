terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "mini-platform"
}

variable "environment" {
  type = string
}

locals {
  ecr_repositories = [
    for service in ["frontend", "orders", "users"] :
    "${var.project_name}/${service}"
  ]

  ecr_repository_urls = {
    for name, repository in data.aws_ecr_repository.shared :
    name => repository.repository_url
  }

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Read dev-owned repositories; a data source does not create or manage them.
data "aws_ecr_repository" "shared" {
  for_each = toset(local.ecr_repositories)
  name     = each.value
}

module "vpc" {
  source = "../../modules/vpc"
  name   = "${var.project_name}-${var.environment}"
  azs    = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "eks" {
  source = "../../modules/eks"
  name   = "${var.project_name}-${var.environment}"
  # UAT has its own VPC and cluster, separate from dev.
  subnet_ids = module.vpc.public_subnet_ids
  tags       = local.common_tags
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repository_urls" {
  value = local.ecr_repository_urls
}
