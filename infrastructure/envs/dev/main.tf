data "aws_caller_identity" "current" {}

module "ssm_parameters" {
  source = "../../modules/ssm-parameters"

  kaggle_username          = var.kaggle_username
  kaggle_key               = var.kaggle_key
  sink_type                = var.sink_type
  sink_bucket              = var.sink_bucket
  kaggle_data_source_urls  = var.kaggle_data_source_urls
  crawler_data_source_urls = var.crawler_data_source_urls
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
  name               = "ingestion-lambda-role"
  lambda_name        = "ingestion-lambda"
  ecr_repository_url = module.ingestion_lambda_ecr.repository_url
  ecr_repository_arn = module.ingestion_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.ingestion_docker_image_tag
  ssm_parameter_arns = values(module.ssm_parameters.parameter_arns)
  timeout            = 120
}


module "silver_transform_lambda" {
  source             = "../../modules/LambdaECR"
  name               = "silver-transform-lambda-role"
  lambda_name        = "silver-transform-lambda"
  ecr_repository_url = module.silver_lambda_ecr.repository_url
  ecr_repository_arn = module.silver_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.silver_docker_image_tag
}

module "gold_transform_lambda" {
  source             = "../../modules/LambdaECR"
  name               = "gold-transform-lambda-role"
  lambda_name        = "gold-transform-lambda"
  ecr_repository_url = module.gold_lambda_ecr.repository_url
  ecr_repository_arn = module.gold_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.gold_docker_image_tag
}

# Setup DataLake
module "data_lake" {
  source = "../../modules/datalake"

  datalake_name               = "oye-dl"
  account_id                  = data.aws_caller_identity.current.account_id
  ingestion_lambda_arn        = module.ingestion_lambda.lambda_role_arn
  silver_transform_lambda_arn = module.silver_transform_lambda.lambda_role_arn
  gold_transform_lambda_arn   = module.gold_transform_lambda.lambda_role_arn
  region                      = var.region

  depends_on = [
    module.ingestion_lambda,
    module.silver_transform_lambda,
    module.gold_transform_lambda
  ]
}
