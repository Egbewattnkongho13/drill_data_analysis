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
