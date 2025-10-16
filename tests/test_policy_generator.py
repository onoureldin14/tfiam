"""Tests for PolicyGenerator."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tfiam.core.models import IAMStatement
from tfiam.core.policy_generator import PolicyGenerator


class TestPolicyGenerator:
    """Test cases for PolicyGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_statements = [
            IAMStatement(
                sid="TestStatement1",
                effect="Allow",
                action=["s3:GetObject", "s3:PutObject"],
                resource=["arn:aws:s3:::test-bucket/*"],
                explanation="Test permissions for S3 bucket",
            ),
            IAMStatement(
                sid="TestStatement2",
                effect="Allow",
                action=["ec2:DescribeInstances"],
                resource=["arn:aws:ec2:*:*:instance/*"],
                explanation="Test permissions for EC2 instances",
            ),
        ]

        self.sample_metadata = {
            "terraform_directory": "/test/dir",
            "services_count": 2,
            "services": ["s3", "ec2"],
            "resources_count": 3,
            "statements_count": 2,
            "permissions_count": 3,
        }

    def test_save_policy_clean(self):
        """Test saving clean JSON policy."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Save policy
            size = PolicyGenerator.save_policy_clean(
                self.sample_statements, self.sample_metadata, temp_filename
            )

            # Verify file was created and has content
            assert size > 0
            assert os.path.exists(temp_filename)

            # Verify JSON structure
            with open(temp_filename, "r") as f:
                policy = json.load(f)

            assert "Version" in policy
            assert policy["Version"] == "2012-10-17"
            assert "Statement" in policy
            assert len(policy["Statement"]) == 2

            # Verify statement structure
            statement1 = policy["Statement"][0]
            assert statement1["Sid"] == "TestStatement1"
            assert statement1["Effect"] == "Allow"
            assert statement1["Action"] == ["s3:GetObject", "s3:PutObject"]
            assert statement1["Resource"] == ["arn:aws:s3:::test-bucket/*"]

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_save_markdown_report(self):
        """Test saving markdown report."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Save report
            size = PolicyGenerator.save_markdown_report(
                self.sample_statements, self.sample_metadata, temp_filename
            )

            # Verify file was created and has content
            assert size > 0
            assert os.path.exists(temp_filename)

            # Verify markdown content
            with open(temp_filename, "r") as f:
                content = f.read()

            assert "# TFIAM Analysis Report" in content
            assert "**Generated:**" in content
            assert "**Terraform Directory:** /test/dir" in content
            assert "**Services Analyzed:** 2" in content
            assert "**Total Statements:** 2" in content
            assert "**Total Permissions:** 3" in content
            assert "## Summary" in content
            assert "## IAM Policy Statements" in content
            assert "### Statement 1: TestStatement1" in content
            assert "### Statement 2: TestStatement2" in content
            assert "## Security Notes" in content

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_empty_statements(self):
        """Test handling of empty statements list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Save empty policy
            size = PolicyGenerator.save_policy_clean([], {}, temp_filename)

            # Verify file was created
            assert size > 0
            assert os.path.exists(temp_filename)

            # Verify JSON structure
            with open(temp_filename, "r") as f:
                policy = json.load(f)

            assert "Version" in policy
            assert policy["Version"] == "2012-10-17"
            assert "Statement" in policy
            assert policy["Statement"] == []

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)


if __name__ == "__main__":
    pytest.main([__file__])
