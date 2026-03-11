locals {
  # Find the wheel file automatically in the dist directory
  wheel_dir      = abspath("${path.module}/../../../glue/dist")
  wheel_filename = element(tolist(fileset(local.wheel_dir, "*.whl")), 0)
  wheel_file     = "${local.wheel_dir}/${local.wheel_filename}"
}

resource "aws_s3_object" "glue_job_script" {
  
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.glue_job_script_s3_key
  source = var.glue_job_script_local_path
  etag   = filemd5(var.glue_job_script_local_path)
}

resource "aws_s3_object" "glue_job_wheel" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = local.wheel_filename
  source = local.wheel_file
  etag   = filemd5(local.wheel_file)
}