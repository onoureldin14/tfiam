"""Policy generator for creating IAM policies and reports."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from .models import IAMStatement


class PolicyGenerator:
    """Generates IAM policies and analysis reports."""

    @staticmethod
    def save_policy_clean(
        statements: List[IAMStatement], analysis_metadata: Dict[str, Any], filename: str
    ) -> int:
        """Save clean JSON policy without comments - only Version and Statement section."""
        policy: Dict[str, Any] = {"Version": "2012-10-17", "Statement": []}

        for statement in statements:
            statement_dict = {
                "Sid": statement.sid,
                "Effect": statement.effect,
                "Action": statement.action,
                "Resource": statement.resource,  # This now handles lists
            }
            policy["Statement"].append(statement_dict)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)

        return os.path.getsize(filename)

    @staticmethod
    def save_markdown_report(
        statements: List[IAMStatement], analysis_metadata: Dict[str, Any], filename: str
    ) -> int:
        """Save detailed Markdown report with AI explanations."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# TFIAM Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"**Terraform Directory:** {analysis_metadata.get('terraform_directory', 'N/A')}\n"
            )
            f.write(f"**Services Analyzed:** {analysis_metadata.get('services_count', 0)}\n")
            f.write(f"**Total Statements:** {len(statements)}\n")
            f.write(f"**Total Permissions:** {sum(len(stmt.action) for stmt in statements)}\n")

            # Add verification results if available
            verification_results = analysis_metadata.get("verification_results", {})
            if verification_results:
                f.write(
                    f"**Policy Verification:** {'✅ PASSED' if verification_results.get('verification_passed', False) else '❌ FAILED'}\n"
                )
                f.write(
                    f"**Security Score:** {verification_results.get('security_score', 0)}/100\n"
                )
                f.write(
                    f"**Complexity Score:** {verification_results.get('complexity_score', 0)}/100\n"
                )

            f.write("\n")

            f.write("## Summary\n\n")
            services = analysis_metadata.get("services", [])
            if services:
                f.write("**Discovered AWS Services:**\n")
                for service in sorted(services):
                    f.write(f"- {service.upper()}\n")
                f.write("\n")

            f.write("## IAM Policy Statements\n\n")

            for i, statement in enumerate(statements, 1):
                f.write(f"### Statement {i}: {statement.sid}\n\n")
                f.write(f"**Purpose:** {statement.explanation}\n\n")
                f.write(f"**Effect:** {statement.effect}\n\n")
                f.write(f"**Resource:** `{statement.resource}`\n\n")
                f.write("**Actions:**\n")
                for action in statement.action:
                    f.write(f"- `{action}`\n")
                f.write("\n---\n\n")

            # Add verification analysis section if available
            verification_analysis = analysis_metadata.get("verification_analysis", "")
            verification_recommendations = analysis_metadata.get("verification_recommendations", {})
            verification_passed = analysis_metadata.get("verification_passed", None)
            policy_stats = analysis_metadata.get("policy_statistics", {})
            terraform_stats = analysis_metadata.get("terraform_statistics", {})

            if (
                verification_analysis
                or verification_recommendations
                or verification_passed is not None
            ):
                f.write("## AI Policy Verification & Analysis\n\n")

                # Verification Status
                if verification_passed is not None:
                    status_emoji = "✅" if verification_passed else "❌"
                    status_text = "PASSED" if verification_passed else "FAILED"
                    f.write(f"### Verification Status: {status_emoji} {status_text}\n\n")

                # Statistics Section
                if policy_stats or terraform_stats:
                    f.write("### Analysis Statistics\n\n")

                    if policy_stats:
                        f.write("#### Policy Metrics\n\n")
                        f.write(
                            f"- **Security Score**: {policy_stats.get('security_score', 0)}/100\n"
                        )
                        f.write(
                            f"- **Total Statements**: {policy_stats.get('total_statements', 0)}\n"
                        )
                        f.write(f"- **Total Actions**: {policy_stats.get('total_actions', 0)}\n")
                        f.write(
                            f"- **Unique Services**: {policy_stats.get('unique_services', 0)}\n"
                        )
                        f.write(
                            f"- **Specific Resources**: {policy_stats.get('specific_resources', 0)}\n"
                        )
                        f.write(
                            f"- **Wildcard Resources**: {policy_stats.get('wildcard_resources', 0)}\n"
                        )

                        # Security score interpretation
                        security_score = policy_stats.get("security_score", 0)
                        if security_score >= 80:
                            f.write(f"- **Security Rating**: 🟢 Excellent ({security_score}/100)\n")
                        elif security_score >= 60:
                            f.write(f"- **Security Rating**: 🟡 Good ({security_score}/100)\n")
                        elif security_score >= 40:
                            f.write(f"- **Security Rating**: 🟠 Fair ({security_score}/100)\n")
                        else:
                            f.write(f"- **Security Rating**: 🔴 Poor ({security_score}/100)\n")
                        f.write("\n")

                    if terraform_stats:
                        f.write("#### Infrastructure Metrics\n\n")
                        f.write(
                            f"- **Total Resources**: {terraform_stats.get('total_resources', 0)}\n"
                        )
                        f.write(
                            f"- **Unique Services**: {terraform_stats.get('unique_services', 0)}\n"
                        )
                        f.write(
                            f"- **Complexity Score**: {terraform_stats.get('complexity_score', 0)}/100\n"
                        )

                        # Complexity interpretation
                        complexity_score = terraform_stats.get("complexity_score", 0)
                        if complexity_score >= 80:
                            f.write(
                                f"- **Infrastructure Complexity**: 🔴 High ({complexity_score}/100)\n"
                            )
                        elif complexity_score >= 60:
                            f.write(
                                f"- **Infrastructure Complexity**: 🟡 Medium ({complexity_score}/100)\n"
                            )
                        else:
                            f.write(
                                f"- **Infrastructure Complexity**: 🟢 Low ({complexity_score}/100)\n"
                            )

                        # Services breakdown
                        services = terraform_stats.get("services", [])
                        if services:
                            f.write(f"- **Services Used**: {', '.join(sorted(services))}\n")
                        f.write("\n")

                # AI Analysis Results
                if verification_analysis:
                    f.write("### AI Analysis Results\n\n")
                    f.write(verification_analysis)
                    f.write("\n\n")

                # Recommendations Section
                if verification_recommendations:
                    f.write("### AI Recommendations\n\n")

                    # Count total recommendations
                    total_recommendations = sum(
                        len(v) for v in verification_recommendations.values() if isinstance(v, list)
                    )
                    f.write(f"**Total Recommendations**: {total_recommendations}\n\n")

                    if verification_recommendations.get("critical_issues"):
                        f.write("#### 🚨 Critical Issues\n\n")
                        f.write(
                            f"**Count**: {len(verification_recommendations['critical_issues'])}\n\n"
                        )
                        for i, issue in enumerate(
                            verification_recommendations["critical_issues"], 1
                        ):
                            f.write(f"{i}. {issue}\n")
                        f.write("\n")

                    if verification_recommendations.get("warnings"):
                        f.write("#### ⚠️ Warnings\n\n")
                        f.write(f"**Count**: {len(verification_recommendations['warnings'])}\n\n")
                        for i, warning in enumerate(verification_recommendations["warnings"], 1):
                            f.write(f"{i}. {warning}\n")
                        f.write("\n")

                    if verification_recommendations.get("optimization_suggestions"):
                        f.write("#### 💡 Optimization Suggestions\n\n")
                        f.write(
                            f"**Count**: {len(verification_recommendations['optimization_suggestions'])}\n\n"
                        )
                        for i, suggestion in enumerate(
                            verification_recommendations["optimization_suggestions"], 1
                        ):
                            f.write(f"{i}. {suggestion}\n")
                        f.write("\n")

                    if verification_recommendations.get("security_recommendations"):
                        f.write("#### 🔒 Security Recommendations\n\n")
                        f.write(
                            f"**Count**: {len(verification_recommendations['security_recommendations'])}\n\n"
                        )
                        for i, rec in enumerate(
                            verification_recommendations["security_recommendations"], 1
                        ):
                            f.write(f"{i}. {rec}\n")
                        f.write("\n")

                    if verification_recommendations.get("missing_permissions"):
                        f.write("#### 🔍 Missing Permissions\n\n")
                        f.write(
                            f"**Count**: {len(verification_recommendations['missing_permissions'])}\n\n"
                        )
                        for i, perm in enumerate(
                            verification_recommendations["missing_permissions"], 1
                        ):
                            f.write(f"{i}. {perm}\n")
                        f.write("\n")

                # Summary and Next Steps
                f.write("### Summary & Next Steps\n\n")

                if verification_passed:
                    f.write("✅ **Policy Status**: Your IAM policy passed AI verification.\n\n")
                else:
                    f.write(
                        "❌ **Policy Status**: Your IAM policy has issues that need attention.\n\n"
                    )

                f.write("**Recommended Actions**:\n")
                f.write(
                    "1. **Review Critical Issues**: Address any critical issues identified above\n"
                )
                f.write(
                    "2. **Implement Security Recommendations**: Apply security best practices\n"
                )
                f.write(
                    "3. **Consider Optimization**: Use the AI optimization feature for improved policies\n"
                )
                f.write(
                    "4. **Test Thoroughly**: Validate policies in development before production\n"
                )
                f.write("5. **Regular Audits**: Schedule periodic policy reviews\n\n")

            f.write("## Security Notes\n\n")
            f.write("- Review all permissions before deployment\n")
            f.write("- Consider implementing least-privilege access\n")
            f.write("- Regularly audit IAM policies for compliance\n")
            f.write("- Use specific resource ARNs when possible\n\n")

            f.write("*Generated by TFIAM - Terraform IAM Permission Analyzer*\n")

        return os.path.getsize(filename)
