data "aws_caller_identity" "current" {}

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

module "ingestion_lambada" {
  source             = "../../modules/LambdaECR"
  name               = "ingestion-lambda-role"
  lambda_name        = "ingestion-lambda"
  ecr_repository_url = module.ingestion_lambda_ecr.repository_url
  ecr_repository_arn = module.ingestion_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.ingestion_docker_image_tag
}

module "Silver_transform_lambada" {
  source             = "../../modules/LambdaECR"
  name               = "silver-transform-lambda-role"
  lambda_name        = "silver-transform-lambda"
  ecr_repository_url = module.silver_lambda_ecr.repository_url
  ecr_repository_arn = module.silver_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.silver_docker_image_tag
}

module "Gold_transform_lambada" {
  source             = "../../modules/LambdaECR"
  name               = "gold-transform-lambda-role"
  lambda_name        = "gold-transform-lambda"
  ecr_repository_url = module.gold_lambda_ecr.repository_url
  ecr_repository_arn = module.gold_lambda_ecr.arn_of_ecr_repository
  docker_image_tag   = var.gold_docker_image_tag
}

# # Setup DataLake
# module "DataLake" {
#   source = "../../modules/datalake"

#   datalake_name               = "oye-data-lake"
#   account_id                  = data.aws_caller_identity.current.account_id
#   ingestion_lambda_arn        = module.ingestion_lambada.arn_of_lambda_function
#   silver_transform_lambda_arn = module.Silver_transform_lambada.arn_of_lambda_function
#   gold_transform_lambda_arn   = module.Gold_transform_lambada.arn_of_lambda_function
#   region                      = var.region

#   depends_on = [
#     module.ingestion_lambada,
#     module.Silver_transform_lambada,
#     module.Gold_transform_lambada
#   ]
# }
