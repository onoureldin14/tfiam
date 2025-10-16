"""Tests for utility modules."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tfiam.utils.arn_builder import ARNBuilder
from tfiam.utils.aws_permissions import AWS_PERMISSIONS


class TestARNBuilder:
    """Test cases for ARNBuilder."""

    def test_build_specific_arn_iam(self):
        """Test building specific IAM ARNs."""
        # Test IAM role ARN
        arn = ARNBuilder.build_specific_arn("iam", "role", "my-role")
        expected = "arn:aws:iam::${aws_account}:role/my-role"
        assert arn == expected

        # Test IAM policy ARN
        arn = ARNBuilder.build_specific_arn("iam", "policy", "my-policy")
        expected = "arn:aws:iam::${aws_account}:policy/my-policy"
        assert arn == expected

    def test_build_specific_arn_s3(self):
        """Test building specific S3 ARNs."""
        arn = ARNBuilder.build_specific_arn("s3", "bucket", "my-bucket")
        expected = "arn:aws:s3:::my-bucket"
        assert arn == expected

    def test_build_specific_arn_lambda(self):
        """Test building specific Lambda ARNs."""
        arn = ARNBuilder.build_specific_arn("lambda", "function", "my-function")
        expected = "arn:aws:lambda:${aws_region}:${aws_account}:function/my-function"
        assert arn == expected

    def test_build_specific_arn_unknown_service(self):
        """Test building ARNs for unknown services."""
        arn = ARNBuilder.build_specific_arn("unknownservice", "resource", "my-resource")
        expected = "arn:aws:unknownservice:${aws_region}:${aws_account}:resource/my-resource"
        assert arn == expected

    def test_get_resource_arn_ec2(self):
        """Test getting wildcard EC2 ARNs."""
        # Test EC2 instance ARN
        arn = ARNBuilder.get_resource_arn("ec2", "instance")
        expected = "arn:aws:ec2:${aws_region}:${aws_account}:instance/*"
        assert arn == expected

        # Test EC2 VPC ARN
        arn = ARNBuilder.get_resource_arn("ec2", "vpc")
        expected = "arn:aws:ec2:${aws_region}:${aws_account}:vpc/*"
        assert arn == expected

    def test_get_resource_arn_s3(self):
        """Test getting wildcard S3 ARNs."""
        arn = ARNBuilder.get_resource_arn("s3", "bucket")
        expected = "arn:aws:s3:::*"
        assert arn == expected

    def test_get_resource_arn_unknown_service(self):
        """Test getting ARNs for unknown services."""
        arn = ARNBuilder.get_resource_arn("unknownservice", "resource")
        expected = "arn:aws:unknownservice:${aws_region}:${aws_account}:*"
        assert arn == expected


class TestAWSPermissions:
    """Test cases for AWS_PERMISSIONS."""

    def test_aws_permissions_structure(self):
        """Test AWS_PERMISSIONS has expected structure."""
        assert isinstance(AWS_PERMISSIONS, dict)
        assert len(AWS_PERMISSIONS) > 0

        # Test that each service has resource types
        for service, resource_types in AWS_PERMISSIONS.items():
            assert isinstance(resource_types, dict)
            assert len(resource_types) > 0

            # Test that each resource type has permissions list
            for resource_type, permissions in resource_types.items():
                assert isinstance(permissions, list)
                assert len(permissions) > 0

                # Test that permissions are strings with service prefix
                for permission in permissions:
                    assert isinstance(permission, str)
                    assert permission.startswith(f"{service}:")

    def test_common_services_present(self):
        """Test that common AWS services are present."""
        common_services = ["ec2", "s3", "iam", "lambda", "rds", "logs", "cloudwatch", "route53"]

        for service in common_services:
            assert service in AWS_PERMISSIONS, f"Service {service} not found in permissions"

    def test_ec2_permissions(self):
        """Test EC2 permissions structure."""
        assert "ec2" in AWS_PERMISSIONS

        ec2_perms = AWS_PERMISSIONS["ec2"]
        assert "instance" in ec2_perms
        assert "vpc" in ec2_perms
        assert "security_group" in ec2_perms

        # Test instance permissions
        instance_perms = ec2_perms["instance"]
        assert "ec2:RunInstances" in instance_perms
        assert "ec2:TerminateInstances" in instance_perms
        assert "ec2:DescribeInstances" in instance_perms

    def test_s3_permissions(self):
        """Test S3 permissions structure."""
        assert "s3" in AWS_PERMISSIONS

        s3_perms = AWS_PERMISSIONS["s3"]
        assert "bucket" in s3_perms
        assert "object" in s3_perms

        # Test bucket permissions
        bucket_perms = s3_perms["bucket"]
        assert "s3:CreateBucket" in bucket_perms
        assert "s3:DeleteBucket" in bucket_perms
        assert "s3:ListBucket" in bucket_perms

    def test_iam_permissions(self):
        """Test IAM permissions structure."""
        assert "iam" in AWS_PERMISSIONS

        iam_perms = AWS_PERMISSIONS["iam"]
        assert "role" in iam_perms
        assert "policy" in iam_perms
        assert "user" in iam_perms

        # Test role permissions
        role_perms = iam_perms["role"]
        assert "iam:CreateRole" in role_perms
        assert "iam:DeleteRole" in role_perms
        assert "iam:GetRole" in role_perms

    def test_permissions_are_unique(self):
        """Test that permissions within each resource type are unique."""
        for service, resource_types in AWS_PERMISSIONS.items():
            for resource_type, permissions in resource_types.items():
                # Check for duplicates
                assert len(permissions) == len(
                    set(permissions)
                ), f"Duplicate permissions found in {service}.{resource_type}"


if __name__ == "__main__":
    pytest.main([__file__])
