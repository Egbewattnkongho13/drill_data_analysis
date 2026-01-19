resource "aws_glue_job" "this" {
  name         = var.glue_job_name
  role_arn     = aws_iam_role.glue_job_role.arn
  glue_version = var.glue_version
  worker_type  = var.glue_job_worker_type

  default_arguments = {
    "--job-language"             = "python"
    "--enable-glue-datacatalog"  = ""
    "--additional-python-modules" = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_wheel.key}"
  }

  command {
    name            = "glueray"
    python_version  = var.python_version
    runtime         = var.glue_runtime
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.glue_job_script.key}"
  }

  depends_on = [
    aws_s3_object.glue_job_script,
    aws_s3_object.glue_job_wheel,
  ]
}
