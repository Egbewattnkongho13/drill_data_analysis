output "parameter_arns" {
  description = "The ARNs of the created SSM parameters."
  value       = {
    kaggle_username          = aws_ssm_parameter.kaggle_username.arn
    kaggle_key               = aws_ssm_parameter.kaggle_key.arn
    sink_type                = aws_ssm_parameter.sink_type.arn
    sink_bucket              = aws_ssm_parameter.sink_bucket.arn
    kaggle_data_source_urls  = aws_ssm_parameter.kaggle_data_source_urls.arn
    crawler_data_source_urls = aws_ssm_parameter.crawler_data_source_urls.arn
  }
}