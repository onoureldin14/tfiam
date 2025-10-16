"""Tests for TerraformAnalyzer."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tfiam.core.analyzer import TerraformAnalyzer


class TestTerraformAnalyzer:
    """Test cases for TerraformAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TerraformAnalyzer()

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        assert self.analyzer.resources == []
        assert self.analyzer.aws_services == set()
        assert self.analyzer.variables == {}
        assert self.analyzer.locals == {}

    def test_extract_variables(self):
        """Test variable extraction from Terraform content."""
        content = """
        variable "project_name" {
          default = "my-project"
        }

        variable "environment" {
          default = "prod"
        }
        """

        self.analyzer.extract_variables_and_locals(content)

        assert "var.project_name" in self.analyzer.variables
        assert self.analyzer.variables["var.project_name"] == "my-project"
        assert "var.environment" in self.analyzer.variables
        assert self.analyzer.variables["var.environment"] == "prod"

    def test_extract_locals(self):
        """Test locals extraction from Terraform content."""
        content = """
        locals {
          name_prefix = "${var.project_name}-${var.environment}"
          common_tags = {
            Project = var.project_name
            Environment = var.environment
          }
        }
        """

        self.analyzer.extract_variables_and_locals(content)

        assert "local.name_prefix" in self.analyzer.locals
        assert "local.common_tags" in self.analyzer.locals

    def test_resolve_variable_reference(self):
        """Test variable reference resolution."""
        self.analyzer.variables["var.project_name"] = "my-project"
        self.analyzer.locals["local.name_prefix"] = "my-project-prod"

        # Test variable reference
        result = self.analyzer.resolve_variable_reference("${var.project_name}")
        assert result == "my-project"

        # Test local reference
        result = self.analyzer.resolve_variable_reference("${local.name_prefix}")
        assert result == "my-project-prod"

    def test_dynamic_permissions_generation(self):
        """Test dynamic permissions generation for unknown services."""
        actions = self.analyzer._generate_generic_permissions("newservice", "resource")

        expected_actions = [
            "newservice:CreateResource",
            "newservice:DeleteResource",
            "newservice:DescribeResource",
            "newservice:GetResource",
            "newservice:ListResource",
            "newservice:ListTagsForResource",
            "newservice:ModifyResource",
            "newservice:PutResource",
            "newservice:TagResource",
            "newservice:UntagResource",
            "newservice:UpdateResource",
            "newservice:Describe*",
            "newservice:Get*",
            "newservice:List*",
        ]

        assert all(action in actions for action in expected_actions)

    def test_service_mapping(self):
        """Test service mapping covers common services."""
        mapping = self.analyzer._get_service_mapping()

        # Test common mappings
        assert mapping["vpc"] == "ec2"
        assert mapping["s3"] == "s3"
        assert mapping["iam"] == "iam"
        assert mapping["lambda"] == "lambda"
        assert mapping["wafv2"] == "wafv2"
        assert mapping["eks"] == "eks"

    def test_scan_directory_with_temp_files(self):
        """Test scanning directory with temporary Terraform files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Terraform file
            test_tf_content = """
            resource "aws_s3_bucket" "test" {
              bucket = "my-test-bucket"
            }

            resource "aws_iam_role" "test" {
              name = "test-role"
            }
            """

            test_file = os.path.join(temp_dir, "test.tf")
            with open(test_file, "w") as f:
                f.write(test_tf_content)

            # Scan the directory
            self.analyzer.scan_directory(temp_dir)

            # Verify resources were found
            assert len(self.analyzer.resources) == 2
            assert len(self.analyzer.aws_services) == 2

            # Check specific resources
            bucket_resource = next(r for r in self.analyzer.resources if r.type == "aws_s3_bucket")
            assert bucket_resource.name == "test"
            assert bucket_resource.resource_name == "my-test-bucket"

            role_resource = next(r for r in self.analyzer.resources if r.type == "aws_iam_role")
            assert role_resource.name == "test"
            assert role_resource.resource_name == "test-role"


if __name__ == "__main__":
    pytest.main([__file__])
