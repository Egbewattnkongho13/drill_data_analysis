output "bronze_bucket_name" {
  value = aws_s3_bucket.bronze_bucket.bucket

}

output "silver_bucket_name" {
  value = aws_s3_bucket.silver_bucket.bucket
}

output "gold_bucket_name" {
  value = aws_s3_bucket.gold_bucket.bucket

}

output "bronze_ingestion_role_arn" {
  value = aws_iam_role.bronze_ingestion_role.arn
}

