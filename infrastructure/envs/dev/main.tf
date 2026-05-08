data "aws_caller_identity" "current" {}

module "ssm_parameters" {
  source = "../../modules/ssm-parameters"

  # Credentials and source URLs
  kaggle_username          = var.kaggle_username
  kaggle_key               = var.kaggle_key
  sink_type                = var.sink_type
  kaggle_data_source_urls  = var.kaggle_data_source_urls
  crawler_data_source_urls = var.crawler_data_source_urls

  # Runtime configs: types, destinations, prefixes
  kaggle_destination = var.kaggle_destination
  bronze_type        = var.bronze_type
  bronze_prefix      = var.bronze_prefix
  silver_sink_type   = var.silver_sink_type
  silver_destination = var.silver_destination
}

module "gold_lambda_ecr" {
  source               = "../../modules/ecr"
  repository_name      = "gold-lambda-ecr"
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true

}
module "silver_lambda_ecr" {
  source               = "../../modules/ecr"
  repository_name      = "silver-lambda-ecr"
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true
}
module "ingestion_lambda_ecr" {
  source               = "../../modules/ecr"
  repository_name      = "ingestion-lambda-ecr"
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true
}

# Create Lambda functions from ECR images

module "ingestion_lambda" {
  source             = "../../modules/LambdaECR"
  lambda_role_arn    = module.data_lake.ingestion_lambda_execution_role_arn
  lambda_name        = "ingestion-lambda"
  ecr_repository_url = module.ingestion_lambda_ecr.repository_url
  ecr_repository_arn = module.ingestion_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.ingestion_docker_image_tag
  ssm_parameter_arns = values(module.ssm_parameters.parameter_arns)
  timeout            = 900
}


module "silver_transform_lambda" {
  source             = "../../modules/LambdaECR"
  lambda_role_arn    = module.data_lake.silver_transform_role_arn
  lambda_name        = "silver-transform-lambda"
  ecr_repository_url = module.silver_lambda_ecr.repository_url
  ecr_repository_arn = module.silver_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.silver_docker_image_tag
}

module "gold_transform_lambda" {
  source             = "../../modules/LambdaECR"
  lambda_role_arn    = module.data_lake.gold_transform_role_arn
  lambda_name        = "gold-transform-lambda"
  ecr_repository_url = module.gold_lambda_ecr.repository_url
  ecr_repository_arn = module.gold_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.gold_docker_image_tag
}

# Setup DataLake
module "data_lake" {
  source = "../../modules/datalake"

  datalake_name = "oye-dl"
  account_id    = data.aws_caller_identity.current.account_id
  region        = var.region
}

# Setup Glue Job for Ingestion
module "glue_ingestion_job" {
  source = "../../modules/glue"

  glue_job_name              = "drill-data-ingestion-job"
  glue_job_script_local_path = "${path.module}/../../../glue-jobs/glue-ingestion/glue_job.py"
  glue_job_script_s3_key     = "scripts/glue_ingestion_job.py"
  glue_job_dist_path         = "${path.module}/../../../glue-jobs/glue-ingestion/dist"
  ssm_parameter_arns         = values(module.ssm_parameters.parameter_arns)
  bronze_bucket_name         = module.data_lake.bronze_bucket_name
}

# Setup Glue Job for Silver Transform
module "glue_silver_transform_job" {
  source = "../../modules/glue"

  glue_job_name              = "drill-data-silver-transform-job"
  glue_job_script_local_path = "${path.module}/../../../glue-jobs/silver-transform/threed_w_transform_job.py"
  glue_job_script_s3_key     = "scripts/glue_silver_transform_job.py"
  glue_job_dist_path         = "${path.module}/../../../glue-jobs/silver-transform/dist"
  ssm_parameter_arns         = values(module.ssm_parameters.parameter_arns)
  bronze_bucket_name         = module.data_lake.bronze_bucket_name
  silver_bucket_name         = module.data_lake.silver_bucket_name

  catalog_database = "oye_silver"
  catalog_table    = "threed_w_dataset"
}