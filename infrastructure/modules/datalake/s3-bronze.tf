resource "aws_s3_bucket" "bronze_bucket" {
    bucket = "${var.datalake_name}_bronze"

    tags = {
        Layer        = "bronze"
        Project      = var.datalake_name
    }
}


resource "aws_s3_bucket_public_access_block" "bronze_bucket_public_access_block" {
  bucket = aws_s3_bucket.bronze_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}