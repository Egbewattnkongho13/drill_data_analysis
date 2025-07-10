
resource "aws_iam_role" "lambda_role" {
  name = var.name

  assume_role_policy = data.aws_iam_policy_document.lambda_role_policy.json
}


resource "aws_iam_role_policy" "ecr_pull_policy" {
  name   = "${var.name}-ecr-pull-policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.ecr_pull_policy.json

}
