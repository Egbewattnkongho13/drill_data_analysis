variable "name" {
  description = "The name of the IAM role for the Lambda function"
  type        = string
  default     = "lambda_role"

  validation {
    condition     = length(var.name) > 0
    error_message = "The name variable must not be empty."
  }
  
}

variable "docker_image_tag" {
  description = "The tag of the Docker image to be used for the Lambda function"
  type        = string
  default     = "latest"

 validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", var.docker_image_tag))
    error_message = "The docker_image_tag must be a valid Docker tag."
  } 
}