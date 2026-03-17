resource "aws_s3_bucket" "bronze_bucket" {
  bucket = "${var.datalake_name}-bronze"

  tags = {
    Layer   = "bronze"
    Project = var.datalake_name
  }
}


resource "aws_s3_bucket_public_access_block" "bronze_bucket_public_access_block" {
  bucket = aws_s3_bucket.bronze_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "bronze_bucket_policy" {
  bucket = aws_s3_bucket.bronze_bucket.id

  policy = data.aws_iam_policy_document.bronze_bucket_policy_document.json
}

data "aws_iam_policy_document" "bronze_bucket_policy_document" {
  statement {
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.ingestion_lambda_execution_role.arn]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.bronze_bucket.arn}/drill-data/*"]
  }
}
