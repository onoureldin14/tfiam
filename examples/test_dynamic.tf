# Test file with various AWS services to test dynamic permissions
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# WAF resources (not in predefined list)
resource "aws_wafv2_web_acl" "main" {
  name  = "my-waf-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }
}

resource "aws_wafv2_rule_group" "main" {
  name     = "my-waf-rule-group"
  scope    = "REGIONAL"
  capacity = 10
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = "example.com"
    origin_id   = "example"
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "example"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "allow-all"
  }
}

# EKS cluster
resource "aws_eks_cluster" "main" {
  name     = "my-eks-cluster"
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = ["subnet-12345", "subnet-67890"]
  }
}

# EKS node group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "my-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = ["subnet-12345", "subnet-67890"]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }
}

# IAM roles for EKS
resource "aws_iam_role" "eks_cluster" {
  name = "my-eks-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

resource "aws_iam_role" "eks_node" {
  name = "my-eks-node-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

# DynamoDB table
resource "aws_dynamodb_table" "main" {
  name         = "my-dynamodb-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# ElastiCache cluster
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "my-redis-cluster"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# API Gateway
resource "aws_api_gateway_rest_api" "main" {
  name = "my-api-gateway"
}

resource "aws_api_gateway_resource" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "users"
}

# Step Functions
resource "aws_sfn_state_machine" "main" {
  name     = "my-state-machine"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "A simple state machine"
    StartAt = "Hello"
    States = {
      Hello = {
        Type     = "Task"
        Resource = "arn:aws:lambda:us-east-1:123456789012:function:HelloFunction"
        End      = true
      }
    }
  })
}

resource "aws_iam_role" "step_functions" {
  name = "my-step-functions-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}
