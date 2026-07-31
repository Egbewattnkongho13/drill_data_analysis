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


variable "kaggle_data_source_urls" {
  description = "A comma-separated list of Kaggle dataset URLs to download."
  type        = string

  validation {
    condition     = var.kaggle_data_source_urls == "" || alltrue([for url in split(",", var.kaggle_data_source_urls) : can(regex("^https://.*", trimspace(url)))])
    error_message = "All kaggle_data_source_urls must be valid URLs starting with https://."
  }
}

variable "crawler_data_source_urls" {
  description = "A comma-separated list of URLs to crawl for data."
  type        = string

  validation {
    condition     = var.crawler_data_source_urls == "" || alltrue([for url in split(",", var.crawler_data_source_urls) : can(regex("^https://.*", trimspace(url)))])
    error_message = "All crawler_data_source_urls must be valid URLs."
  }
}

# Ingestion destination
variable "kaggle_destination" {
  description = "Destination path in bronze bucket for Kaggle ingestion output (e.g., 'raw/dev/glue_ingestion/')."
  type        = string
  default     = "raw/dev/glue_ingestion/"
}

# Bronze layer source configuration (for silver-transform)
variable "bronze_type" {
  description = "Type of bronze source (typically 's3')."
  type        = string
  default     = "s3"

  validation {
    condition     = var.bronze_type == "s3"
    error_message = "Currently only 's3' is supported for bronze_type."
  }
}

variable "bronze_prefix" {
  description = "Prefix path in bronze bucket to read from (e.g., 'raw/dev/glue_ingestion/')."
  type        = string
  default     = "raw/dev/glue_ingestion/"
}

variable "bronze_key" {
  # Ingestion names the archive from the Kaggle slug with '/' replaced by '_',
  # so 'afrniomelo/3w-dataset' lands as 'afrniomelo_3w-dataset.zip'.
  description = "Specific S3 key for bronze source file (e.g., 'raw/dev/glue_ingestion/afrniomelo_3w-dataset.zip'). Optional - use either key or prefix."
  type        = string
  default     = "raw/dev/glue_ingestion/afrniomelo_3w-dataset.zip"
}

variable "bronze_staging_prefix" {
  description = "Prefix in the bronze bucket where silver-transform unzips archives before Spark reads them. Must not sit under bronze_prefix."
  type        = string
  default     = "_unzipped/dev/3w_dataset"
}

# Silver layer configuration
variable "silver_sink_type" {
  description = "Type of silver sink. Valid values are 's3' or 'local'."
  type        = string
  default     = "s3"

  validation {
    condition     = contains(["s3", "local"], var.silver_sink_type)
    error_message = "The silver_sink_type must be either 's3' or 'local'."
  }
}

variable "silver_destination" {
  description = "Destination path in silver bucket (e.g., 'silver/dev/3w_dataset/')."
  type        = string
  default     = "silver/dev/3w_dataset/"
}
