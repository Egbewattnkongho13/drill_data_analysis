# Bronze Layer Policies
data "aws_iam_policy_document" "bronze_write_policy" {
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${var.datalake_name}-bronze"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = ["arn:aws:s3:::${var.datalake_name}-bronze/drill_data/*"]
  }
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}


# Silver Layer Policies

data "aws_iam_policy_document" "silver_write_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "arn:aws:s3:::${var.datalake_name}-silver",
      "arn:aws:s3:::${var.datalake_name}-silver/drill_data/*"
    ]
  }
}

data "aws_iam_policy_document" "bronze_read_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.datalake_name}-bronze",
      "arn:aws:s3:::${var.datalake_name}-bronze/drill_data/*"
    ]
  }
}




# Gold Layer Policies

data "aws_iam_policy_document" "gold_write_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "arn:aws:s3:::${var.datalake_name}-gold",
      "arn:aws:s3:::${var.datalake_name}-gold/drill_data/*"
    ]
  }
}

data "aws_iam_policy_document" "silver_read_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.datalake_name}-silver",
      "arn:aws:s3:::${var.datalake_name}-silver/drill_data/*"
    ]
  }
}

