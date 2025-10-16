# Test file to demonstrate resource grouping
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Multiple S3 buckets that should be grouped together
resource "aws_s3_bucket" "logs" {
  bucket = "my-app-logs-bucket"
}

resource "aws_s3_bucket" "data" {
  bucket = "my-app-data-bucket"
}

resource "aws_s3_bucket" "backups" {
  bucket = "my-app-backups-bucket"
}

# Multiple Lambda functions that should be grouped together
resource "aws_lambda_function" "processor" {
  function_name = "my-app-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.9"
  filename      = "processor.zip"
}

resource "aws_lambda_function" "api" {
  function_name = "my-app-api"
  role          = aws_iam_role.lambda_role.arn
  handler       = "api.handler"
  runtime       = "python3.9"
  filename      = "api.zip"
}

resource "aws_lambda_function" "worker" {
  function_name = "my-app-worker"
  role          = aws_iam_role.lambda_role.arn
  handler       = "worker.handler"
  runtime       = "python3.9"
  filename      = "worker.zip"
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "my-app-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Multiple RDS instances that should be grouped together
resource "aws_db_instance" "primary" {
  identifier        = "my-app-primary-db"
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
}

resource "aws_db_instance" "replica" {
  identifier        = "my-app-replica-db"
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
}
