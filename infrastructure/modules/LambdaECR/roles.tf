locals {
  role_name = split("/", var.lambda_role_arn)[1]
}

resource "aws_iam_role_policy" "ssm_read_policy" {
  count = length(var.ssm_parameter_arns) > 0 ? 1 : 0

  name   = "ssm-read-policy"
  role   = local.role_name
  policy = data.aws_iam_policy_document.ssm_read_policy_document.json
}

resource "aws_iam_role_policy_attachment" "ecr_pull_policy" {
  role       = local.role_name
  policy_arn = aws_iam_policy.ecr_pull_policy.arn
}

resource "aws_iam_role_policy_attachment" "aws_lambda_vpc_access_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = local.role_name
}

resource "aws_iam_role_policy_attachment" "aws_lambda_basic_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = local.role_name
}