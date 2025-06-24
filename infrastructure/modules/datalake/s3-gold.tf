resource "aws_s3_bucket" "gold_bucket" {
    bucket = "${var.datalake_name}_gold"

    tags = {
      Layer       = "gold"
      Project     = var.datalake_name
    }
}

resource "aws_s3_bucket_public_access_block" "gold_bucket_public_access_block" {
 bucket = aws_s3_bucket.gold_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  
}

