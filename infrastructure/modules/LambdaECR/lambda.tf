resource "aws_lambda_function" "lambbda_from_ecr" {
  function_name = var.lambda_name
  role          = var.lambda_role_arn
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}:${var.docker_image_tag}"
  timeout       = var.timeout

  tags = {
    Name = "LambdaFunctionFromECR"
  }
  depends_on = [aws_iam_role_policy_attachment.ecr_pull_policy]
}


