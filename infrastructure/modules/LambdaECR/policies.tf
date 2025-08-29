data "aws_region" "current" {}

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

data "aws_iam_policy_document" "ssm_read_policy_document" {
  

  statement {

    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]

    resources = var.ssm_parameter_arns
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

