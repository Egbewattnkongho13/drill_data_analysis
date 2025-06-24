resource "random_id" "s3_gold_bucket_id" {
  byte_length = 4
}

resource "aws_s3_bucket" "gold_bucket" {
    bucket = "${var.project_name}_gold_${random_id.s3_gold_bucket_id.hex}"

    tags = {
      Layer       = "gold"
      Project     = var.project_name
    }
}

resource "aws_s3_public_access_block" "gold_bucket_public_access_block" {
 bucket = aws_s3_bucket.gold_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  
}

