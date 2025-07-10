resource "aws_lambda_function" "lambbda_from_ecr" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}:${var.docker_image_tag}"

  tags = {
    Name = "LambdaFunctionFromECR"
  }
  depends_on = [aws_iam_role_policy.ecr_pull_policy]
}


