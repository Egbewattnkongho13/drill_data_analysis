variable "datalake_name" {
  description = "The name of the project"
  type        = string
  default     = "data-lake"

  validation {
    condition     = length(var.datalake_name) > 0 && can(regex("^[a-zA-Z0-9-]+$", var.datalake_name))
    error_message = "The datalake_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
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