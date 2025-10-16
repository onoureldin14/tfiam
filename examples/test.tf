# Comprehensive TFIAM Test File
# This file tests all major features:
# - Variables and locals resolution
# - Resource grouping
# - Dynamic/unknown AWS services
# - Complex resource configurations
# - Multiple resource types per service

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "tfiam-test"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "bucket_names" {
  description = "List of S3 bucket names"
  type        = list(string)
  default     = ["app-data", "backups", "logs"]
}

# Locals
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    CreatedBy   = "tfiam"
  }

  bucket_prefix = "${var.project_name}-${var.environment}"

  # Simplified monitoring config
  retention_days = 30
  log_level = "INFO"

  # Local referencing other locals
  full_project_name = "${local.bucket_prefix}-${var.region}"
}

# =============================================================================
# VPC and Networking (EC2 Service - Testing Grouping)
# =============================================================================

# Multiple VPC resources that should be grouped together
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-vpc"
  })
}

resource "aws_vpc" "secondary" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-secondary-vpc"
  })
}

# Subnets that should be grouped with VPC
resource "aws_subnet" "public_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.region}a"

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-public-1"
    Type = "public"
  })
}

resource "aws_subnet" "public_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}b"

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-public-2"
    Type = "public"
  })
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.region}a"

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-private"
    Type = "private"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-igw"
  })
}

# Security Groups (should be grouped together)
resource "aws_security_group" "web" {
  name_prefix = "${local.full_project_name}-web-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-web-sg"
  })
}

resource "aws_security_group" "database" {
  name_prefix = "${local.full_project_name}-db-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-db-sg"
  })
}

# =============================================================================
# S3 Buckets (Testing Dynamic List Processing)
# =============================================================================

# Multiple S3 buckets using variables - should be grouped
resource "aws_s3_bucket" "data_buckets" {
  for_each = toset(var.bucket_names)

  bucket = "${local.bucket_prefix}-${each.value}"

  tags = merge(local.common_tags, {
    Name = "${local.bucket_prefix}-${each.value}"
    Type = "data"
  })
}

resource "aws_s3_bucket" "static_assets" {
  bucket = "${local.bucket_prefix}-static-assets"

  tags = merge(local.common_tags, {
    Name = "${local.bucket_prefix}-static-assets"
    Type = "static"
  })
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${local.bucket_prefix}-terraform-state"

  tags = merge(local.common_tags, {
    Name = "${local.bucket_prefix}-terraform-state"
    Type = "terraform"
  })
}

# S3 bucket configurations
resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# =============================================================================
# RDS Database (Testing Complex Resource Types)
# =============================================================================

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${local.full_project_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private.id, aws_subnet.public_1.id]

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-db-subnet-group"
  })
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "postgres13"
  name   = "${local.full_project_name}-db-params"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-db-params"
  })
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${local.full_project_name}-db"

  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "appdb"
  username = "dbuser"
  password = "changeme123"  # In real usage, use secrets manager

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name   = aws_db_parameter_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-db"
  })
}

# =============================================================================
# Lambda Functions (Testing Multiple Functions)
# =============================================================================

# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${local.full_project_name}-lambda-execution"

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

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Multiple Lambda functions
resource "aws_lambda_function" "api_handler" {
  filename         = "api_handler.zip"
  function_name    = "${local.full_project_name}-api"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "index.handler"
  source_code_hash = "dummy_hash"
  runtime         = "python3.9"

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DB_HOST     = aws_db_instance.main.endpoint
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-api"
  })
}

resource "aws_lambda_function" "data_processor" {
  filename         = "data_processor.zip"
  function_name    = "${local.full_project_name}-processor"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "processor.handler"
  source_code_hash = "dummy_hash"
  runtime         = "python3.9"

  timeout = 300

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-processor"
  })
}

# =============================================================================
# CloudWatch (Testing Monitoring Resources)
# =============================================================================

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset(["api", "processor"])

  name              = "/aws/lambda/${local.full_project_name}-${each.value}"
  retention_in_days = local.retention_days

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-${each.value}-logs"
  })
}

