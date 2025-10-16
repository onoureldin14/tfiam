"""OpenAI integration for generating explanations and verification."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import openai

from ..utils.cache import AIResponseCache
from .models import IAMStatement, TerraformResource


class OpenAIAnalyzer:
    """OpenAI-powered analysis for IAM statements with verification and optimization."""

    def __init__(self, api_key: str, cache_dir: str = ".tfiam-cache"):
        self.client = openai.OpenAI(api_key=api_key)
        self.cache = AIResponseCache(cache_dir)
        self.cache_hits = 0
        self.cache_misses = 0

    def enhance_statements(self, statements: List[IAMStatement]) -> List[IAMStatement]:
        """Enhance statements with AI-generated explanations."""
        enhanced_statements = []

        for statement in statements:
            try:
                explanation = self._generate_explanation(statement)
                enhanced_statement = IAMStatement(
                    sid=statement.sid,
                    effect=statement.effect,
                    action=statement.action,
                    resource=statement.resource,
                    explanation=explanation,
                )
                enhanced_statements.append(enhanced_statement)
            except Exception as e:
                print(f"Warning: Could not generate AI explanation for {statement.sid}: {e}")
                # Use original statement with default explanation
                enhanced_statements.append(statement)

        return enhanced_statements

    def verify_and_optimize_policy(
        self,
        statements: List[IAMStatement],
        terraform_resources: List[TerraformResource],
        terraform_content: str,
        quiet: bool = False,
    ) -> Dict[str, Any]:
        """
        Cross-reference IAM policy with Terraform code and provide verification and optimization.

        Args:
            statements: Generated IAM statements
            terraform_resources: List of Terraform resources found
            terraform_content: Combined Terraform file content
            quiet: Whether to suppress progress output

        Returns:
            Dict containing verification results and recommendations
        """
        if not quiet:
            from ..cli.cyber_cli import CyberCLI

            print(
                f"\n{CyberCLI.MAGENTA}🔍 Cross-referencing policy with Terraform code...{CyberCLI.END}"
            )

        # Create cache data for verification
        verification_data = {
            "terraform_resources": [f"{r.type}:{r.name}" for r in terraform_resources],
            "policy_statements": [
                f"{s.sid}:{s.effect}:{','.join(s.action[:3])}" for s in statements
            ],
            "terraform_content": terraform_content,
        }

        # Check cache first
        cached_response = self.cache.get_verification(verification_data)
        if cached_response:
            if not quiet:
                print(f"  📦 Using cached verification response")

            # Parse the cached response into structured recommendations
            recommendations = self._parse_verification_response(cached_response)

            return {
                "verification_passed": recommendations.get("verification_passed", True),
                "recommendations": recommendations,
                "raw_analysis": cached_response,
                "policy_statistics": self._calculate_policy_statistics(statements),
                "terraform_statistics": self._calculate_terraform_statistics(terraform_resources),
            }

        # Prepare data for AI analysis
        policy_summary = self._create_policy_summary(statements)
        terraform_summary = self._create_terraform_summary(terraform_resources, terraform_content)

        # Generate comprehensive verification prompt
        verification_prompt = self._create_verification_prompt(
            policy_summary, terraform_summary, statements
        )

        try:
            # Start loading spinner for verification
            spinner = None
            if not quiet:
                from ..cli.cyber_cli import CyberCLI

                spinner = CyberCLI.create_loading_spinner("🔍 AI Analyzing Policy", CyberCLI.CYAN)
                spinner.start()

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use more capable model for complex analysis
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AWS security expert and Terraform specialist.
                        Your task is to verify IAM policies against Terraform code and provide optimization recommendations.
                        Focus on:
                        1. Permission accuracy - are permissions aligned with actual resource usage?
                        2. Security posture - are permissions too broad or too narrow?
                        3. Missing permissions - what might be missing for proper operation?
                        4. Optimization opportunities - how can permissions be improved?
                        5. Best practices - adherence to AWS security best practices.

                        Provide specific, actionable feedback.""",
                    },
                    {"role": "user", "content": verification_prompt},
                ],
                max_tokens=800,
                temperature=0.1,  # Low temperature for consistent analysis
                timeout=30,
            )

            verification_result = response.choices[0].message.content.strip()

            # Stop loading spinner
            if spinner:
                spinner.stop("✅ AI Analysis Complete!")

            # Cache the response (handle Unicode issues)
            try:
                self.cache.set_verification(verification_data, verification_result)
            except UnicodeEncodeError:
                if not quiet:
                    print(f"  ⚠️  Could not cache verification response due to encoding issues")

            # Parse the response into structured recommendations
            recommendations = self._parse_verification_response(verification_result)

            return {
                "verification_passed": recommendations.get("verification_passed", True),
                "recommendations": recommendations,
                "raw_analysis": verification_result,
                "policy_statistics": self._calculate_policy_statistics(statements),
                "terraform_statistics": self._calculate_terraform_statistics(terraform_resources),
            }

        except Exception as e:
            # Stop spinner on error
            if spinner:
                spinner.stop("❌ AI Verification Failed")
            if not quiet:
                from ..cli.cyber_cli import CyberCLI

                print(f"{CyberCLI.YELLOW}Warning: Policy verification failed: {e}{CyberCLI.END}")

            return {
                "verification_passed": False,
                "error": str(e),
                "recommendations": {"critical_issues": [f"Verification failed: {e}"]},
                "policy_statistics": self._calculate_policy_statistics(statements),
                "terraform_statistics": self._calculate_terraform_statistics(terraform_resources),
            }

    def enhance_statements_with_progress(
        self, statements: List[IAMStatement], quiet: bool = False
    ) -> List[IAMStatement]:
        """Enhance statements with AI-generated explanations and progress tracking."""
        total = len(statements)
        enhanced_statements = [None] * total  # Pre-allocate list

        # Use concurrent processing for better performance
        max_workers = min(5, total)  # Limit concurrent requests

        def process_statement(indexed_statement):
            i, statement = indexed_statement
            if not quiet:
                print(f"  {i+1}/{total} - Analyzing {statement.sid}...", end=" ", flush=True)

            start_time = time.time()

            try:
                # Check if this will be a cache hit before generating
                statement_data = {
                    "sid": statement.sid,
                    "effect": statement.effect,
                    "action": statement.action,
                    "resource": statement.resource,
                }
                is_cache_hit = self.cache.get(statement_data) is not None

                explanation = self._generate_explanation(statement)
                enhanced_statement = IAMStatement(
                    sid=statement.sid,
                    effect=statement.effect,
                    action=statement.action,
                    resource=statement.resource,
                    explanation=explanation,
                )

                if not quiet:
                    duration = time.time() - start_time
                    cache_indicator = "📦" if is_cache_hit else "🌐"
                    print(f"{cache_indicator} ✓ ({duration:.1f}s)")

                return i, enhanced_statement

            except Exception as e:
                if not quiet:
                    duration = time.time() - start_time
                    print(f"✗ ({duration:.1f}s) - {str(e)[:50]}...")

                # Use original statement with default explanation
                return i, statement

        # Process statements concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(process_statement, (i, stmt)): i
                for i, stmt in enumerate(statements)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    index, enhanced_statement = future.result()
                    enhanced_statements[index] = enhanced_statement
                except Exception as e:
                    if not quiet:
                        print(f"Unexpected error: {e}")

        return enhanced_statements

    def generate_optimized_policy(
        self,
        statements: List[IAMStatement],
        terraform_resources: List[TerraformResource],
        verification_result: Dict[str, Any],
        quiet: bool = False,
    ) -> str:
        """
        Generate an optimized IAM policy using AI with caching.

        Args:
            statements: Current IAM statements
            terraform_resources: List of Terraform resources
            verification_result: Verification analysis results
            quiet: Whether to suppress progress output

        Returns:
            Optimized IAM policy as JSON string
        """
        # Create cache data for optimization
        optimization_data = {
            "terraform_resources": [f"{r.type}:{r.name}" for r in terraform_resources],
            "policy_statements": [
                f"{s.sid}:{s.effect}:{','.join(s.action[:3])}" for s in statements
            ],
            "verification_analysis": verification_result.get("raw_analysis", ""),
        }

        # Check cache first
        cached_response = self.cache.get_optimization(optimization_data)
        if cached_response:
            if not quiet:
                print(f"  📦 Using cached optimization response")
            return cached_response

        # Generate optimization prompt
        optimization_prompt = f"""
You are an AWS security expert. Generate a complete, valid JSON IAM policy based on the analysis below.

CURRENT POLICY ANALYSIS:
{verification_result.get('raw_analysis', '')}

TERRAFORM RESOURCES FOUND:
{len(terraform_resources)} resources across services: {', '.join(set(r.type.split('_')[1] for r in terraform_resources if len(r.type.split('_')) > 1))}

CURRENT IAM STATEMENTS:
{self._format_statements_for_ai(statements)}

REQUIREMENTS:
1. Apply the principle of least privilege
2. Use specific resource ARNs where possible (not wildcards)
3. Remove unnecessary permissions
4. Group related permissions efficiently
5. Follow AWS security best practices
6. Ensure all Terraform resources are properly covered

CRITICAL: You MUST respond with a complete, valid JSON object. Do not truncate or leave incomplete statements.

Required format (complete the entire structure):
{{
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Sid": "DescriptiveName",
      "Effect": "Allow",
      "Action": ["service:action"],
      "Resource": "arn:aws:service:region:account:resource"
    }}
  ]
}}

IMPORTANT:
- Include ALL statements for all services
- Ensure proper JSON syntax (no trailing commas)
- Complete all opening and closing braces
- Do not include any text outside the JSON
- Make sure the JSON is valid and parseable
"""

        try:
            # Start loading spinner for AI optimization
            spinner = None
            if not quiet:
                from ..cli.cyber_cli import CyberCLI

                spinner = CyberCLI.create_loading_spinner(
                    "🤖 AI Generating Optimized Policy", CyberCLI.MAGENTA
                )
                spinner.start()

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "AWS security expert. Generate complete, valid JSON IAM policies. Always respond with ONLY the complete JSON policy, no explanations. Ensure the JSON is properly closed and valid.",
                    },
                    {"role": "user", "content": optimization_prompt},
                ],
                max_tokens=2000,  # Increased to ensure complete response
                temperature=0.1,
                timeout=60,  # Increased timeout for larger responses
            )

            optimized_policy_json = response.choices[0].message.content.strip()

            # Stop loading spinner
            if spinner:
                spinner.stop("✅ AI Policy Generated!")

            # Cache the response (handle Unicode issues)
            try:
                self.cache.set_optimization(optimization_data, optimized_policy_json)
            except UnicodeEncodeError:
                if not quiet:
                    print(f"  ⚠️  Could not cache optimization response due to encoding issues")

            return optimized_policy_json

        except Exception as e:
            # Stop spinner on error
            if spinner:
                spinner.stop("❌ AI Policy Generation Failed")
            if not quiet:
                from ..cli.cyber_cli import CyberCLI

                print(f"{CyberCLI.YELLOW}Warning: Policy optimization failed: {e}{CyberCLI.END}")
            raise e

    def _format_statements_for_ai(self, statements):
        """Format IAM statements for AI analysis."""
        formatted = []
        for i, stmt in enumerate(statements, 1):
            formatted.append(f"Statement {i} ({stmt.sid}):")
            formatted.append(
                f"  Actions: {', '.join(stmt.action[:5])}{'...' if len(stmt.action) > 5 else ''}"
            )
            formatted.append(f"  Resources: {stmt.resource[0] if stmt.resource else 'N/A'}")
            formatted.append("")
        return "\n".join(formatted)

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        stats = self.cache.get_stats()
        stats.update(
            {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "total_requests": self.cache_hits + self.cache_misses,
                "hit_rate": (self.cache_hits / (self.cache_hits + self.cache_misses) * 100)
                if (self.cache_hits + self.cache_misses) > 0
                else 0,
            }
        )
        return stats

    def _generate_explanation(self, statement: IAMStatement) -> str:
        """Generate AI explanation for a statement."""
        # Create statement data for cache key generation
        statement_data = {
            "sid": statement.sid,
            "effect": statement.effect,
            "action": statement.action,
            "resource": statement.resource,
        }

        # Check cache first
        cached_response = self.cache.get(statement_data)
        if cached_response:
            self.cache_hits += 1
            return cached_response

        self.cache_misses += 1

        # Optimized prompt - shorter and more focused
        actions_str = ", ".join(statement.action[:5])  # Limit to first 5 actions
        if len(statement.action) > 5:
            actions_str += f" (+{len(statement.action) - 5} more)"

        prompt = f"""Explain this IAM statement in 2-3 sentences:
SID: {statement.sid}
Actions: {actions_str}
Resources: {statement.resource[0] if statement.resource else 'N/A'}

Focus on: what it allows and security implications."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "AWS security expert. Give concise IAM explanations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,  # Reduced from 150
            temperature=0.2,  # Reduced for consistency
            timeout=10,  # Add timeout
        )

        explanation = response.choices[0].message.content.strip()

        # Cache the response
        self.cache.set(statement_data, explanation)

        return explanation

    def _create_policy_summary(self, statements: List[IAMStatement]) -> str:
        """Create a summary of the generated IAM policy."""
        total_actions = sum(len(stmt.action) for stmt in statements)
        services = set()
        resource_types = set()

        for stmt in statements:
            # Extract service from actions
            for action in stmt.action:
                if ":" in action:
                    service = action.split(":")[0]
                    services.add(service)

            # Extract resource types from resources
            for resource in stmt.resource:
                if isinstance(resource, str) and "arn:aws:" in resource:
                    parts = resource.split(":")
                    if len(parts) >= 4:
                        service = parts[2]
                        resource_type = parts[5].split("/")[0] if len(parts) > 5 else "unknown"
                        resource_types.add(f"{service}:{resource_type}")

        return f"""
