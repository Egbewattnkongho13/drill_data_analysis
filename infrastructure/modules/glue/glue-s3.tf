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
    "--enable-glue-datacatalog"  = ""
    "--pip-install"                      = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_wheel.key}"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.ingestion-lg.name
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
  }

  command {
    name            = "glueetl"
    python_version  = var.python_version
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_script.key}"
  }

  depends_on = [
    aws_s3_object.glue_job_script,
    aws_s3_object.glue_job_wheel,
  ]
}
