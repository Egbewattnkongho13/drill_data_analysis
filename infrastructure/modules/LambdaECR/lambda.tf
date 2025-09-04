resource "aws_lambda_function" "lambda_function" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}:${var.docker_image_tag}"
  timeout       = var.timeout

  environment {
    variables = var.environment_variables
  }

  tags = {
    Name = "LambdaFunctionFromECR"
  }
  depends_on = [aws_iam_role_policy_attachment.ecr_pull_policy]
}


