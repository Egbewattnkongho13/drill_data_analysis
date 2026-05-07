resource "aws_ssm_parameter" "kaggle_username" {
  name  = "/drill-data-analysis/dev/kaggle/username"
  value = var.kaggle_username
  type  = "String"
}

resource "aws_ssm_parameter" "kaggle_key" {
  name  = "/drill-data-analysis/dev/kaggle/key"
  value = var.kaggle_key
  type  = "SecureString"
}

resource "aws_ssm_parameter" "sink_type" {
  name  = "/drill-data-analysis/dev/sink/type"
  value = var.sink_type
  type  = "String"
}


resource "aws_ssm_parameter" "kaggle_data_source_urls" {
  name  = "/drill-data-analysis/dev/kaggle/data_source_urls"
  value = var.kaggle_data_source_urls
  type  = "StringList"
}

resource "aws_ssm_parameter" "crawler_data_source_urls" {
  name  = "/drill-data-analysis/dev/crawler/data_source_urls"
  value = var.crawler_data_source_urls
  type  = "StringList"
}

# Destination paths and types (runtime configs)
resource "aws_ssm_parameter" "kaggle_destination" {
  name  = "/drill-data-analysis/dev/kaggle/destination"
  value = var.kaggle_destination
  type  = "String"
}

resource "aws_ssm_parameter" "bronze_type" {
  name  = "/drill-data-analysis/dev/bronze/type"
  value = var.bronze_type
  type  = "String"
}

resource "aws_ssm_parameter" "bronze_prefix" {
  name  = "/drill-data-analysis/dev/bronze/prefix"
  value = var.bronze_prefix
  type  = "String"
}

resource "aws_ssm_parameter" "silver_sink_type" {
  name  = "/drill-data-analysis/dev/silver/sink_type"
  value = var.silver_sink_type
  type  = "String"
}

resource "aws_ssm_parameter" "silver_destination" {
  name  = "/drill-data-analysis/dev/silver/destination"
  value = var.silver_destination
  type  = "String"
}