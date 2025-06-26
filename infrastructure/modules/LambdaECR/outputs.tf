output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_ecr.repository_url
  description = "ECR repository URL where one pushes the Docker image for the Lambda function"
  
}

output "name_of_lambda_function" {
  value = aws_lambda_function.lambbda_from_ecr.function_name
  description = "Name of the Lambda function created from the ECR image"
  
}