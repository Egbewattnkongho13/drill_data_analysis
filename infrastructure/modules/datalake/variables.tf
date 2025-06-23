variable "project_name" {
    description = "The name of the project"
    type        = string
    default     = "data_lake"
  
}

variable "global_tags" {
  description = "Tags applied to all AWS resources"
  type        = map(string)
    default     = {
        Environment = "dev"
        Owner       = "OyeData"
    }
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
}

variable "region" {
    description = "AWS Region"
    type        = string
    default     = "us-west-2"
  
}