Policy Summary:
- {len(statements)} IAM statements
- {total_actions} total permissions
- Services: {', '.join(sorted(services))}
- Resource types: {', '.join(sorted(resource_types))}
"""

    def _create_terraform_summary(
        self, resources: List[TerraformResource], terraform_content: str
    ) -> str:
        """Create a summary of the Terraform resources and configuration."""
        services = set()
        resource_counts = {}

        for resource in resources:
            service = (
                resource.type.split("_")[1] if len(resource.type.split("_")) > 1 else "unknown"
            )
            services.add(service)
            resource_counts[resource.type] = resource_counts.get(resource.type, 0) + 1

        # Analyze Terraform content for patterns
        content_analysis = self._analyze_terraform_patterns(terraform_content)

        return f"""
Terraform Summary:
- {len(resources)} AWS resources
- Services: {', '.join(sorted(services))}
- Resource breakdown: {dict(list(resource_counts.items())[:10])}
- Configuration patterns: {content_analysis}
"""

    def _analyze_terraform_patterns(self, content: str) -> str:
        """Analyze Terraform content for common patterns."""
        patterns = []

        if "for_each" in content:
            patterns.append("dynamic resources")
        if "count" in content:
            patterns.append("conditional resources")
        if "data." in content:
            patterns.append("data sources")
        if "module." in content:
            patterns.append("modules")
        if "depends_on" in content:
            patterns.append("explicit dependencies")
        if "lifecycle" in content:
            patterns.append("lifecycle rules")

        return ", ".join(patterns) if patterns else "standard configuration"

    def _create_verification_prompt(
        self, policy_summary: str, terraform_summary: str, statements: List[IAMStatement]
    ) -> str:
        """Create a comprehensive verification prompt for AI analysis."""

        # Create detailed statement breakdown
        statement_details = []
        for i, stmt in enumerate(statements[:10], 1):  # Limit to first 10 for prompt length
            actions_preview = ", ".join(stmt.action[:3])
            if len(stmt.action) > 3:
                actions_preview += f" (+{len(stmt.action) - 3} more)"

            resources_preview = stmt.resource[0] if stmt.resource else "N/A"
            if len(stmt.resource) > 1:
                resources_preview += f" (+{len(stmt.resource) - 1} more resources)"

            statement_details.append(
                f"""
