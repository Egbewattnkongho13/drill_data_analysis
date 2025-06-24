provider "aws" {
  region = "us-east-1"
  profile = "jr"

  default_tags {
    tags = {
      Environment  = "dev"
      Owner        = "OyeData"}
  }
}

