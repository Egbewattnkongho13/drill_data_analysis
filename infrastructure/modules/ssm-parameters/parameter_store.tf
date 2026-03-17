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

resource "aws_ssm_parameter" "sink_bucket" {
  name  = "/drill-data-analysis/dev/sink/bucket_name"
  value = var.sink_bucket
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