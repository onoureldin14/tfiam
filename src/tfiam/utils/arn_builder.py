"""ARN building utilities for AWS resources."""

from typing import Optional


class ARNBuilder:
    """Utility class for building AWS ARNs."""

    @staticmethod
    def build_specific_arn(service: str, resource_type: str, resource_name: str) -> Optional[str]:
        """Build specific ARN for a resource if possible."""
        arn_templates = {
            "iam": {
                "role": f"arn:aws:iam::${{aws_account}}:role/{resource_name}",
                "policy": f"arn:aws:iam::${{aws_account}}:policy/{resource_name}",
                "user": f"arn:aws:iam::${{aws_account}}:user/{resource_name}",
            },
            "s3": {"bucket": f"arn:aws:s3:::{resource_name}"},
            "lambda": {
                "function": f"arn:aws:lambda:${{aws_region}}:${{aws_account}}:function:{resource_name}"
            },
            "rds": {
                "instance": f"arn:aws:rds:${{aws_region}}:${{aws_account}}:db:{resource_name}",
                "subnet_group": f"arn:aws:rds:${{aws_region}}:${{aws_account}}:subgrp:{resource_name}",
            },
            "logs": {
                "log_group": f"arn:aws:logs:${{aws_region}}:${{aws_account}}:log-group:{resource_name}*"
            },
            "cloudwatch": {
                "metric_alarm": f"arn:aws:cloudwatch:${{aws_region}}:${{aws_account}}:alarm:{resource_name}",
                "dashboard": f"arn:aws:cloudwatch:${{aws_region}}:${{aws_account}}:dashboard/{resource_name}",
            },
        }

        if service in arn_templates and resource_type in arn_templates[service]:
            return arn_templates[service][resource_type]

        # Generic ARN for unknown services
        return f"arn:aws:{service}:${{aws_region}}:${{aws_account}}:{resource_type}/{resource_name}"

    @staticmethod
    def get_resource_arn(service: str, resource_type: str) -> str:
        """Get wildcard ARN for a service and resource type."""
        arn_patterns = {
            "ec2": {
                "instance": "arn:aws:ec2:${aws_region}:${aws_account}:instance/*",
                "volume": "arn:aws:ec2:${aws_region}:${aws_account}:volume/*",
                "vpc": "arn:aws:ec2:${aws_region}:${aws_account}:vpc/*",
            },
            "s3": {"bucket": "arn:aws:s3:::*"},
            "rds": {
                "instance": "arn:aws:rds:${aws_region}:${aws_account}:db:*",
                "subnet_group": "arn:aws:rds:${aws_region}:${aws_account}:subgrp:*",
            },
            "iam": {
                "role": "arn:aws:iam::${aws_account}:role/*",
                "policy": "arn:aws:iam::${aws_account}:policy/*",
                "user": "arn:aws:iam::${aws_account}:user/*",
            },
            "lambda": {"function": "arn:aws:lambda:${aws_region}:${aws_account}:function:*"},
            "logs": {"log_group": "arn:aws:logs:${aws_region}:${aws_account}:log-group:*"},
            "cloudwatch": {
                "metric_alarm": "arn:aws:cloudwatch:${aws_region}:${aws_account}:alarm:*",
                "dashboard": "arn:aws:cloudwatch:${aws_region}:${aws_account}:dashboard/*",
            },
            "route53": {
                "record": "arn:aws:route53:::hostedzone/*",
                "zone": "arn:aws:route53:::hostedzone/*",
            },
        }

        return arn_patterns.get(service, {}).get(
            resource_type, f"arn:aws:{service}:${{aws_region}}:${{aws_account}}:*"
        )
