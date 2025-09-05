output "bronze_bucket_name" {
  value = aws_s3_bucket.bronze_bucket.bucket

}

output "silver_bucket_name" {
  value = aws_s3_bucket.silver_bucket.bucket
}

output "gold_bucket_name" {
  value = aws_s3_bucket.gold_bucket.bucket

}

output "ingestion_lambda_execution_role_arn" {
  description = "ARN of the IAM role for the ingestion Lambda function"
  value       = aws_iam_role.ingestion_lambda_execution_role.arn
}

