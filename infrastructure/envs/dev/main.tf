


module "gold_lambda_ecr" {
  source = "../../modules/ecr"
  repository_name = "gold-lambda-ecr"
  image_tag_mutability = "MUTABLE"
  scan_on_push = true
  
}
module "silver_lambda_ecr" {
  source = "../../modules/ecr"
  repository_name = "silver-lambda-ecr"
  image_tag_mutability = "MUTABLE"  
  scan_on_push = true
}
module "ingestion_lambda_ecr" {
  source = "../../modules/ecr"
  repository_name = "ingestion-lambda-ecr"
  image_tag_mutability = "MUTABLE"  
  scan_on_push = true
}