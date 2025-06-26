resource "aws_lambda_function" "lambbda_from_ecr" {
  function_name = var.name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_ecr.repository_url}:${var.docker_image_tag}"

  tags = {
    Name        = "LambdaFunctionFromECR"
    Environment = "dev"
  }
  depends_on = [aws_ecr_repository.lambda_ecr]
}


resource "aws_iam_role" "lambda_role" {
  name = "${var.name}_role"

  assume_role_policy = data.aws_iam_policy_document.lambda_role_policy.json
}

data "aws_iam_policy_document" "lambda_role_policy" {
    statement {
      effect =  "Allow"
      principals {
        type = "Service"
        identifiers = ["lambda.amazonaws.com"]
      }
      actions = [ 
        "sts:AssumeRole"
      ]
    }
}


