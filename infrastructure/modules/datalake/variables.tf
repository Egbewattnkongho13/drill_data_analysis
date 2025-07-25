variable "datalake_name" {
  description = "The name of the project"
  type        = string
  default     = "data-lake"

  validation {
    condition     = length(var.datalake_name) > 0 && can(regex("^[a-zA-Z0-9-]+$", var.datalake_name))
    error_message = "The datalake_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
  }
}


variable "ingestion_lambda_arn" {
  description = "ARN of the IAM role for the ingestion Lambda function"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/([a-zA-Z0-9-_]+)$", var.ingestion_lambda_arn))
    error_message = "The ingestion_lambda_arn must be a valid AWS IAM Role ARN."
  }
}

variable "silver_transform_lambda_arn" {
  description = "ARN of the IAM role for the silver transformation Lambda function"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/([a-zA-Z0-9-_]+)$", var.silver_transform_lambda_arn))
    error_message = "The silver_transform_lambda_arn must be a valid AWS IAM Role ARN."
  }
}

variable "gold_transform_lambda_arn" {
  description = "ARN of the IAM role for the gold transformation Lambda function"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/([a-zA-Z0-9-_]+)$", var.gold_transform_lambda_arn))
    error_message = "The gold_transform_lambda_arn must be a valid AWS IAM Role ARN."
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
    condition     = contains(["us-east-1", "us-west-1", "us-west-2"], var.region)
    error_message = "value must be one of the valid AWS regions liste above."
  }
}