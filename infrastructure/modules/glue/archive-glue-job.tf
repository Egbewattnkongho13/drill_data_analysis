data "local_file" "wheel_filename" {
  filename = abspath("${path.module}/../../../glue/dist/wheel_name.txt")
}

resource "aws_s3_object" "glue_job_script" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.glue_job_script_s3_key
  source = var.glue_job_script_local_path
  etag   = filemd5(var.glue_job_script_local_path)
}

resource "aws_s3_object" "glue_job_wheel" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = data.local_file.wheel_filename.content
  source = abspath("${path.module}/../../../glue/dist/${data.local_file.wheel_filename.content}")

  depends_on = [
    data.local_file.wheel_filename
  ]
}