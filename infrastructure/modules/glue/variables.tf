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
  default     = "G.1X" # Changed from Z.2X to G.1X for Spark ETL jobs

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


variable "ssm_parameter_arns" {
  description = "A list of ARNs for the SSM parameters that the Glue job needs to access."
  type        = list(string)
  default     = []

}

variable "glue_job_number_of_workers" {
  description = "The number of workers for the Glue job."
  type        = number
  default     = 5
}