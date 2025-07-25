resource "aws_ecr_repository" "ecr_repo" {
  name                 = var.repository_name
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }



  tags = {
    Name = "ECRModuleRepo"
  }

}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
