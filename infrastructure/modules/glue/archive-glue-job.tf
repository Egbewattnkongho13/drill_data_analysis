resource "null_resource" "run_bundle_script" {
  triggers = {
    # Trigger a rebuild and re-upload if the bundle script changes
    bundle_script_hash = filemd5(abspath("${path.module}/../../../glue/bundle.sh"))
    # Trigger if the pyproject.toml changes (which can affect the wheel version)
    pyproject_hash     = filemd5(abspath("${path.module}/../../../glue/pyproject.toml"))
    # Also trigger if the main glue job script changes
    glue_job_script_hash = filemd5(var.glue_job_script_local_path)
  }

  provisioner "local-exec" {
    command = "bash bundle.sh"
    # Ensure the command is run from the glue directory
    working_dir = abspath("${path.module}/../../../glue")
  }
}

data "local_file" "wheel_filename" {
  # This file is created by the bundle.sh script
  filename = abspath("${path.module}/../../../glue/dist/wheel_name.txt")
  depends_on = [
    null_resource.run_bundle_script
  ]
}

resource "aws_s3_object" "glue_job_script" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.glue_job_script_s3_key
  source = var.glue_job_script_local_path
  etag   = filemd5(var.glue_job_script_local_path)

  depends_on = [
    null_resource.run_bundle_script
  ]
}

resource "aws_s3_object" "glue_job_wheel" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = data.local_file.wheel_filename.content
  source = abspath("${path.module}/../../../glue/dist/${data.local_file.wheel_filename.content}")


  depends_on = [
    null_resource.run_bundle_script,
    data.local_file.wheel_filename
  ]
}