locals {
  # Find the zip file automatically in the dist directory.
  # This assumes there is only one .zip file.
  bundle_dir      = abspath("${path.module}/../../../glue/dist")
  bundle_filename = element(tolist(fileset(local.bundle_dir, "*.zip")), 0)
  bundle_file     = "${local.bundle_dir}/${local.bundle_filename}"
}

resource "aws_s3_object" "glue_job_script" {
  
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.glue_job_script_s3_key
  source = var.glue_job_script_local_path
  etag   = filemd5(var.glue_job_script_local_path)
}

resource "aws_s3_object" "glue_job_bundle" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = local.bundle_filename
  source = local.bundle_file
  etag   = filemd5(local.bundle_file)
}