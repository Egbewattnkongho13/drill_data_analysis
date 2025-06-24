# creates IAM roles for the bronze layer of the data lake
resource "aws_iam_role" "bronze_ingestion_role" {
  name = "${var.datalake_name}_bronze_ingestion_role"

  assume_role_policy = data.aws_iam_policy_document.bronze_assume_role_policy.json

  tags =  {
      Layer   = "bronze"
      Project = var.datalake_name
    }

  
}

resource "aws_iam_role_policy_attachment" "bronze_policy_to_ingestion_role_attachment" {
    role       = aws_iam_role.bronze_ingestion_role.arn
    policy_arn = data.aws_iam_policy_document.bronze_write_policy.json
   
}

# creates IAM roles for the silver layer of the data lake

resource "aws_iam_role" "silver_tansform_role" {
  name = "${var.datalake_name}_silver_transform_role"

  assume_role_policy = data.aws_iam_policy_document.silver_assume_role_policy.json 

    tags =  {
      Layer   = "silver"
      Project = var.datalake_name
    }
  
}


resource "aws_iam_role_policy_attachment" "silver_write_policy_to_transform_role_attachment" {
    role       = aws_iam_role.silver_tansform_role.arn
    policy_arn = data.aws_iam_policy_document.silver_write_policy.json  
}

resource "aws_iam_role_policy_attachment" "bronze_read_to_silver_policy_to_transform_role_attachment" {
    role       = aws_iam_role.silver_tansform_role.arn
    policy_arn = data.aws_iam_policy_document.bronze_read_to_silver_policy.json
}

# creates IAM roles for the gold layer of the data lake

resource "aws_iam_role" "gold_transform_role" {
  name = "${var.datalake_name}_gold_transform_role"

  assume_role_policy = data.aws_iam_policy_document.gold_assume_role_policy.json

  tags = {
      Layer   = "gold"
      Project = var.datalake_name
    } 
}

resource "aws_iam_role_policy_attachment" "gold_write_policy_to_transform_role_attachment" {
  role = aws_iam_role.gold_transform_role.arn
  policy_arn = data.aws_iam_policy_document.gold_write_policy.json 
}

resource "aws_iam_role_policy_attachment" "silver_read_to_gold_policy_to_transform_role_attachment" {
  role = aws_iam_role.gold_transform_role.arn
  policy_arn = data.aws_iam_policy_document.silver_read_to_gold_policy.json 
}

