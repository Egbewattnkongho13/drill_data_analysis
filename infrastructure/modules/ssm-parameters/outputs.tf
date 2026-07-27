output "parameter_arns" {
  description = "The ARNs of the created SSM parameters."
  value       = {
    kaggle_username          = aws_ssm_parameter.kaggle_username.arn
    kaggle_key               = aws_ssm_parameter.kaggle_key.arn
    sink_type                = aws_ssm_parameter.sink_type.arn
    kaggle_data_source_urls  = aws_ssm_parameter.kaggle_data_source_urls.arn
    crawler_data_source_urls = aws_ssm_parameter.crawler_data_source_urls.arn
    kaggle_destination       = aws_ssm_parameter.kaggle_destination.arn
    bronze_type              = aws_ssm_parameter.bronze_type.arn
    bronze_prefix            = aws_ssm_parameter.bronze_prefix.arn
    bronze_key               = aws_ssm_parameter.bronze_key.arn
    bronze_staging_prefix    = aws_ssm_parameter.bronze_staging_prefix.arn
    silver_sink_type         = aws_ssm_parameter.silver_sink_type.arn
    silver_destination       = aws_ssm_parameter.silver_destination.arn
  }
}