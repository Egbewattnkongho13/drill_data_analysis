variable "project_name" {
    description = "The name of the project"
    type        = string
    default     = "data_lake"
  
  validation {
    condition     = length(var.project_name) > 0 && can(regex("^[a-zA-Z0-9_-]+$", var.project_name))
    error_message = "The project_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
  }
}


variable "ingestions_lambda_name" {
    description = "Name of the Lambda function for ingestions"
    type        = string
    default     = "ingestions_lambda"
  
  validation {
    condition     = length(var.ingestions_lambda_name) > 0 && can(regex("^[a-zA-Z0-9_-]+$", var.ingestions_lambda_name))
    error_message = "The ingestions_lambda_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
  }
}

variable "silver_transform_lambda_name" {
    description = "Name of the Lambda function for silver transformations"
    type        = string
    default     = "silver_transform_lambda"

    validation {
        condition     = length(var.silver_transform_lambda_name) > 0 && can(regex("^[a-zA-Z0-9_-]+$",var.silver_transform_lambda_name))
        error_message = "The silver_transform_lambda_name variable must not be empty  and can only contain alphanumeric characters, underscores, and hyphens."
    }

}

variable "IDE_gold_transform_lambda_name" {
    description = "Name of the Lambda function for gold transformations"
    type        = string
    default     = "gold_transform_lambda"

    validation {
        condition     = length(var.IDE_gold_transform_lambda_name) > 0 && can(regex("^[a-zA-Z0-9_-]+$", var.IDE_gold_transform_lambda_name))
        error_message = "The IDE_gold_transform_lambda_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
    }
  
}

variable "account_id" {
    description = "AWS Account ID"
    type        = string
    default     = "123456789012"

    # ensure the string contains only digits
    validation {
        condition     = can(regex("^[0-9]{12}$", var.account_id))
        error_message = "The account_id must be a 12-digit number."
    }
}

variable "region" {
    description = "AWS Region"
    type        = string
    default     = "us-east-1"

    # ensure it is one of the valid AWS regions - [us-east-1, us-west-1, us-west-2 ]
    validation {
        condition   = contains(["us-east-1", "us-west-1", "us-west-2"], var.region)
        error_message = "value must be one of the valid AWS regions liste above."
    }
}