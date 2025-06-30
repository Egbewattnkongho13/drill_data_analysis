output "repository_url" {
  value = aws_ecr_repository.ecr_repo.repository_url

}

output "arn_of_ecr_repository" {
  value = aws_ecr_repository.ecr_repo.arn
}