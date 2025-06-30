provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Project     = "drill_data_analysis"
      Environment = "dev"
      owner       = "OyeData"
    }
  }
}

