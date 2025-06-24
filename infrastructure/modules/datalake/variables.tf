variable "project_name" {
    description = "The name of the project"
    type        = string
    default     = "data_lake"
  
}


variable "ingestions_lambda_name" {
    description = "Name of the Lambda function for ingestions"
    type        = string
    default     = "ingestions_lambda"
  
}

variable "silver_transform_lambda_name" {
    description = "Name of the Lambda function for silver transformations"
    type        = string
    default     = "silver_transform_lambda"

    validation {
        condition     = length(var.silver_transform_lambda_name) > 0
        error_message = "The silver_transform_lambda_name variable must not be empty."
    }

}

variable "IDE_gold_transform_lambda_name" {
    description = "Name of the Lambda function for gold transformations"
    type        = string
    default     = "gold_transform_lambda"
  
}

variable "account_id" {
    description = "AWS Account ID"
    type        = string
    default     = "123456789012"

    # ensure the string contains only digits
}

variable "region" {
    description = "AWS Region"
    type        = string
    default     = "us-west-2"

    # ensure it is one of the valid AWS regions - [us-east-1, us-west-1, us-west-2 ]
      
}