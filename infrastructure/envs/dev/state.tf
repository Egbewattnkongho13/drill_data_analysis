terraform {
  backend "s3" {
    bucket         = "egbewattdevops-state-bucket-dev"
    key            = "terraform-state/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock-table"
    encrypt        = true
  }
}
