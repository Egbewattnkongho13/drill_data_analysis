output "repository_url" {
  value       = aws_ecr_repository.ecr_repo.repository_url
  description = "The URL of the ECR repository"
}

output "arn_of_ecr_repository" {
  value       = aws_ecr_repository.ecr_repo.arn
  description = "The ARN of the ECR repository"
}