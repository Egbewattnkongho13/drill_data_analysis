data "aws_iam_policy_document" "lambda_role_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}


data "aws_iam_policy_document" "ecr_pull_policy" {
   statement {
     effect = "Allow"
     actions = [
        "ecr:GetAuthorizationToken"
     ]
    resources = ["*"]
   }

   statement {
     effect = "Allow"
     actions = [
       "ecr:BatchCheckLayerAvailability",
       "ecr:GetDownloadUrlForLayer",
       "ecr:BatchGetImage"
     ]
     resources = [var.ecr_repository_arn]
  }
}
