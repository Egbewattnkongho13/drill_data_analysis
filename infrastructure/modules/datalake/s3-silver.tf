resource "random_id" "s3_silver_bucket_id" {
  byte_length = 4
}

resource "aws_s3_bucket" "silver_bucket" {
    bucket = "${var.project_name}_silver_${random_id.s3_silver_bucket_id.hex}"

    tags = merge(var.global_tags,{
        Layer        = "silver"
        Project      = var.project_name
    }
  )
}

resource "aws_s3_bucket_public_access_block" "silver_bucket_public_access_block" {
  bucket = aws_s3_bucket.silver_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}