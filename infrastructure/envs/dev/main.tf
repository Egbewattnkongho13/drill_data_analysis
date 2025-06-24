data "aws_caller_identity" "current" {}

module "DataLake" {
  source = "../../modules/datalake"

  datalake_name                 = "oye-data-lake"
  account_id                    = data.aws_caller_identity.current.account_id
  ingestion_lambda_name         = "ingestion_lambda"
  silver_transform_lambda_name  = "silver_transform_lambda"
  ide_gold_tranform_lambda_name = "gold_transform_lambda"
  region                        = var.region

}

