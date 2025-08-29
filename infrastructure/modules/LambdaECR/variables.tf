variable "name" {
  description = "The name of the IAM role for the Lambda function"
  type        = string
  default     = "lambda_role"

  validation {
    condition     = length(var.name) > 0
    error_message = "The name variable must not be empty."
  }

}

variable "lambda_name" {
  description = "The name of the Lambda function"
  type        = string
  default     = "lambda_from_ecr"

  validation {
    condition     = length(var.lambda_name) > 0
    error_message = "The lambda_name variable must not be empty."
  }

}

variable "docker_image_tag" {
  description = "The tag of the Docker image to be used for the Lambda function"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", var.docker_image_tag))
    error_message = "The docker_image_tag must be a valid Docker tag."
  }
}

variable "ecr_repository_url" {
  description = "The URL of the ECR repository"
  type        = string

  validation {
    condition     = can(regex("^[0-9]+.dkr.ecr.[a-z0-9-]+.amazonaws.com/[a-z0-9_.-]+$", var.ecr_repository_url))
    error_message = "The ecr_repository_url must be a valid ECR repository URL."
  }
}

variable "ecr_repository_arn" {
  description = "The ARN of the ECR repository"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:ecr:[a-z0-9-]+:[0-9]{12}:repository/[a-z0-9_.-]+$", var.ecr_repository_arn))
    error_message = "The ecr_repository_arn must be a valid ECR repository ARN."
  }
}

variable "ssm_parameter_arns" {
  description = "A list of SSM parameter ARNs that the Lambda function needs access to."
  type        = list(string)
  default     = []
}