Statement {i} ({stmt.sid}):
  Actions: {actions_preview}
  Resources: {resources_preview}
"""
            )

        prompt = f"""
Please verify this IAM policy against the Terraform configuration and provide optimization recommendations.

{policy_summary}

{terraform_summary}

IAM Statement Details:
{''.join(statement_details)}

Please analyze and provide:
1. **Permission Accuracy**: Are the permissions correctly aligned with the Terraform resources?
2. **Security Assessment**: Are permissions appropriately scoped (not too broad/restrictive)?
3. **Missing Permissions**: What permissions might be missing for proper operation?
4. **Optimization Opportunities**: How can this policy be improved?
5. **Best Practice Compliance**: Does this follow AWS security best practices?

Format your response with clear sections and actionable recommendations.
"""

        return prompt

    def _parse_verification_response(self, response: str) -> Dict[str, Any]:
        """Parse AI verification response into structured recommendations."""
        recommendations = {
            "critical_issues": [],
            "warnings": [],
            "optimization_suggestions": [],
            "security_recommendations": [],
            "missing_permissions": [],
            "verification_passed": True,
        }

        # Simple parsing - in a real implementation, you'd want more sophisticated parsing
        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if any(keyword in line.lower() for keyword in ["critical", "issue", "problem"]):
                current_section = "critical_issues"
            elif any(keyword in line.lower() for keyword in ["warning", "concern", "caution"]):
                current_section = "warnings"
            elif any(keyword in line.lower() for keyword in ["optimization", "improve", "suggest"]):
                current_section = "optimization_suggestions"
            elif any(keyword in line.lower() for keyword in ["security", "secure"]):
                current_section = "security_recommendations"
            elif any(keyword in line.lower() for keyword in ["missing", "missing permission"]):
                current_section = "missing_permissions"
            elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                # This is a recommendation item
                if current_section and current_section in recommendations:
                    recommendations[current_section].append(line[1:].strip())

        # Check if there are critical issues
        if recommendations["critical_issues"]:
            recommendations["verification_passed"] = False

        return recommendations

    def _calculate_policy_statistics(self, statements: List[IAMStatement]) -> Dict[str, Any]:
        """Calculate policy statistics."""
        total_actions = sum(len(stmt.action) for stmt in statements)
        services = set()
        wildcard_resources = 0
        specific_resources = 0

        for stmt in statements:
            for action in stmt.action:
                if ":" in action:
                    services.add(action.split(":")[0])

            for resource in stmt.resource:
                if isinstance(resource, str):
                    if "*" in resource:
                        wildcard_resources += 1
                    else:
                        specific_resources += 1

        return {
            "total_statements": len(statements),
            "total_actions": total_actions,
            "unique_services": len(services),
            "services": list(services),
            "wildcard_resources": wildcard_resources,
            "specific_resources": specific_resources,
            "security_score": self._calculate_security_score(
                statements, wildcard_resources, specific_resources
            ),
        }

    def _calculate_terraform_statistics(self, resources: List[TerraformResource]) -> Dict[str, Any]:
        """Calculate Terraform statistics."""
        services = set()
        resource_types = {}

        for resource in resources:
            service = (
                resource.type.split("_")[1] if len(resource.type.split("_")) > 1 else "unknown"
            )
            services.add(service)
            resource_types[resource.type] = resource_types.get(resource.type, 0) + 1

        return {
            "total_resources": len(resources),
            "unique_services": len(services),
            "services": list(services),
            "resource_types": resource_types,
            "complexity_score": self._calculate_complexity_score(resources),
        }

    def _calculate_security_score(
        self, statements: List[IAMStatement], wildcards: int, specific: int
    ) -> int:
        """Calculate a basic security score (0-100, higher is better)."""
        if wildcards + specific == 0:
            return 50

        # Favor specific resources over wildcards
        specificity_ratio = specific / (wildcards + specific)
        base_score = int(specificity_ratio * 70)

        # Bonus for reasonable number of statements (not too many, not too few)
        statement_count = len(statements)
        if 5 <= statement_count <= 20:
            base_score += 20
        elif 20 < statement_count <= 50:
            base_score += 10

        return min(100, max(0, base_score))

    def _calculate_complexity_score(self, resources: List[TerraformResource]) -> int:
        """Calculate a complexity score (0-100, higher is more complex)."""
        # Simple complexity based on resource count and diversity
        resource_count = len(resources)
        unique_types = len(set(r.type for r in resources))

        # More resources and more diverse types = higher complexity
        complexity = min(100, (resource_count * 2) + (unique_types * 5))
        return complexity
