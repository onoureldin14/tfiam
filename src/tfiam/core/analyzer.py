"""Terraform analyzer for extracting AWS resources and generating IAM permissions."""

import os
import re
from collections import Counter
from typing import Dict, List, Optional, Set

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
        """Scan directory for Terraform files."""
        tf_files = []
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and common non-Terraform directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["node_modules", "venv", "__pycache__"]
            ]

            for file in files:
                if file.endswith(".tf"):
                    tf_files.append(os.path.join(root, file))

        for tf_file in tf_files:
            self.parse_terraform_file(tf_file)

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

        # Extract locals - handle nested braces properly
        locals_pattern = r"locals\s*\{(.*?)\n\}"
        for match in re.finditer(locals_pattern, content, re.MULTILINE | re.DOTALL):
            locals_content = match.group(1)

            # Parse line by line with brace counting
            lines = locals_content.split("\n")
            brace_count = 0
            current_local = None
            current_value = []

            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                # Count braces
                brace_count += stripped.count("{") - stripped.count("}")

                # Check for new local definition (at brace level 0)
                if brace_count == 0 and "=" in stripped:
                    # Save previous local if exists
                    if current_local and current_value:
                        full_value = " ".join(current_value).strip().strip("\"'")
                        if full_value.endswith(","):
                            full_value = full_value[:-1]
                        self.locals[f"local.{current_local}"] = full_value

                    # Parse new local
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        current_local = parts[0].strip()
                        current_value = [parts[1].strip()]
                    continue

                # Add to current value if we're in a local
                if current_local is not None:
                    current_value.append(stripped)

            # Save last local
            if current_local and current_value:
                full_value = " ".join(current_value).strip().strip("\"'")
                if full_value.endswith(","):
                    full_value = full_value[:-1]
                self.locals[f"local.{current_local}"] = full_value

    def resolve_variable_reference(self, value: str) -> str:
        """Resolve variable and local references."""
        if not isinstance(value, str):
            return str(value)

        result = value

        # Handle variable references
        var_pattern = r"\$\{var\.([^}]+)\}"
        for var_match in re.finditer(var_pattern, value):
            var_name = f"var.{var_match.group(1)}"
            if var_name in self.variables:
                result = result.replace(var_match.group(0), self.variables[var_name])

        # Handle local references
        local_pattern = r"\$\{local\.([^}]+)\}"
        for local_match in re.finditer(local_pattern, value):
            local_name = f"local.{local_match.group(1)}"
            if local_name in self.locals:
                resolved = self.resolve_variable_reference(self.locals[local_name])
                result = result.replace(local_match.group(0), resolved)

        # Handle data source references
        data_pattern = r"\$\{data\.([^}]+)\}"
        for data_match in re.finditer(data_pattern, value):
            # For now, just replace with a placeholder
            result = result.replace(data_match.group(0), f"{data_match.group(1)}-*")

        return result

    def extract_resources(self, content: str, file_path: str) -> None:
        """Extract AWS resources from Terraform content."""
        resource_pattern = (
            r'resource\s+["\']([^"\']+)["\']\s+["\']([^"\']+)["\']\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        )

        for match in re.finditer(resource_pattern, content, re.MULTILINE | re.DOTALL):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_content = match.group(3)

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
        """Extract key-value pairs from resource content."""
        properties = {}

        # Simple key-value extraction (handles basic cases)
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip("\"'")
                    if value.endswith(","):
                        value = value[:-1]
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
        }

        name_prop = name_properties.get(resource_type, "name")

        if name_prop in properties:
            raw_value = properties[name_prop]
            resolved_value = self.resolve_variable_reference(raw_value)
            if resolved_value and resolved_value != raw_value:
                return resolved_value

        return terraform_name

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

                # Get permissions for this service/resource type (with dynamic fallback)
                actions = self._get_dynamic_permissions(aws_service, resource_type)

                # Create a key based on service and permissions (not resource type)
                service_key = aws_service

                if service_key not in permission_groups:
                    permission_groups[service_key] = {}

                if actions not in permission_groups[service_key]:
                    permission_groups[service_key][actions] = {
                        "resources": [],
                        "resource_types": set(),
                        "service": aws_service,
                    }

                permission_groups[service_key][actions]["resources"].append(resource)
                permission_groups[service_key][actions]["resource_types"].add(resource_type)

        # Generate statements for each permission group
        for service_key, action_groups in permission_groups.items():
            for actions, group_info in action_groups.items():
                resources = group_info["resources"]
                resource_types = list(group_info["resource_types"])
                aws_service = group_info["service"]

                # Create a descriptive SID
                if len(resource_types) == 1:
                    sid = f"{aws_service.title()}{resource_types[0].title()}"
                else:
                    # Group multiple resource types under the service
                    sid = f"{aws_service.title()}Resources"

                # Generate resource ARNs - either specific or wildcard
                specific_arns = []
                for resource in resources:
                    resource_arn = self._get_resource_arn_for_resource(aws_service, resource)
                    if (
                        resource_arn
                        and "*" not in resource_arn
                        and resource_arn not in specific_arns
                    ):
                        specific_arns.append(resource_arn)

                # Use specific ARNs if available, otherwise use wildcard
                if specific_arns:
                    # Use list of specific ARNs for multiple resources
                    final_resource = specific_arns
                else:
                    # Use the most specific wildcard possible
                    if len(resource_types) == 1:
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

    def _get_resource_arn_for_resource(self, service: str, resource: TerraformResource) -> str:
        """Get resource ARN for a specific resource."""
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
