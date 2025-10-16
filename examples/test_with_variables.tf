# Test file with variables, locals, and data sources
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "my-app"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# Locals
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Data sources
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# S3 Bucket with variable-based name
resource "aws_s3_bucket" "main" {
  bucket = "${local.name_prefix}-storage"

  tags = local.common_tags
}

# IAM Role with variable-based name
resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}-lambda-role"

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

  tags = local.common_tags
}

# Lambda function with variable-based name
resource "aws_lambda_function" "main" {
  function_name = "${local.name_prefix}-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.9"

  filename = "lambda.zip"

  tags = local.common_tags
}

# RDS instance with variable-based identifier
resource "aws_db_instance" "main" {
  identifier        = "${local.name_prefix}-database"
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  tags = local.common_tags
}

# CloudWatch Log Group with variable-based name
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.main.function_name}"
  retention_in_days = 14

  tags = local.common_tags
}
