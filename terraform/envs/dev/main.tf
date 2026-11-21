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

locals {
  common_tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

module "vpc" {
  source = "../../modules/vpc"
  name   = "${var.project_name}-dev"
  azs    = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "ecr" {
  source = "../../modules/ecr"
  tags   = local.common_tags
}

module "eks" {
  source     = "../../modules/eks"
  name       = "${var.project_name}-dev"
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
  value = module.ecr.repository_urls
}
