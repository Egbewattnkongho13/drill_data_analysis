output "name_of_lambda_function" {
  value       = aws_lambda_function.lambbda_from_ecr.function_name
  description = "Name of the Lambda function created from the ECR image"

}

output "arn_of_lambda_function" {
  value       = aws_lambda_function.lambbda_from_ecr.arn
  description = "ARN of the Lambda function created from the ECR image"
}

output "invoke_arn_of_lambda_function" {
  value       = aws_lambda_function.lambbda_from_ecr.invoke_arn
  description = "Invoke ARN of the Lambda function created from the ECR image"

}