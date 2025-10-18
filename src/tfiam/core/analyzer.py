"""Terraform analyzer for extracting AWS resources and generating IAM permissions."""

import os
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Union

from ..utils.arn_builder import ARNBuilder
from ..utils.aws_permissions import AWS_PERMISSIONS
from .models import IAMStatement, TerraformResource


class TerraformAnalyzer:
    """Analyzes Terraform files and generates IAM permissions."""

    def __init__(self):
        self.resources: List[TerraformResource] = []
        self.aws_services: Set[str] = set()
        self.variables: Dict[str, str] = {}
        self.locals: Dict[str, str] = {}
        self.terraform_locals: Dict[str, str] = {}
        self.service_permissions = AWS_PERMISSIONS

    def scan_directory(self, directory: str) -> None:
        """Scan directory for Terraform files (only in the specified directory, not subdirectories)."""
        tf_files = []

        # Only scan the specified directory, not subdirectories
        try:
            files = os.listdir(directory)
            for file in files:
                if file.endswith(".tf"):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        tf_files.append(file_path)
        except OSError as e:
            print(f"Error accessing directory {directory}: {e}")
            return

        for tf_file in tf_files:
            self.parse_terraform_file(tf_file)

        # Resolve for_each resources after all files are parsed
        self.resources = self.resolve_for_each_resources(self.resources)

    def parse_terraform_file(self, file_path: str) -> None:
        """Parse a single Terraform file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract variables and locals first
            self.extract_variables_and_locals(content)

            # Extract resources
            self.extract_resources(content, file_path)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

    def extract_variables_and_locals(self, content: str) -> None:
        """Extract variables, locals, and data sources from Terraform content."""
        # Extract variables
        variable_pattern = r'variable\s+["\']([^"\']+)["\']\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        for match in re.finditer(variable_pattern, content, re.MULTILINE | re.DOTALL):
            var_name = match.group(1)
            var_content = match.group(2)

            # Extract default value if present
            default_match = re.search(r"default\s*=\s*([^\n]+)", var_content)
            if default_match:
                default_value = default_match.group(1).strip().strip("\"'")
                self.variables[f"var.{var_name}"] = default_value

        # Extract locals - improved parsing with better brace matching
        locals_pattern = r"locals\s*\{(.*?)\n\}"
        for match in re.finditer(locals_pattern, content, re.MULTILINE | re.DOTALL):
            locals_content = match.group(1)

            # Parse each local definition more carefully
            lines = locals_content.split("\n")
            current_local = None
            current_value = []
            brace_count = 0

            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                # Count braces to handle nested structures
                brace_count += stripped.count("{") - stripped.count("}")

                # Check for new local definition (at brace level 0)
                if brace_count == 0 and "=" in stripped:
                    # Save previous local if exists
                    if current_local and current_value:
                        full_value = "\n".join(current_value).strip().strip("\"'")
                        if full_value.endswith(","):
                            full_value = full_value[:-1]
                        self.locals[f"local.{current_local}"] = full_value

                    # Parse new local
                    eq_pos = stripped.find("=")
                    if eq_pos > 0:
                        current_local = stripped[:eq_pos].strip()
                        value_part = stripped[eq_pos + 1 :].strip()
                        current_value = [value_part]
                        brace_count += value_part.count("{") - value_part.count("}")
                else:
                    # Continue current local value
                    if current_local:
                        current_value.append(stripped)

            # Save last local
            if current_local and current_value:
                full_value = "\n".join(current_value).strip().strip("\"'")
                if full_value.endswith(","):
                    full_value = full_value[:-1]
                self.locals[f"local.{current_local}"] = full_value

    def resolve_variable_reference(self, value: str) -> str:
        """Resolve variable and local references with better interpolation support."""
        if not isinstance(value, str):
            return str(value)

        result = value

        # Handle complex string interpolation with multiple variables/locals
        # Pattern: ${var.name} or ${local.name} or ${var.name}-${local.other}
        interpolation_pattern = r"\$\{([^}]+)\}"

        def replace_interpolation(match):
            expression = match.group(1)

            # Handle random_id patterns (e.g., ${random_id.suffix.hex})
            if expression.startswith("random_id."):
                return "*"  # Replace with wildcard

            # Handle for_each patterns (e.g., ${each.value})
            if expression.startswith("each."):
                return "*"  # Replace with wildcard

            # Handle variable references
            if expression.startswith("var."):
                var_name = expression
                if var_name in self.variables:
                    return self.variables[var_name]

            # Handle local references
            elif expression.startswith("local."):
                local_name = expression
                if local_name in self.locals:
                    return self.resolve_variable_reference(self.locals[local_name])

            # Handle resource references (like aws_vpc.main.id)
            elif "." in expression:
                parts = expression.split(".")
                if len(parts) >= 2:
                    resource_type = parts[0]
                    resource_name = parts[1]
                    # Try to find a matching resource and return a placeholder
                    for res in self.resources:
                        if res.type == f"aws_{resource_type}" and res.name == resource_name:
                            return f"${{{expression}}}"  # Keep as placeholder for now

            # Return original if we can't resolve
            return match.group(0)

        # Apply interpolation replacement
        result = re.sub(interpolation_pattern, replace_interpolation, result)

        # Handle simple variable references (without ${})
        var_pattern = r"var\.([a-zA-Z_][a-zA-Z0-9_]*)"
        for var_match in re.finditer(var_pattern, result):
            var_name = f"var.{var_match.group(1)}"
            if var_name in self.variables:
                result = result.replace(var_match.group(0), self.variables[var_name])

        # Handle simple local references (without ${})
        local_pattern = r"local\.([a-zA-Z_][a-zA-Z0-9_]*)"
        for local_match in re.finditer(local_pattern, result):
            local_name = f"local.{local_match.group(1)}"
            if local_name in self.locals:
                resolved = self.resolve_variable_reference(self.locals[local_name])
                result = result.replace(local_match.group(0), resolved)

        # Handle data source references
        data_pattern = r"\$\{data\.([^}]+)\}"
        for data_match in re.finditer(data_pattern, result):
            # For now, just replace with a placeholder
            result = result.replace(data_match.group(0), f"{data_match.group(1)}-*")

        return result

    def expand_for_each_values(self, value: str) -> List[str]:
        """Expand for_each values to show all possible values instead of ${each.value}."""
        if "${each.value}" not in value:
            return [value]

        # For now, we'll return a placeholder that indicates this is a for_each resource
        # In a more advanced implementation, we could parse the for_each expression
        # and expand it based on the actual values
        return [value.replace("${each.value}", "*")]

    def resolve_for_each_resources(
        self, resources: List[TerraformResource]
    ) -> List[TerraformResource]:
        """Handle for_each resources by filtering them out since we can't resolve the actual values."""
        expanded_resources = []

        for resource in resources:
            if resource.resource_name and "${each.value}" in resource.resource_name:
                # Skip for_each resources since we can't resolve the actual values
                # This prevents generating wildcard ARNs that are too broad
                continue
            else:
                expanded_resources.append(resource)

        return expanded_resources

    def extract_resources(self, content: str, file_path: str) -> None:
        """Extract AWS resources from Terraform content."""
        # Find resource blocks manually to handle nested braces properly
        resource_pattern = r'resource\s+["\']([^"\']+)["\']\s+["\']([^"\']+)["\']\s*\{'

        for match in re.finditer(resource_pattern, content, re.MULTILINE):
            resource_type = match.group(1)
            resource_name = match.group(2)

            # Find the matching closing brace
            start_pos = match.end()
            brace_count = 1
            pos = start_pos

            while pos < len(content) and brace_count > 0:
                if content[pos] == "{":
                    brace_count += 1
                elif content[pos] == "}":
                    brace_count -= 1
                pos += 1

            if brace_count == 0:
                resource_content = content[start_pos : pos - 1]
            else:
                # Malformed resource block, skip
                continue

            if resource_type.startswith("aws_"):
                # Extract resource properties
                properties = self._extract_resource_properties(resource_content)

                # Extract specific resource name
                actual_name = self._extract_resource_name(resource_type, resource_name, properties)

                resource = TerraformResource(
                    type=resource_type,
                    name=resource_name,
                    resource_name=actual_name,
                    file_path=file_path,
                    properties=properties,
                )

                self.resources.append(resource)

                # Track AWS services
                service = (
                    resource_type.split("_")[1]
                    if len(resource_type.split("_")) > 1
                    else resource_type
                )
                self.aws_services.add(service)

    def _extract_resource_properties(self, content: str) -> Dict[str, str]:
        """Extract key-value pairs from resource content with better parsing."""
        properties = {}

        # More sophisticated parsing that handles complex Terraform syntax
        lines = content.split("\n")
        current_key = None
        current_value = []
        brace_count = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle multi-line values and nested structures
            if brace_count > 0:
                current_value.append(line)
                brace_count += line.count("{") - line.count("}")
                if brace_count == 0:
                    # End of nested structure
                    if current_key:
                        value_str = "\n".join(current_value).strip()
                        properties[current_key] = value_str
                        current_key = None
                        current_value = []
                continue

            # Handle key-value pairs
            if "=" in line:
                # Find the first = that's not inside quotes
                eq_pos = -1
                in_quotes = False
                quote_char = None

                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i - 1] != "\\"):
                        if not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char:
                            in_quotes = False
                            quote_char = None
                    elif char == "=" and not in_quotes:
                        eq_pos = i
                        break

                if eq_pos > 0:
                    key = line[:eq_pos].strip()
                    value = line[eq_pos + 1 :].strip()

                    # Handle trailing comma
                    if value.endswith(","):
                        value = value[:-1]

                    # Check if value starts a nested structure or contains interpolation
                    if value.endswith("{") or (
                        "${" in value and value.count("${") > value.count("}")
                    ):
                        current_key = key
                        current_value = [value]
                        brace_count = value.count("{") - value.count("}")
                    else:
                        # Simple value - handle interpolation properly
                        value = value.strip("\"'")
                        properties[key] = value

        return properties

    def _extract_resource_name(
        self, resource_type: str, terraform_name: str, properties: Dict[str, str]
    ) -> Optional[str]:
        """Extract the actual resource name from properties or use Terraform name."""
        # Common name properties for different resource types
        name_properties = {
            "aws_s3_bucket": "bucket",
            "aws_iam_role": "name",
            "aws_iam_policy": "name",
            "aws_iam_user": "name",
            "aws_lambda_function": "function_name",
            "aws_rds_instance": "identifier",
            "aws_rds_subnet_group": "name",
            "aws_cloudwatch_log_group": "name",
            "aws_cloudwatch_metric_alarm": "alarm_name",
            "aws_vpc": "name",  # VPC doesn't have a name property, but let's check
            "aws_subnet": "name",  # Subnet doesn't have a name property, but let's check
            "aws_security_group": "name",  # Security group doesn't have a name property, but let's check
            "aws_internet_gateway": "name",  # IGW doesn't have a name property, but let's check
            "aws_route53_zone": "name",
            "aws_route53_record": "name",
            "aws_cloudfront_distribution": "name",  # CloudFront doesn't have a name property
            "aws_wafv2_web_acl": "name",
            "aws_eks_cluster": "name",
            "aws_dynamodb_table": "name",
            "aws_elasticache_replication_group": "name",  # Actually "replication_group_id"
            "aws_api_gateway_rest_api": "name",
            "aws_api_gateway_resource": "name",  # Actually "path_part"
            "aws_api_gateway_method": "name",  # Actually "http_method"
            "aws_sfn_state_machine": "name",
        }

        name_prop = name_properties.get(resource_type, "name")

        if name_prop in properties:
            raw_value = properties[name_prop]
            resolved_value = self.resolve_variable_reference(raw_value)

            # Return resolved value if it's not a variable reference
            if resolved_value and not resolved_value.startswith("${"):
                return resolved_value

        # For resources without explicit names, try to construct a meaningful name
        # using variables and locals if available
        if resource_type in ["aws_vpc", "aws_subnet", "aws_security_group", "aws_internet_gateway"]:
            # These resources don't have name properties, so we'll use tags or construct from context
            return None  # Let ARN builder handle with wildcards

        return terraform_name

    def _get_s3_permission_groups(self, resource: TerraformResource) -> List[Dict]:
        """Analyze S3 resource and return granular permission groups based on features used."""
        s3_groups = []

        # Always include bucket permissions for S3 bucket resources
        if resource.type == "aws_s3_bucket":
            bucket_permissions = self._get_s3_bucket_permissions(resource)
            if bucket_permissions:
                s3_groups.append({"type": "bucket", "actions": bucket_permissions})

        # For S3 bucket-related resources (versioning, encryption, etc.),
        # don't create separate statements but let them contribute to main bucket permissions
        if resource.type in [
            "aws_s3_bucket_versioning",
            "aws_s3_bucket_server_side_encryption_configuration",
            "aws_s3_bucket_policy",
            "aws_s3_bucket_cors_configuration",
            "aws_s3_bucket_website_configuration",
            "aws_s3_bucket_acl",
            "aws_s3_bucket_lifecycle_configuration",
            "aws_s3_bucket_logging",
            "aws_s3_bucket_notification",
            "aws_s3_bucket_public_access_block",
            "aws_s3_bucket_object_lock_configuration",
            "aws_s3_bucket_replication_configuration",
        ]:
            # These resources don't need separate statements
            # They're configuration resources that work with the main bucket
            return s3_groups

        # Check for object-related features (only for main S3 bucket)
        if resource.type == "aws_s3_bucket":
            object_permissions = self._get_s3_object_permissions(resource)
            if object_permissions:
                s3_groups.append({"type": "object", "actions": object_permissions})

        return s3_groups

    def _get_related_s3_resources(
        self, bucket_resource: TerraformResource
    ) -> List[TerraformResource]:
        """Get S3 resources that are related to the main bucket (versioning, encryption, etc.)."""
        related_resources = []

        # Look for resources that reference this bucket
        bucket_name = bucket_resource.name
        bucket_reference = f"aws_s3_bucket.{bucket_name}"

        for resource in self.resources:
            if resource == bucket_resource:
                continue

            # Check if this resource references the bucket
            if hasattr(resource, "properties") and resource.properties:
                bucket_ref = resource.properties.get("bucket", "")
                if bucket_ref == f"{bucket_reference}.id" or bucket_ref == bucket_reference:
                    related_resources.append(resource)

        return related_resources

    def _get_s3_bucket_permissions(self, resource: TerraformResource) -> List[str]:
        """Get S3 bucket permissions based on features used."""
        bucket_permissions = []

        # Base bucket permissions
        base_permissions = [
            "s3:CreateBucket",
            "s3:DeleteBucket",
            "s3:ListBucket",
            "s3:GetBucketLocation",
        ]
        bucket_permissions.extend(base_permissions)

        # Analyze resource properties to determine additional permissions needed
        properties = resource.properties or {}

        # Also check for related S3 resources that might need additional permissions
        related_s3_resources = self._get_related_s3_resources(resource)
        for related_resource in related_s3_resources:
            if related_resource.properties:
                properties.update(related_resource.properties)

        # Versioning permissions
        if self._has_versioning_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketVersioning", "s3:PutBucketVersioning", "s3:ListBucketVersions"]
            )

        # Policy permissions
        if self._has_policy_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketPolicy", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy"]
            )

        # CORS permissions
        if self._has_cors_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketCors", "s3:PutBucketCors", "s3:DeleteBucketCors"]
            )

        # Website permissions
        if self._has_website_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketWebsite", "s3:PutBucketWebsite", "s3:DeleteBucketWebsite"]
            )

        # ACL permissions
        if self._has_acl_features(properties):
            bucket_permissions.extend(["s3:GetBucketAcl", "s3:PutBucketAcl"])

        # Encryption permissions
        if self._has_encryption_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketEncryption", "s3:PutBucketEncryption", "s3:DeleteBucketEncryption"]
            )

        # Lifecycle permissions
        if self._has_lifecycle_features(properties):
            bucket_permissions.extend(
                [
                    "s3:GetBucketLifecycleConfiguration",
                    "s3:PutBucketLifecycleConfiguration",
                    "s3:DeleteBucketLifecycleConfiguration",
                ]
            )

        # Logging permissions
        if self._has_logging_features(properties):
            bucket_permissions.extend(["s3:GetBucketLogging", "s3:PutBucketLogging"])

        # Tagging permissions
        if self._has_tagging_features(properties):
            bucket_permissions.extend(["s3:GetBucketTagging", "s3:PutBucketTagging"])

        # Public access block permissions
        if self._has_public_access_features(properties):
            bucket_permissions.extend(
                ["s3:GetBucketPublicAccessBlock", "s3:PutBucketPublicAccessBlock"]
            )

        # Object lock permissions
        if self._has_object_lock_features(properties):
            bucket_permissions.extend(["s3:GetBucketObjectLockConfiguration"])

        # Replication permissions
        if self._has_replication_features(properties):
            bucket_permissions.extend(
                ["s3:GetReplicationConfiguration", "s3:PutReplicationConfiguration"]
            )

        # Multipart upload permissions
        bucket_permissions.extend(
            [
                "s3:ListBucketMultipartUploads",
                "s3:ListMultipartUploadParts",
                "s3:AbortMultipartUpload",
            ]
        )

        return list(set(bucket_permissions))  # Remove duplicates

    def _get_s3_object_permissions(self, resource: TerraformResource) -> List[str]:
        """Get S3 object permissions based on features used."""
        object_permissions = []

        # Base object permissions
        base_permissions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        object_permissions.extend(base_permissions)

        # Analyze resource properties
        properties = resource.properties or {}

        # Versioning-related object permissions
        if self._has_versioning_features(properties):
            object_permissions.extend(
                ["s3:GetObjectVersion", "s3:DeleteObjectVersion", "s3:ListObjectVersions"]
            )

        # ACL permissions for objects
        if self._has_acl_features(properties):
            object_permissions.extend(
                [
                    "s3:GetObjectAcl",
                    "s3:PutObjectAcl",
                    "s3:GetObjectVersionAcl",
                    "s3:PutObjectVersionAcl",
                ]
            )

        # Object tagging
        if self._has_tagging_features(properties):
            object_permissions.extend(["s3:GetObjectTagging", "s3:PutObjectTagging"])

        # Object attributes and metadata
        object_permissions.extend(["s3:GetObjectAttributes", "s3:HeadObject"])

        return list(set(object_permissions))  # Remove duplicates

    def _get_s3_resource_arn(
        self, resource: TerraformResource, s3_type: str
    ) -> Union[str, List[str]]:
        """Get S3 resource ARN based on the S3 type (bucket or object)."""
        if s3_type == "bucket":
            # For bucket permissions, return both bucket and bucket/* ARNs
            if resource.resource_name and resource.resource_name != resource.name:
                bucket_name = resource.resource_name
                return [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
            else:
                # Fallback to wildcard
                return ["arn:aws:s3:::*", "arn:aws:s3:::/*"]

        elif s3_type == "object":
            # For object permissions, return bucket/* ARNs
            if resource.resource_name and resource.resource_name != resource.name:
                bucket_name = resource.resource_name
                return [f"arn:aws:s3:::{bucket_name}/*"]
            else:
                # Fallback to wildcard
                return ["arn:aws:s3:::/*"]

        # Default fallback
        return "arn:aws:s3:::/*"

    def _get_s3_wildcard_arn(
        self, s3_type: str, bucket_prefix: str = None
    ) -> Union[str, List[str]]:
        """Get S3 wildcard ARN based on the S3 type and bucket prefix."""
        if bucket_prefix and not bucket_prefix.startswith("${"):
            # Use specific bucket prefix with wildcard
            if s3_type == "bucket":
                return [f"arn:aws:s3:::{bucket_prefix}", f"arn:aws:s3:::{bucket_prefix}/*"]
            elif s3_type == "object":
                return [f"arn:aws:s3:::{bucket_prefix}/*"]

        # Fallback to global wildcards only if no specific prefix available
        if s3_type == "bucket":
            return "arn:aws:s3:::*"
        elif s3_type == "object":
            return "arn:aws:s3:::/*"
        else:
            return "arn:aws:s3:::*"

    def _has_versioning_features(self, properties: Dict) -> bool:
        """Check if resource has versioning-related features."""
        versioning_indicators = [
            "versioning",
            "versioning_configuration",
            "versioning_enabled",
            "versioning_mfa_delete",
            "versioning_status",
        ]
        # Check for versioning resource type or versioning-related properties
        if "versioning" in str(properties).lower():
            return True
        # Check for status field which indicates versioning configuration
        if "status" in properties and properties["status"] in ["Enabled", "Suspended"]:
            return True
        return False

    def _has_policy_features(self, properties: Dict) -> bool:
        """Check if resource has policy-related features."""
        policy_indicators = ["policy", "bucket_policy"]
        return any(key in str(properties).lower() for key in policy_indicators)

    def _has_cors_features(self, properties: Dict) -> bool:
        """Check if resource has CORS-related features."""
        cors_indicators = ["cors_rule", "cors_configuration"]
        if any(key in str(properties).lower() for key in cors_indicators):
            return True
        # Check for CORS-related properties
        cors_properties = [
            "allowed_headers",
            "allowed_methods",
            "allowed_origins",
            "max_age_seconds",
        ]
        return any(key in properties for key in cors_properties)

    def _has_website_features(self, properties: Dict) -> bool:
        """Check if resource has website-related features."""
        website_indicators = ["website", "website_configuration", "website_endpoint"]
        return any(key in str(properties).lower() for key in website_indicators)

    def _has_acl_features(self, properties: Dict) -> bool:
        """Check if resource has ACL-related features."""
        acl_indicators = ["acl", "access_control_list"]
        return any(key in str(properties).lower() for key in acl_indicators)

    def _has_encryption_features(self, properties: Dict) -> bool:
        """Check if resource has encryption-related features."""
        encryption_indicators = ["encryption", "server_side_encryption", "sse"]
        return any(key in str(properties).lower() for key in encryption_indicators)

    def _has_lifecycle_features(self, properties: Dict) -> bool:
        """Check if resource has lifecycle-related features."""
        lifecycle_indicators = ["lifecycle", "lifecycle_rule", "lifecycle_configuration"]
        if any(key in str(properties).lower() for key in lifecycle_indicators):
            return True
        # Check for lifecycle-related properties
        lifecycle_properties = [
            "noncurrent_days",
            "noncurrent_version_expiration",
            "transition",
            "expiration",
        ]
        return any(key in properties for key in lifecycle_properties)

    def _has_logging_features(self, properties: Dict) -> bool:
        """Check if resource has logging-related features."""
        logging_indicators = ["logging", "access_logging", "log_bucket"]
        return any(key in str(properties).lower() for key in logging_indicators)

    def _has_tagging_features(self, properties: Dict) -> bool:
        """Check if resource has tagging-related features."""
        return "tags" in properties

    def _has_public_access_features(self, properties: Dict) -> bool:
        """Check if resource has public access block features."""
        public_access_indicators = ["public_access_block", "block_public_acls"]
        return any(key in str(properties).lower() for key in public_access_indicators)

    def _has_object_lock_features(self, properties: Dict) -> bool:
        """Check if resource has object lock features."""
        object_lock_indicators = ["object_lock", "object_lock_configuration"]
        return any(key in str(properties).lower() for key in object_lock_indicators)

    def _has_replication_features(self, properties: Dict) -> bool:
        """Check if resource has replication features."""
        replication_indicators = ["replication", "replication_configuration"]
        return any(key in str(properties).lower() for key in replication_indicators)

    def generate_permissions(self) -> List[IAMStatement]:
        """Generate IAM permissions based on discovered AWS services and resources."""
        statements = []

        # Map discovered services to actual AWS service permissions
        service_mapping = self._get_service_mapping()

        # Group resources by service and permissions
        permission_groups: Dict[str, Dict] = {}

        for resource in self.resources:
            parts = resource.type.split("_")
            if len(parts) >= 2:
                service = parts[1]
                aws_service = service_mapping.get(service, service)
                resource_type = parts[-1] if len(parts) > 2 else parts[1]

                # Special handling for S3 resources - create granular permissions
                if aws_service == "s3":
                    s3_permission_groups = self._get_s3_permission_groups(resource)
                    for s3_group in s3_permission_groups:
                        service_key = f"s3_{s3_group['type']}"
                        actions_key = tuple(sorted(s3_group["actions"]))

                        if service_key not in permission_groups:
                            permission_groups[service_key] = {}

                        if actions_key not in permission_groups[service_key]:
                            permission_groups[service_key][actions_key] = {
                                "resources": [],
                                "resource_types": set(),
                                "service": "s3",
                                "actions": s3_group["actions"],
                                "s3_type": s3_group["type"],
                            }

                        permission_groups[service_key][actions_key]["resources"].append(resource)
                        permission_groups[service_key][actions_key]["resource_types"].add(
                            s3_group["type"]
                        )
                else:
                    # Standard handling for non-S3 resources
                    actions = self._get_dynamic_permissions(aws_service, resource_type)

                    # Create a key based on service and permissions (not resource type)
                    service_key = aws_service
                    actions_key = tuple(sorted(actions))  # Use sorted tuple as key for consistency

                    if service_key not in permission_groups:
                        permission_groups[service_key] = {}

                    if actions_key not in permission_groups[service_key]:
                        permission_groups[service_key][actions_key] = {
                            "resources": [],
                            "resource_types": set(),
                            "service": aws_service,
                            "actions": actions,
                        }

                    permission_groups[service_key][actions_key]["resources"].append(resource)
                    permission_groups[service_key][actions_key]["resource_types"].add(resource_type)

        # Generate statements for each permission group
        for service_key, action_groups in permission_groups.items():
            for actions_key, group_info in action_groups.items():
                resources = group_info["resources"]
                resource_types = list(group_info["resource_types"])
                aws_service = group_info["service"]
                actions = group_info["actions"]

                # Create a descriptive SID
                if aws_service == "s3" and "s3_type" in group_info:
                    # Special S3 granular SID
                    s3_type = group_info["s3_type"]
                    sid = f"S3{s3_type.title()}"
                elif len(resource_types) == 1:
                    sid = f"{aws_service.title()}{resource_types[0].title()}"
                else:
                    # Group multiple resource types under the service
                    sid = f"{aws_service.title()}Resources"

                # Generate resource ARNs - either specific or wildcard
                specific_arns = []
                for resource in resources:
                    # Special handling for S3 granular permissions
                    if aws_service == "s3" and "s3_type" in group_info:
                        s3_type = group_info["s3_type"]
                        resource_arn = self._get_s3_resource_arn(resource, s3_type)
                    else:
                        resource_arn = self._get_resource_arn_for_resource(aws_service, resource)

                    # Handle both single ARN and list of ARNs
                    if isinstance(resource_arn, list):
                        for arn in resource_arn:
                            if arn and arn not in specific_arns:
                                specific_arns.append(arn)
                    elif resource_arn and resource_arn not in specific_arns:
                        specific_arns.append(resource_arn)

                # Use specific ARNs if available, otherwise use wildcard
                if specific_arns:
                    # Use list of specific ARNs for multiple resources
                    final_resource = specific_arns
                else:
                    # Use the most specific wildcard possible
                    if aws_service == "s3" and "s3_type" in group_info:
                        s3_type = group_info["s3_type"]
                        # Try to extract bucket prefix from resource names
                        bucket_prefix = None
                        for resource in resources:
                            if hasattr(resource, "resource_name") and resource.resource_name:
                                # Extract prefix from resolved resource name (e.g., "tf-platform-playground-*")
                                if "*" in resource.resource_name:
                                    bucket_prefix = resource.resource_name
                                    break
                                # Or extract from bucket property if available
                                elif hasattr(resource, "properties") and resource.properties:
                                    bucket_value = resource.properties.get("bucket", "")
                                    if bucket_value and not bucket_value.startswith("${"):
                                        bucket_prefix = bucket_value
                                        break

                        wildcard_arn = self._get_s3_wildcard_arn(s3_type, bucket_prefix)
                        if isinstance(wildcard_arn, list):
                            final_resource = wildcard_arn
                        else:
                            final_resource = [wildcard_arn]
                    elif len(resource_types) == 1:
                        final_resource = [
                            ARNBuilder.get_resource_arn(aws_service, resource_types[0])
                        ]
                    else:
                        final_resource = [
                            f"arn:aws:{aws_service}:${{aws_region}}:${{aws_account}}:*"
                        ]

                # Create statement with combined resources
                statement = IAMStatement(
                    sid=sid,
                    effect="Allow",
                    action=list(actions),
                    resource=final_resource,
                    explanation=f"Permissions for {aws_service} {', '.join(sorted(resource_types))} management",
                )
                statements.append(statement)

        return statements

    def _get_service_mapping(self) -> Dict[str, str]:
        """Get comprehensive service mapping."""
        return {
            # EC2 and related
            "vpc": "ec2",
            "subnet": "ec2",
            "instance": "ec2",
            "security": "ec2",
            "internet": "ec2",
            "network": "ec2",
            "volume": "ec2",
            "launch": "ec2",
            "transit": "ec2",
            "nat": "ec2",
            "route": "ec2",
            "client": "ec2",
            "elastic": "ec2",
            "dhcp": "ec2",
            "egress": "ec2",
            "image": "ec2",
            "prefix": "ec2",
            "account": "ec2",
            # Other services
            "db": "rds",
            "rds": "rds",
            "cloudwatch": "cloudwatch",
            "logs": "logs",
            "log": "logs",
            "lambda": "lambda",
            "route53": "route53",
            "iam": "iam",
            "s3": "s3",
            "waf": "wafv2",
            "wafv2": "wafv2",
            "cloudfront": "cloudfront",
            "eks": "eks",
            "dynamodb": "dynamodb",
            "dynamo": "dynamodb",
            "elasticache": "elasticache",
            "redis": "elasticache",
            "api": "apigateway",
            "apigateway": "apigateway",
            "states": "states",
            "sfn": "states",
            "step": "states",
            "ecr": "ecr",
            "ecs": "ecs",
            "lb": "elasticloadbalancing",
            "load": "elasticloadbalancing",
            "target": "elasticloadbalancing",
            "listener": "elasticloadbalancing",
            "events": "events",
            "event": "events",
            "firehose": "firehose",
            "fis": "fis",
            "guardduty": "guardduty",
            "kms": "kms",
            "organizations": "organizations",
            "org": "organizations",
            "secrets": "secretsmanager",
            "secret": "secretsmanager",
            "securityhub": "securityhub",
            "security_hub": "securityhub",
            "servicediscovery": "servicediscovery",
            "service_discovery": "servicediscovery",
            "signer": "signer",
            "sns": "sns",
            "sqs": "sqs",
            "ssm": "ssm",
            "parameter": "ssm",
            "sts": "sts",
            "transfer": "transfer",
            "acm": "acm",
            "certificate": "acm",
            "airflow": "airflow",
            "mwaa": "airflow",
            "application_autoscaling": "application-autoscaling",
            "app_autoscaling": "application-autoscaling",
            "autoscaling": "autoscaling",
            "asg": "autoscaling",
            "backup": "backup",
            "chatbot": "chatbot",
            "cloudformation": "cloudformation",
            "cfn": "cloudformation",
            "cloudtrail": "cloudtrail",
            "trail": "cloudtrail",
            "cognito": "cognito-idp",
            "user_pool": "cognito-idp",
        }

    def _get_dynamic_permissions(self, aws_service: str, resource_type: str) -> tuple:
        """Get permissions dynamically, with fallback for unknown services."""
        # First, try to get from predefined mappings
        if (
            aws_service in self.service_permissions
            and resource_type in self.service_permissions[aws_service]
        ):
            return tuple(sorted(self.service_permissions[aws_service][resource_type]))

        # If service exists but resource type doesn't, use service-wide permissions
        if aws_service in self.service_permissions:
            # Get all permissions for this service and return the most common ones
            all_permissions = []
            for rt_permissions in self.service_permissions[aws_service].values():
                all_permissions.extend(rt_permissions)

            # Return common permissions (appearing in multiple resource types)
            perm_counts = Counter(all_permissions)
            common_permissions = [perm for perm, count in perm_counts.items() if count > 1]

            if common_permissions:
                return tuple(sorted(common_permissions))

        # Generate generic permissions for unknown services
        return self._generate_generic_permissions(aws_service, resource_type)

    def _generate_generic_permissions(self, aws_service: str, resource_type: str) -> tuple:
        """Generate generic permissions for unknown AWS services."""
        service_prefix = aws_service.lower()

        # Common permission patterns across AWS services
        generic_permissions = [
            f"{service_prefix}:Create{resource_type.title()}",
            f"{service_prefix}:Delete{resource_type.title()}",
            f"{service_prefix}:Describe{resource_type.title()}",
            f"{service_prefix}:List{resource_type.title()}",
            f"{service_prefix}:Get{resource_type.title()}",
            f"{service_prefix}:Update{resource_type.title()}",
            f"{service_prefix}:Modify{resource_type.title()}",
            f"{service_prefix}:Put{resource_type.title()}",
            f"{service_prefix}:Tag{resource_type.title()}",
            f"{service_prefix}:Untag{resource_type.title()}",
            f"{service_prefix}:ListTagsFor{resource_type.title()}",
        ]

        # Add service-wide permissions
        service_permissions = [
            f"{service_prefix}:Describe*",
            f"{service_prefix}:List*",
            f"{service_prefix}:Get*",
        ]

        # Combine and return
        all_permissions = generic_permissions + service_permissions
        return tuple(sorted(all_permissions))

    def _get_resource_arn_for_resource(
        self, service: str, resource: TerraformResource
    ) -> Union[str, List[str]]:
        """Get resource ARN for a specific resource. Returns list for S3 buckets."""
        # Check if we have a specific resource name
        if resource.resource_name and resource.resource_name != resource.name:
            specific_arn = ARNBuilder.build_specific_arn(
                service, resource.type.split("_")[-1], resource.resource_name
            )
            if specific_arn:
                return specific_arn

        # Fallback to wildcard
        resource_type = resource.type.split("_")[-1]
        return ARNBuilder.get_resource_arn(service, resource_type)
