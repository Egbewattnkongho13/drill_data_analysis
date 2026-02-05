resource "aws_cloudwatch_log_group" "ingestion-lg" {
  name              = "/glue/${var.glue_job_name}"
  retention_in_days = 14
}
resource "aws_glue_job" "this" {
  name         = var.glue_job_name
  role_arn     = aws_iam_role.glue_job_role.arn
  glue_version      = var.glue_version
  worker_type       = var.glue_job_worker_type
  number_of_workers = var.glue_job_number_of_workers

  default_arguments = {
    "--job-language"             = "python"
    "--enable-metrics"           = "true"      
    "--TempDir"                  = "s3://${aws_s3_bucket.glue_assets.id}/temp/"
    "--enable-glue-datacatalog"  = ""
    "--extra-py-files"           = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_wheel.key}"
    "--additional-python-modules" = "omegaconf==2.3.0,pyyaml==6.0.1,requests==2.28.0,pydantic==2.11.7"
    "--continuous-log-logGroup"  = aws_cloudwatch_log_group.ingestion-lg.name
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
  }

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_script.key}"
  }

  tags = {
    Name = var.glue_job_name
  }

  depends_on = [
    aws_s3_object.glue_job_script,
    aws_s3_object.glue_job_wheel,
  ]
}
