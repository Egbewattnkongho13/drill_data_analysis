resource "aws_s3_bucket" "glue_assets" {
  bucket = "${var.glue_job_name}-assets"
}

resource "aws_s3_bucket_public_access_block" "glue_assets_public_access" {
  bucket = aws_s3_bucket.glue_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
