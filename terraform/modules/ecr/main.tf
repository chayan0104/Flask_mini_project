variable "repositories" {
  type    = list(string)
  default = ["mini-platform/frontend", "mini-platform/orders", "mini-platform/users"]
}

variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_ecr_repository" "this" {
  for_each             = toset(var.repositories)
  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

output "repository_urls" {
  value = { for name, repository in aws_ecr_repository.this : name => repository.repository_url }
}
