# creates IAM roles for the bronze layer of the data lake
resource "aws_iam_role" "bronze_ingestion_role" {
  name = "${var.datalake_name}-bronze-ingestion-role"

  assume_role_policy = data.aws_iam_policy_document.bronze_assume_role_policy.json

  tags = {
    Layer = "bronze"
  }


}

resource "aws_iam_role_policy" "bronze_write_policy" {
  name   = "${var.datalake_name}-bronze-write-policy"
  role   = aws_iam_role.bronze_ingestion_role.name
  policy = data.aws_iam_policy_document.bronze_write_policy.json

}

# creates IAM roles for the silver layer of the data lake

resource "aws_iam_role" "silver_tansform_role" {
  name = "${var.datalake_name}-silver-transform-role"

  assume_role_policy = data.aws_iam_policy_document.silver_assume_role_policy.json

  tags = {
    Layer = "silver"
  }

}


resource "aws_iam_role_policy" "silver_write_policy" {
  name   = "${var.datalake_name}-silver-write-policy"
  role   = aws_iam_role.silver_tansform_role.name
  policy = data.aws_iam_policy_document.silver_write_policy.json
}

resource "aws_iam_role_policy" "bronze_read_policy" {
  name   = "${var.datalake_name}-bronze-read-policy"
  role   = aws_iam_role.silver_tansform_role.name
  policy = data.aws_iam_policy_document.bronze_read_policy.json
}

# creates IAM roles for the gold layer of the data lake

resource "aws_iam_role" "gold_transform_role" {
  name = "${var.datalake_name}-gold-transform-role"

  assume_role_policy = data.aws_iam_policy_document.gold_assume_role_policy.json

  tags = {
    Layer = "gold"
  }
}

resource "aws_iam_role_policy" "gold_write_policy" {
  name   = "${var.datalake_name}-gold-write-policy"
  role   = aws_iam_role.gold_transform_role.name
  policy = data.aws_iam_policy_document.gold_write_policy.json
}

resource "aws_iam_role_policy" "silver_read_policy" {
  name   = "${var.datalake_name}-silver-read-policy"
  role   = aws_iam_role.gold_transform_role.name
  policy = data.aws_iam_policy_document.silver_read_policy.json
}

