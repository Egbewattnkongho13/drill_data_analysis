variable "glue_job_name" {
  description = "The name of the AWS Glue job."
  type        = string

  validation {
    condition     = length(var.glue_job_name) > 0 && length(var.glue_job_name) <= 255
    error_message = "The glue_job_name must be between 1 and 255 characters long."
  }
}

variable "glue_job_script_local_path" {
  description = "The local path to the Glue job script."
  type        = string

  validation {
    condition     = fileexists(var.glue_job_script_local_path)
    error_message = "The file specified in glue_job_script_local_path does not exist."
  }
}

variable "glue_job_script_s3_key" {
  description = "The S3 key for the Glue job script."
  type        = string

  validation {
    condition     = endswith(var.glue_job_script_s3_key, ".py")
    error_message = "The glue_job_script_s3_key must end with '.py'."
  }
}

variable "glue_job_worker_type" {
  description = "The worker type for the Glue job."
  type        = string
  default     = "Z.2X"

  validation {
    condition     = var.glue_job_worker_type != ""
    error_message = "The glue_job_worker_type cannot be empty."
  }
}

variable "glue_version" {
  description = "The Glue version."
  type        = string
  default     = "4.0"

  validation {
    condition     = contains(["4.0", "3.0", "2.0", "1.0"], var.glue_version)
    error_message = "The glue_version must be one of '4.0', '3.0', '2.0', or '1.0'."
  }
}

variable "python_version" {
  description = "The Python version for the Glue job."
  type        = string
  default     = "3.9"

  validation {
    condition     = contains(["3.9", "3.7", "3.6"], var.python_version)
    error_message = "The python_version must be one of '3.9', '3.7', or '3.6'."
  }
}

variable "glue_runtime" {
  description = "The runtime for the Glue job."
  type        = string
  default     = "Ray2.4"

  validation {
    condition     = var.glue_runtime != ""
    error_message = "The glue_runtime cannot be empty."
  }
}

variable "ssm_parameter_arns" {
  description = "A list of ARNs for the SSM parameters that the Glue job needs to access."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for arn in var.ssm_parameter_arns : can(regex("^arn:aws:ssm:[^:]+:[^:]+:parameter/.*$", arn))
    ])
    error_message = "All elements in ssm_parameter_arns must be valid SSM parameter ARNs."
  }
}