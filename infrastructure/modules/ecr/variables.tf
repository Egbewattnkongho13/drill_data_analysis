variable "repository_name" {
  description = "The name of the ECR repository"
  type        = string

  validation {
    condition     = length(var.name) > 0
    error_message = "The name variable must not be empty."
  }
  
}

variable "image_tag_mutability" {
  description = "The image tag mutability setting for the ECR repository"
  type        = string
  default     = "MUTABLE"

  validation {
    condition     = var.image_tag_mutability == "MUTABLE" || var.image_tag_mutability == "IMMUTABLE"
    error_message = "The image_tag_mutability must be either 'MUTABLE' or 'IMMUTABLE'."
  }
  
}

variable "scan_on_push" {
  description = "Whether to enable image scanning on push for the ECR repository"
  type        = bool
  default     = true

  validation {
    condition     = can(regex("^(true|false)$", tostring(var.scan_on_push)))
    error_message = "The scan_on_push must be a boolean value."
  }
  
}