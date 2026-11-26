terraform {
  # Keep the Terraform CLI and AWS provider within the tested version ranges.
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
  # One ECR repository per application service; dev owns these shared repos.
  ecr_repositories = [
    for service in ["frontend", "orders", "users"] :
    "${var.project_name}/${service}"
  ]

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

module "vpc" {
  source = "../../modules/vpc"
  name   = "${var.project_name}-${var.environment}"
  azs    = ["${var.aws_region}a", "${var.aws_region}b"]
}

# ECR is shared by dev and UAT, so this is the only environment that creates it.
module "ecr" {
  source       = "../../modules/ecr"
  repositories = local.ecr_repositories
  tags         = merge(local.common_tags, { Environment = "shared" })
}

module "eks" {
  source = "../../modules/eks"
  name   = "${var.project_name}-${var.environment}"
  # Passing subnet IDs from VPC makes the network dependency explicit.
  subnet_ids = module.vpc.public_subnet_ids
  tags       = local.common_tags
}

# Outputs are values operators need after apply, not extra AWS resources.
output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}