resource "aws_cloudwatch_log_group" "application_logs" {
  name              = "/aws/${local.full_project_name}/application"
  retention_in_days = local.retention_days

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-app-logs"
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${local.full_project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-high-cpu"
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.full_project_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors Lambda function errors"

  dimensions = {
    FunctionName = aws_lambda_function.api_handler.function_name
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-lambda-errors"
  })
}

# =============================================================================
# Route53 (Testing DNS Resources)
# =============================================================================

# Hosted Zone
resource "aws_route53_zone" "main" {
  name = "${local.full_project_name}.example.com"

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-zone"
  })
}

# DNS Records
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.${aws_route53_zone.main.name}"
  type    = "CNAME"
  ttl     = 300

  records = ["api.example.com"]
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${aws_route53_zone.main.name}"
  type    = "A"

  alias {
    name                   = "d1234567890.cloudfront.net"
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}

# =============================================================================
# DYNAMIC/UNKNOWN SERVICES (Testing Dynamic Permission Generation)
# =============================================================================

# WAF Web ACL (Testing dynamic permissions)
resource "aws_wafv2_web_acl" "main" {
  name  = "${local.full_project_name}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 10000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-waf"
  })
}

# CloudFront Distribution (Testing dynamic permissions)
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static_assets.bucket}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static_assets.bucket}"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-cdn"
  })
}

resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "OAI for ${local.full_project_name}"
}

# EKS Cluster (Testing complex dynamic permissions)
resource "aws_eks_cluster" "main" {
  name     = "${local.full_project_name}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.27"

  vpc_config {
    subnet_ids = [aws_subnet.private.id, aws_subnet.public_1.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-cluster"
  })
}

resource "aws_iam_role" "eks_cluster" {
  name = "${local.full_project_name}-eks-cluster"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# DynamoDB Tables (Testing NoSQL resources)
resource "aws_dynamodb_table" "users" {
  name           = "${local.full_project_name}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-users"
  })
}

resource "aws_dynamodb_table" "sessions" {
  name           = "${local.full_project_name}-sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-sessions"
  })
}

# ElastiCache (Testing caching resources)
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.full_project_name}-cache-subnet"
  subnet_ids = [aws_subnet.private.id]

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-cache-subnet"
  })
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${local.full_project_name}-cache"
  description                = "Redis cluster for ${local.full_project_name}"

  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"

  num_cache_clusters         = 2

  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.database.id]

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-cache"
  })
}

# API Gateway (Testing API resources)
resource "aws_api_gateway_rest_api" "main" {
  name        = "${local.full_project_name}-api"
  description = "API Gateway for ${local.full_project_name}"

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-api"
  })
}

resource "aws_api_gateway_resource" "users" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "users"
}

resource "aws_api_gateway_method" "users_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.users.id
  http_method   = "GET"
  authorization = "NONE"
}

# Step Functions (Testing workflow resources)
resource "aws_sfn_state_machine" "data_processing" {
  name     = "${local.full_project_name}-data-processing"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Data processing workflow"
    StartAt = "ProcessData"
    States = {
      ProcessData = {
        Type     = "Task"
        Resource = aws_lambda_function.data_processor.arn
        End      = true
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.full_project_name}-data-processing"
  })
}

resource "aws_iam_role" "step_functions" {
  name = "${local.full_project_name}-step-functions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "step_functions_lambda" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSStepFunctionsExecutionRole"
  role       = aws_iam_role.step_functions.name
}

# =============================================================================
# Outputs
# =============================================================================

output "vpc_id" {
  description = "ID of the main VPC"
  value       = aws_vpc.main.id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  value = {
    api       = aws_lambda_function.api_handler.arn
    processor = aws_lambda_function.data_processor.arn
  }
}

output "s3_bucket_names" {
  description = "Names of S3 buckets"
  value = [
    for bucket in aws_s3_bucket.data_buckets : bucket.bucket
  ]
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.main.domain_name
}
