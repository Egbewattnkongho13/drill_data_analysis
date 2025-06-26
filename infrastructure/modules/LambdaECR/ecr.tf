resource "aws_ecr_repository" "lambda_ecr" {
  name                = "${var.name}_ecr"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "LambdaECRModuleRepo"
    Environment = "dev"
  }
  
}