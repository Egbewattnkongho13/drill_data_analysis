locals {
  # Find all wheel files in the dist directory
  wheel_dir = abspath(var.glue_job_dist_path)

  # Get all .whl files from the dist directory (use try-catch for robustness)
  wheel_files = try(fileset(local.wheel_dir, "*.whl"), [])

  # Create a map of wheel files with their full paths
  wheels_map = {
    for wheel in local.wheel_files :
    wheel => {
      filename = wheel
      path     = "${local.wheel_dir}/${wheel}"
    }
  }
}

resource "aws_s3_object" "glue_job_script" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.glue_job_script_s3_key
  source = var.glue_job_script_local_path
  etag   = filemd5(var.glue_job_script_local_path)
}

# Upload all wheel files to S3
resource "aws_s3_object" "glue_job_wheels" {
  for_each = local.wheels_map

  bucket = aws_s3_bucket.glue_assets.id
  key    = "wheels/${each.value.filename}"
  source = each.value.path
  etag   = filemd5(each.value.path)
}