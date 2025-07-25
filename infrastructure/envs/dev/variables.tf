variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "drill_data_analysis"

  validation {
    condition     = length(var.project_name) > 0 && can(regex("^[a-zA-Z0-9_-]+$", var.project_name))
    error_message = "The project_name variable must not be empty and can only contain alphanumeric characters, underscores, and hyphens."
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

variable "ingestion_docker_image_tag" {
  type        = string
  description = "Docker image tag for the ingestion lambda"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+$", var.ingestion_docker_image_tag))
    error_message = "The ingestion_docker_image_tag must consist of alphanumeric characters, dots, underscores, or hyphens."
  }
}

variable "silver_docker_image_tag" {
  type        = string
  description = "Docker image tag for the silver transform lambda"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+$", var.silver_docker_image_tag))
    error_message = "The silver_docker_image_tag must consist of alphanumeric characters, dots, underscores, or hyphens."
  }
}

variable "gold_docker_image_tag" {
  type        = string
  description = "Docker image tag for the gold transform lambda"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+$", var.gold_docker_image_tag))
    error_message = "The gold_docker_image_tag must consist of alphanumeric characters, dots, underscores, or hyphens."
  }
}
