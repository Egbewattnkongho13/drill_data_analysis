resource "aws_iam_policy" "ecr_pull_policy" {
  name        = "${var.lambda_name}-ecr-pull-policy"
  description = "A policy to allow pulling images from ECR"
  policy      = data.aws_iam_policy_document.ecr_pull_policy.json
}
