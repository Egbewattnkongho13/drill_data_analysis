provider "aws" {
  region = "us-east-1"


  default_tags {
    tags = {
      Environment  = "dev"
      Owner        = "OyeData"
      project_name = "drill_data_analysis"
    }
  }
}

