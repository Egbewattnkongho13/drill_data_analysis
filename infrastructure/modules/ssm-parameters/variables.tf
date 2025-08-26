variable "kaggle_username" {
  description = "Kaggle username for authentication."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_]{1,50}$", var.kaggle_username))
    error_message = "The Kaggle username must be between 1 and 50 characters long and can only contain letters, numbers, and underscores."
  }
}

variable "kaggle_key" {
  description = "Kaggle API key for authentication."
  type        = string
  sensitive = true

  validation {
    condition     = can(regex("^[a-f0-9]{32}$", var.kaggle_key))
    error_message = "The Kaggle key must be a 32-character hexadecimal string."
  }
}

variable "sink_type" {
  description = "The type of sink to use for storing data. Valid values are 's3' or 'local'."
  type        = string

  validation {
    condition     = contains(["s3", "local"], var.sink_type)
    error_message = "The sink_type must be either 's3' or 'local'."
  }
}

variable "sink_bucket" {
  description = "The name of the S3 bucket to use as the sink."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9.-]{3,63}$", var.sink_bucket))
    error_message = "The sink_bucket name must be a valid S3 bucket name."
  }
}

variable "kaggle_data_source_urls" {
  description = "A list of Kaggle dataset URLs to download."
  type        = list(string)

  validation {
    condition     = alltrue([for url in var.kaggle_data_source_urls : can(regex("^https://www.kaggle.com/api/v1/datasets/download/.", url))])
    error_message = "All kaggle_data_source_urls must be valid Kaggle API download URLs."
  }
}

variable "crawler_data_source_urls" {
  description = "A list of URLs to crawl for data."
  type        = list(string)

  validation {
    condition     = alltrue([for url in var.crawler_data_source_urls : can(regex("^https://.*", url))])
    error_message = "All crawler_data_source_urls must be valid URLs."
  }
}
