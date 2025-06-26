

module "ingestion_lambda" {
  source = "../modules/LambdaECR"
  name   = "lambda_a"
  
}

module "silver_transformation_lambda" {
  source = "../modules/LambdaECR"
  name   = "lambda_b"
  
}

module "gold_transformation_lambda" {
  source = "../modules/LambdaECR"
  name   = "lambda_c"
  
}