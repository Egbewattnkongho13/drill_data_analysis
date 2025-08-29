
resource "aws_iam_role" "lambda_role" {
  name = var.name

  assume_role_policy = data.aws_iam_policy_document.lambda_role_policy.json
}

resource "aws_iam_role_policy" "ssm_read_policy" {
  count = length(var.ssm_parameter_arns) > 0 ? 1 : 0

  name   = "ssm-read-policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.ssm_read_policy_document.json
}

resource "aws_iam_role_policy_attachment" "ecr_pull_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.ecr_pull_policy.arn
}

resource "aws_iam_role_policy_attachment" "aws_lambda_vpc_access_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "aws_lambda_basic_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

