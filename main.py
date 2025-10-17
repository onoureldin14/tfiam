#!/usr/bin/env python3
"""
TFIAM - Terraform IAM Permission Analyzer

A tool that scans Terraform repositories and recommends IAM permissions
with OpenAI-powered explanations for complete resource management.
"""

import argparse
import getpass
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tfiam import CyberCLI, OpenAIAnalyzer, PolicyGenerator, TerraformAnalyzer, print_cyberpunk_help


def get_openai_key():
    """Get OpenAI API key from environment or prompt user."""
    # Check if key exists in environment
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key

    print(f"{CyberCLI.YELLOW}OpenAI API key not found in environment.{CyberCLI.END}")
    print(
        f"{CyberCLI.CYAN}To enable AI-powered explanations, please provide your OpenAI API key.{CyberCLI.END}"
    )
    print(
        f"{CyberCLI.GRAY}You can get one from: https://platform.openai.com/api-keys{CyberCLI.END}"
    )

    while True:
        key = getpass.getpass(f"{CyberCLI.CYAN}Enter your OpenAI API key: {CyberCLI.END}")
        if key.strip():
            # Show first 5 characters and mask the rest for verification
            masked_key = key[:5] + "*" * (len(key) - 5) if len(key) > 5 else key
            print(f"{CyberCLI.GREEN}✅ API key received: {masked_key}{CyberCLI.END}")
            break
        print(f"{CyberCLI.RED}Please enter a valid API key.{CyberCLI.END}")

    # Ask if user wants to save it permanently
    save = input(
        f"{CyberCLI.CYAN}Would you like to save this key to your shell profile? (y/n): {CyberCLI.END}"
    ).lower()
    if save in ["y", "yes"]:
        save_key_to_profile(key)

    return key


def _display_verification_results(verification_result):
    """Display AI verification and optimization results."""
    print(f"\n{CyberCLI.MAGENTA}🔍 AI Policy Verification Results:{CyberCLI.END}")

    # Display verification status
    if verification_result.get("verification_passed", False):
        print(f"{CyberCLI.GREEN}✅ Policy verification passed{CyberCLI.END}")
    else:
        print(f"{CyberCLI.RED}❌ Policy verification failed{CyberCLI.END}")

    # Display statistics
    policy_stats = verification_result.get("policy_statistics", {})
    terraform_stats = verification_result.get("terraform_statistics", {})

    print(f"\n{CyberCLI.CYAN}📊 Analysis Statistics:{CyberCLI.END}")
    print(f"  Security Score: {policy_stats.get('security_score', 0)}/100")
    print(f"  Complexity Score: {terraform_stats.get('complexity_score', 0)}/100")
    print(f"  Specific Resources: {policy_stats.get('specific_resources', 0)}")
    print(f"  Wildcard Resources: {policy_stats.get('wildcard_resources', 0)}")

    # Display recommendations
    recommendations = verification_result.get("recommendations", {})

    if recommendations.get("critical_issues"):
        print(f"\n{CyberCLI.RED}🚨 Critical Issues:{CyberCLI.END}")
        for issue in recommendations["critical_issues"]:
            print(f"  • {issue}")

    if recommendations.get("warnings"):
        print(f"\n{CyberCLI.YELLOW}⚠️  Warnings:{CyberCLI.END}")
        for warning in recommendations["warnings"]:
            print(f"  • {warning}")

    if recommendations.get("optimization_suggestions"):
        print(f"\n{CyberCLI.CYAN}💡 Optimization Suggestions:{CyberCLI.END}")
        for suggestion in recommendations["optimization_suggestions"]:
            print(f"  • {suggestion}")

    if recommendations.get("security_recommendations"):
        print(f"\n{CyberCLI.MAGENTA}🔒 Security Recommendations:{CyberCLI.END}")
        for rec in recommendations["security_recommendations"]:
            print(f"  • {rec}")

    if recommendations.get("missing_permissions"):
        print(f"\n{CyberCLI.BLUE}🔍 Missing Permissions:{CyberCLI.END}")
        for perm in recommendations["missing_permissions"]:
            print(f"  • {perm}")


def _show_optimization_prompt(
    verification_result, openai_analyzer, statements, resources, directory, output_dir, quiet
):
    """Show optimization prompt after analysis completion."""
    if quiet:
        return

    print(f"\n{CyberCLI.MAGENTA}🎯 AI Optimization Available!{CyberCLI.END}")

    # Show a preview of what optimization would do
    recommendations = verification_result.get("recommendations", {})
    total_recommendations = sum(len(v) for v in recommendations.values() if isinstance(v, list))

    if total_recommendations > 0:
        print(
            f"{CyberCLI.CYAN}📊 Analysis found {total_recommendations} optimization opportunities:{CyberCLI.END}"
        )

        if recommendations.get("critical_issues"):
            print(f"  🚨 {len(recommendations['critical_issues'])} critical issues")
        if recommendations.get("warnings"):
            print(f"  ⚠️  {len(recommendations['warnings'])} warnings")
        if recommendations.get("optimization_suggestions"):
            print(
                f"  💡 {len(recommendations['optimization_suggestions'])} optimization suggestions"
            )
        if recommendations.get("security_recommendations"):
            print(
                f"  🔒 {len(recommendations['security_recommendations'])} security recommendations"
            )
        if recommendations.get("missing_permissions"):
            print(f"  🔍 {len(recommendations['missing_permissions'])} missing permissions")

        print(
            f"\n{CyberCLI.GRAY}AI can generate an optimized policy with these improvements applied.{CyberCLI.END}"
        )
    else:
        print(
            f"{CyberCLI.GREEN}✅ Your policy looks good! No major optimization opportunities found.{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GRAY}AI can still generate a detailed optimization report for best practices.{CyberCLI.END}"
        )

    # Ask if user wants optimization
    while True:
        choice = (
            input(
                f"\n{CyberCLI.CYAN}Would you like AI to generate an optimized policy? (y/n): {CyberCLI.END}"
            )
            .strip()
            .lower()
        )
        if choice in ["y", "yes"]:
            _generate_optimized_policy(
                openai_analyzer, statements, resources, directory, output_dir, verification_result
            )
            break
        elif choice in ["n", "no"]:
            print(
                f"{CyberCLI.GRAY}No optimization requested. Your current policy is ready for use.{CyberCLI.END}"
            )
            break
        else:
            print(f"{CyberCLI.RED}Please enter 'y' for yes or 'n' for no.{CyberCLI.END}")


def _generate_optimized_policy(
    openai_analyzer, statements, resources, directory, output_dir, verification_result
):
    """Generate an optimized policy based on AI recommendations."""
    print(f"\n{CyberCLI.MAGENTA}🚀 Generating optimized policy...{CyberCLI.END}")

    try:
        # Use the new cached optimization method
        optimized_policy_json = openai_analyzer.generate_optimized_policy(
            statements, resources, verification_result, quiet=False
        )

        # Clean up the response to extract just the JSON
        optimized_policy_json = _extract_json_from_response(optimized_policy_json)

        # Validate and save the optimized policy
        optimized_filename = os.path.join(output_dir, "tf-ai-permissions-ai-powered.json")

        try:
            import json

            # Validate JSON
            optimized_policy = json.loads(optimized_policy_json)

            # Save the optimized policy
            with open(optimized_filename, "w", encoding="utf-8") as f:
                json.dump(optimized_policy, f, indent=2, ensure_ascii=False)

            optimized_size = os.path.getsize(optimized_filename)

            print(f"{CyberCLI.GREEN}✅ AI-optimized policy generated!{CyberCLI.END}")
            print(
                f"{CyberCLI.CYAN}📄 File: {os.path.basename(optimized_filename)} ({optimized_size:,} bytes){CyberCLI.END}"
            )
            print(f"{CyberCLI.GRAY}📁 Location: {optimized_filename}{CyberCLI.END}")

            # Show comparison
            original_statements = len(statements)
            optimized_statements = len(optimized_policy.get("Statement", []))
            original_permissions = sum(len(stmt.action) for stmt in statements)
            optimized_permissions = sum(
                len(stmt.get("Action", [])) for stmt in optimized_policy.get("Statement", [])
            )

            print(f"\n{CyberCLI.CYAN}📊 Policy Comparison:{CyberCLI.END}")
            print(
                f"  Original: {original_statements} statements, {original_permissions} permissions"
            )
            print(
                f"  Optimized: {optimized_statements} statements, {optimized_permissions} permissions"
            )

            if optimized_permissions < original_permissions:
                reduction = original_permissions - optimized_permissions
                print(
                    f"  🎯 Reduced permissions by {reduction} ({reduction/original_permissions*100:.1f}%)"
                )

        except json.JSONDecodeError as e:
            print(
                f"{CyberCLI.YELLOW}⚠️  Generated policy had JSON formatting issues: {e}{CyberCLI.END}"
            )

            # Try to fix common JSON issues
            try:
                # Apply comprehensive JSON fixes
                fixed_json = _fix_json_formatting(optimized_policy_json)

                # Try parsing again
                optimized_policy = json.loads(fixed_json)

                # Save the fixed policy
                with open(optimized_filename, "w", encoding="utf-8") as f:
                    json.dump(optimized_policy, f, indent=2, ensure_ascii=False)

                optimized_size = os.path.getsize(optimized_filename)
                print(
                    f"{CyberCLI.GREEN}✅ AI-optimized policy generated (after fixing JSON issues)!{CyberCLI.END}"
                )
                print(
                    f"{CyberCLI.CYAN}📄 File: {os.path.basename(optimized_filename)} ({optimized_size:,} bytes){CyberCLI.END}"
                )

                # Show comparison
                original_statements = len(statements)
                optimized_statements = len(optimized_policy.get("Statement", []))
                original_permissions = sum(len(stmt.action) for stmt in statements)
                optimized_permissions = sum(
                    len(stmt.get("Action", [])) for stmt in optimized_policy.get("Statement", [])
                )

                print(f"\n{CyberCLI.CYAN}📊 Policy Comparison:{CyberCLI.END}")
                print(
                    f"  Original: {original_statements} statements, {original_permissions} permissions"
                )
                print(
                    f"  Optimized: {optimized_statements} statements, {optimized_permissions} permissions"
                )

                if optimized_permissions < original_permissions:
                    reduction = original_permissions - optimized_permissions
                    print(
                        f"  🎯 Reduced permissions by {reduction} ({reduction/original_permissions*100:.1f}%)"
                    )

            except json.JSONDecodeError as fix_error:
                print(f"{CyberCLI.RED}❌ Could not fix JSON issues: {fix_error}{CyberCLI.END}")
                # Save as text file if all fixes fail
                optimized_filename = os.path.join(output_dir, "tf-ai-permissions-ai-powered.txt")
                with open(optimized_filename, "w", encoding="utf-8") as f:
                    f.write(optimized_policy_json)
                print(
                    f"{CyberCLI.CYAN}📄 File: {os.path.basename(optimized_filename)} (raw text format){CyberCLI.END}"
                )
                print(
                    f"{CyberCLI.YELLOW}⚠️  Please review and manually convert to JSON if needed{CyberCLI.END}"
                )

        # Also generate the optimization report
        optimization_report_filename = os.path.join(
            output_dir, "tf-ai-permissions-optimization-report.md"
        )

        with open(optimization_report_filename, "w", encoding="utf-8") as f:
            f.write("# TFIAM AI Optimization Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Directory:** {directory}\n\n")

            f.write("## Analysis Summary\n\n")
            f.write(verification_result.get("raw_analysis", ""))
            f.write("\n\n")

            f.write("## Generated Optimized Policy\n\n")
            f.write("The AI has generated an optimized IAM policy based on the analysis above.\n\n")
            f.write("### Key Optimizations Applied:\n")
            f.write("- Applied principle of least privilege\n")
            f.write("- Used specific resource ARNs where possible\n")
            f.write("- Removed unnecessary permissions\n")
            f.write("- Grouped related permissions efficiently\n")
            f.write("- Followed AWS security best practices\n\n")

            f.write("### Files Generated:\n")
            f.write(f"- `tf-ai-permissions-ai-powered.json` - Optimized IAM policy\n")
            f.write(f"- `tf-ai-permissions.json` - Original policy for comparison\n\n")

            f.write("## Next Steps\n\n")
            f.write("1. Review the optimized policy carefully\n")
            f.write("2. Test in a development environment\n")
            f.write("3. Compare with your original policy\n")
            f.write("4. Apply the optimized policy to your infrastructure\n")
            f.write("5. Monitor for any permission issues\n\n")

            f.write("*Generated by TFIAM AI Optimization Engine*\n")

        report_size = os.path.getsize(optimization_report_filename)
        print(
            f"{CyberCLI.CYAN}📄 Report: {os.path.basename(optimization_report_filename)} ({report_size:,} bytes){CyberCLI.END}"
        )

    except Exception as e:
        print(f"{CyberCLI.RED}❌ Optimization failed: {e}{CyberCLI.END}")
        print(
            f"{CyberCLI.YELLOW}Your original policy is still valid and ready for use.{CyberCLI.END}"
        )


def _format_statements_for_ai(statements):
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


def _extract_json_from_response(response_text):
    """Extract JSON from AI response, handling markdown formatting and incomplete responses."""
    import json

    # Remove markdown code blocks
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        if end > start:
            response_text = response_text[start:end]
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        if end > start:
            response_text = response_text[start:end]

    # Find JSON object boundaries
    start_brace = response_text.find("{")

    if start_brace != -1:
        response_text = response_text[start_brace:]

        # Try to find a complete JSON object
        brace_count = 0
        in_string = False
        escape_next = False
        end_pos = -1

        for i, char in enumerate(response_text):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break

        if end_pos != -1:
            # Found complete JSON
            response_text = response_text[: end_pos + 1]
        else:
            # Try to complete the JSON
            response_text = _complete_incomplete_json(response_text)

    return response_text.strip()


def _fix_json_formatting(json_text):
    """Fix common JSON formatting issues."""
    import re

    # Remove trailing commas before closing braces/brackets
    json_text = re.sub(r",(\s*[}\]])", r"\1", json_text)

    # Fix missing commas between array elements
    json_text = re.sub(r'"\s*\n\s*"', '",\n    "', json_text)

    # Fix missing commas between object properties
    json_text = re.sub(r'"\s*\n\s*"([A-Za-z])', r'",\n    "\1', json_text)

    # Ensure proper indentation
    lines = json_text.split("\n")
    fixed_lines = []
    indent_level = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append("")
            continue

        # Adjust indent level based on braces/brackets
        if stripped.startswith("}") or stripped.startswith("]"):
            indent_level = max(0, indent_level - 1)

        # Apply proper indentation
        indent = "  " * indent_level
        fixed_lines.append(indent + stripped)

        # Increase indent for opening braces/brackets
        if stripped.endswith("{") or stripped.endswith("["):
            indent_level += 1

    return "\n".join(fixed_lines)


def _complete_incomplete_json(json_text):
    """Complete an incomplete JSON response with robust parsing."""
    import re

    json_text = json_text.strip()

    # Find the last incomplete line
    lines = json_text.split("\n")

    # Look for incomplete Resource lines
    for i, line in enumerate(lines):
        if '"Resource":' in line:
            # Check if this line is incomplete
            line_stripped = line.strip()
            if line_stripped.endswith('"') and not line_stripped.endswith('",'):
                # Complete Resource line
                if not line_stripped.endswith('",'):
                    lines[i] = line.rstrip() + '",'
            elif not line_stripped.endswith('"') and not line_stripped.endswith('",'):
                # Incomplete Resource ARN
                lines[i] = line.rstrip() + ':*"'

    # Remove trailing commas from the last statement
    if lines:
        last_line = lines[-1].strip()
        if last_line.endswith(","):
            lines[-1] = lines[-1].rstrip(",")

    json_text = "\n".join(lines)

    # Count braces to determine what needs to be closed
    open_braces = json_text.count("{")
    close_braces = json_text.count("}")
    open_brackets = json_text.count("[")
    close_brackets = json_text.count("]")

    # Add missing closing brackets/braces
    if not json_text.endswith("}"):
        # Add statement closing if needed
        if not json_text.endswith("    }"):
            json_text += "\n    }"

        # Add array closing if needed
        if open_brackets > close_brackets:
            json_text += "\n  ]"

        # Add object closing if needed
        if open_braces > close_braces:
            json_text += "\n}"

    return json_text


def save_key_to_profile(key):
    """Save OpenAI API key to shell profile."""
    from src.tfiam.cli.cyber_cli import CyberCLI

    shell = os.environ.get("SHELL", "/bin/bash")
    print(f"{CyberCLI.CYAN}Detected shell: {shell}{CyberCLI.END}")

    # Determine profile file based on shell
    profile_file = None
    if shell.endswith("/zsh") or "zsh" in shell:
        profile_file = os.path.expanduser("~/.zshrc")
        print(f"{CyberCLI.CYAN}Using zsh profile: {profile_file}{CyberCLI.END}")
    elif shell.endswith("/bash") or "bash" in shell:
        profile_file = os.path.expanduser("~/.bashrc")
        print(f"{CyberCLI.CYAN}Using bash profile: {profile_file}{CyberCLI.END}")
    else:
        # Default to .bashrc for most systems
        profile_file = os.path.expanduser("~/.bashrc")
        print(f"{CyberCLI.CYAN}Using default profile: {profile_file}{CyberCLI.END}")

    # Check if key already exists in profile
    try:
        with open(profile_file, "r") as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                print(
                    f"{CyberCLI.YELLOW}⚠️  OpenAI API key already exists in {profile_file}{CyberCLI.END}"
                )
                print(
                    f"{CyberCLI.CYAN}The key should be available in new terminal sessions.{CyberCLI.END}"
                )
                return
    except FileNotFoundError:
        print(f"{CyberCLI.CYAN}Profile file not found, will create: {profile_file}{CyberCLI.END}")

    # Add key to profile
    export_line = f'\n# OpenAI API Key for TFIAM\nexport OPENAI_API_KEY="{key}"\n'
    try:
        with open(profile_file, "a") as f:
            f.write(export_line)
        print(f"{CyberCLI.GREEN}✅ OpenAI API key saved to {profile_file}{CyberCLI.END}")
        print(f"{CyberCLI.CYAN}📝 Added to profile: {os.path.basename(profile_file)}{CyberCLI.END}")
        print(
            f"{CyberCLI.YELLOW}⚠️  Please run one of these commands to reload your profile:{CyberCLI.END}"
        )
        if "zsh" in shell:
            print(f"{CyberCLI.CYAN}   source ~/.zshrc{CyberCLI.END}")
        else:
            print(f"{CyberCLI.CYAN}   source ~/.bashrc{CyberCLI.END}")
        print(
            f"{CyberCLI.GRAY}   Or restart your terminal for the key to take effect.{CyberCLI.END}"
        )
    except Exception as e:
        print(f"{CyberCLI.RED}❌ Failed to save key to {profile_file}: {e}{CyberCLI.END}")
        print(f"{CyberCLI.YELLOW}You can manually add this line to your profile:{CyberCLI.END}")
        print(f'{CyberCLI.CYAN}export OPENAI_API_KEY="{key}"{CyberCLI.END}')


def check_terraform_files(directory):
    """Check if directory contains Terraform files (only in the specified directory, not subdirectories)."""
    tf_files = []
    try:
        files = os.listdir(directory)
        for file in files:
            if file.endswith(".tf") and os.path.isfile(os.path.join(directory, file)):
                tf_files.append(file)
    except OSError:
        pass  # Directory doesn't exist or can't be accessed
    return tf_files


def interactive_mode():
    """Interactive mode when no arguments are provided."""
    CyberCLI.print_header()

    print(f"{CyberCLI.CYAN}🌐 Welcome to TFIAM Interactive Mode!{CyberCLI.END}")
    print(
        f"{CyberCLI.GRAY}Let's analyze your Terraform configuration and generate IAM policies.{CyberCLI.END}\n"
    )

    # Get directory
    while True:
        directory = input(
            f"{CyberCLI.CYAN}📁 Enter the path to your Terraform directory (use . for current directory): {CyberCLI.END}"
        ).strip()
        if not directory:
            print(f"{CyberCLI.RED}Please enter a directory path.{CyberCLI.END}")
            continue

        if not os.path.isdir(directory):
            print(
                f"{CyberCLI.RED}Directory '{directory}' does not exist. Please try again.{CyberCLI.END}"
            )
            continue

        # Check if directory contains .tf files
        tf_files = check_terraform_files(directory)

        if not tf_files:
            print(f"\n{CyberCLI.RED}❌ No Terraform files found in '{directory}'{CyberCLI.END}")
            print(
                f"{CyberCLI.YELLOW}TFIAM requires .tf files to analyze AWS resources.{CyberCLI.END}"
            )
            print(
                f"{CyberCLI.GRAY}Please ensure your directory contains Terraform configuration files.{CyberCLI.END}"
            )
            print(
                f"\n{CyberCLI.CYAN}Would you like to try a different directory? (y/n): {CyberCLI.END}",
                end="",
            )
            if input().lower() not in ["y", "yes"]:
                print(f"{CyberCLI.YELLOW}Exiting...{CyberCLI.END}")
                sys.exit(1)
            continue

        print(
            f"{CyberCLI.GREEN}✅ Found {len(tf_files)} Terraform file(s) in '{directory}'{CyberCLI.END}"
        )
        break

    # Get AI preference
    print(f"\n{CyberCLI.CYAN}🤖 AI Analysis Options:{CyberCLI.END}")
    print(
        f"{CyberCLI.GRAY}1. Enable AI explanations + verification & optimization (requires OpenAI API key){CyberCLI.END}"
    )
    print(f"{CyberCLI.GRAY}2. Skip AI analysis (faster, basic explanations){CyberCLI.END}")

    while True:
        choice = input(f"{CyberCLI.CYAN}Choose an option (1 or 2): {CyberCLI.END}").strip()
        if choice == "1":
            use_ai = True
            break
        elif choice == "2":
            use_ai = False
            break
        else:
            print(f"{CyberCLI.RED}Please enter 1 or 2.{CyberCLI.END}")

    # Ask about cache clearing if AI is enabled
    clear_cache = False
    if use_ai:
        print(f"\n{CyberCLI.CYAN}💾 Cache Management:{CyberCLI.END}")
        print(
            f"{CyberCLI.GRAY}TFIAM caches AI responses to save costs. If you've made significant changes to your Terraform code,{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GRAY}you may want to clear the cache to get fresh AI analysis (this will incur extra costs).{CyberCLI.END}"
        )

        while True:
            clear_choice = (
                input(f"{CyberCLI.CYAN}Would you like to clear the AI cache? (y/n): {CyberCLI.END}")
                .strip()
                .lower()
            )
            if clear_choice in ["y", "yes"]:
                clear_cache = True
                print(
                    f"{CyberCLI.YELLOW}⚠️  Cache will be cleared - fresh AI analysis will be generated{CyberCLI.END}"
                )
                break
            elif clear_choice in ["n", "no"]:
                clear_cache = False
                print(f"{CyberCLI.GREEN}✅ Using cached responses where available{CyberCLI.END}")
                break
            else:
                print(f"{CyberCLI.RED}Please enter 'y' for yes or 'n' for no.{CyberCLI.END}")

    # Get output directory
    output_dir = input(
        f"{CyberCLI.CYAN}📂 Output directory (press Enter for 'tfiam-output'): {CyberCLI.END}"
    ).strip()
    if not output_dir:
        output_dir = "tfiam-output"

    # Get quiet mode preference
    quiet = input(f"{CyberCLI.CYAN}🔇 Quiet mode? (y/n): {CyberCLI.END}").lower() in ["y", "yes"]

    return {
        "directory": directory,
        "use_ai": use_ai,
        "clear_cache": clear_cache,
        "output_dir": output_dir,
        "quiet": quiet,
    }


def show_future_usage(directory, use_ai, output_dir, quiet):
    """Show how to use the same command in the future."""
    print(f"\n{CyberCLI.GREEN}💡 Future Usage:{CyberCLI.END}")
    print(f"{CyberCLI.GRAY}You can run the same analysis with this command:{CyberCLI.END}")

    # Build command
    cmd_parts = ["python main.py", directory]

    if use_ai:
        cmd_parts.append("-ai")
    else:
        cmd_parts.append("-no-ai")

    if output_dir != "tfiam-output":
        cmd_parts.extend(["--output-dir", output_dir])

    if quiet:
        cmd_parts.append("--quiet")

    command = " ".join(cmd_parts)
    print(f"{CyberCLI.CYAN}{CyberCLI.BOLD}{command}{CyberCLI.END}")

    # Show AI key info if applicable
    if use_ai:
        if os.getenv("OPENAI_API_KEY"):
            print(f"\n{CyberCLI.GREEN}✅ OpenAI API key is saved in your environment{CyberCLI.END}")
        else:
            print(
                f"\n{CyberCLI.YELLOW}⚠️  You'll need to provide your OpenAI API key each time{CyberCLI.END}"
            )


def main():
    """Main entry point for TFIAM."""
    # Fix working directory for Homebrew installation
    original_working_dir = os.getenv("ORIGINAL_WORKING_DIR")
    if original_working_dir and os.path.exists(original_working_dir):
        os.chdir(original_working_dir)

    # Handle help before parsing arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        print_cyberpunk_help()
        return

    # Check if no arguments provided (interactive mode)
    if len(sys.argv) == 1:
        try:
            config = interactive_mode()
            directory = config["directory"]
            use_ai = config["use_ai"]
            clear_cache = config["clear_cache"]
            output_dir = config["output_dir"]
            quiet = config["quiet"]
        except KeyboardInterrupt:
            print(f"\n{CyberCLI.YELLOW}Operation cancelled by user.{CyberCLI.END}")
            return
    else:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="TFIAM - Analyze Terraform repositories and generate IAM permission recommendations",
            add_help=False,  # Disable default help to use our custom one
        )
        parser.add_argument("directory", help="Path to Terraform repository directory")
        parser.add_argument("-ai", action="store_true", help="Enable AI explanations")
        parser.add_argument("-no-ai", action="store_true", help="Skip AI explanations (default)")
        parser.add_argument(
            "--output-dir",
            "-o",
            default="tfiam-output",
            help="Output directory for generated files (default: tfiam-output)",
        )
        parser.add_argument(
            "--quiet", "-q", action="store_true", help="Quiet mode - minimal output"
        )

        args = parser.parse_args()

        directory = args.directory
        use_ai = args.ai
        clear_cache = False  # Command line mode doesn't support cache clearing for now
        output_dir = args.output_dir
        quiet = args.quiet

    # Validate directory
    if not os.path.isdir(directory):
        print(
            f"{CyberCLI.RED}Error: Directory {directory} does not exist{CyberCLI.END}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if directory contains Terraform files
    tf_files = check_terraform_files(directory)
    if not tf_files:
        print(
            f"{CyberCLI.RED}❌ No Terraform files found in '{directory}'{CyberCLI.END}",
            file=sys.stderr,
        )
        print(
            f"{CyberCLI.YELLOW}TFIAM requires .tf files to analyze AWS resources.{CyberCLI.END}",
            file=sys.stderr,
        )
        print(
            f"{CyberCLI.GRAY}Please ensure your directory contains Terraform configuration files.{CyberCLI.END}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Display header unless in quiet mode
    if not quiet:
        CyberCLI.print_header()
        print(f"{CyberCLI.CYAN}🔍 Scanning Terraform directory: {directory}{CyberCLI.END}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize analyzer
    analyzer = TerraformAnalyzer()

    # Scan directory
    if not quiet:
        print(f"{CyberCLI.CYAN}🔍 Scanning Terraform files...{CyberCLI.END}")

    analyzer.scan_directory(directory)

    # Check if any resources were found
    if len(analyzer.resources) == 0:
        print(f"{CyberCLI.RED}❌ No AWS resources found in '{directory}'{CyberCLI.END}")
        print(
            f"{CyberCLI.YELLOW}No .tf files with AWS resources were found in the specified directory.{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GRAY}Make sure the directory contains Terraform configuration files with AWS resources.{CyberCLI.END}"
        )
        sys.exit(1)

    if not quiet:
        print(
            f"{CyberCLI.GREEN}✅ Found {len(analyzer.resources)} AWS resources across {len(analyzer.aws_services)} services{CyberCLI.END}"
        )
        print(f"{CyberCLI.CYAN}⚙️  Generating IAM permissions...{CyberCLI.END}")

    # Generate permissions
    statements = analyzer.generate_permissions()

    if not quiet:
        print(f"{CyberCLI.GREEN}✅ Generated {len(statements)} IAM policy statements{CyberCLI.END}")

    # OpenAI enhancement
    openai_enabled = False
    if use_ai:
        try:
            openai_key = get_openai_key()
            if not quiet:
                print(
                    f"\n{CyberCLI.MAGENTA}🤖 Starting AI analysis of {len(statements)} statements...{CyberCLI.END}"
                )
                print(
                    f"{CyberCLI.GRAY}This may take a moment as we analyze each IAM statement.{CyberCLI.END}"
                )

            openai_analyzer = OpenAIAnalyzer(openai_key)

            # Clear cache if requested
            if clear_cache:
                if not quiet:
                    print(f"{CyberCLI.YELLOW}🗑️  Clearing AI cache...{CyberCLI.END}")
                openai_analyzer.cache.clear()
                if not quiet:
                    print(f"{CyberCLI.GREEN}✅ Cache cleared{CyberCLI.END}")

            # Process statements with progress tracking
            if not quiet:
                print(f"{CyberCLI.CYAN}📊 Processing statements:{CyberCLI.END}")

            statements = openai_analyzer.enhance_statements_with_progress(statements, quiet)
            openai_enabled = True

            if not quiet:
                print(
                    f"\n{CyberCLI.GREEN}✅ Successfully enhanced {len(statements)} statements with AI explanations{CyberCLI.END}"
                )

                # Display cache statistics
                cache_stats = openai_analyzer.get_cache_stats()
                if cache_stats["total_requests"] > 0:
                    print(f"\n{CyberCLI.CYAN}📦 Cache Statistics:{CyberCLI.END}")
                    print(
                        f"  Cache hits: {cache_stats['cache_hits']} ({cache_stats['hit_rate']:.1f}%)"
                    )
                    print(f"  Cache misses: {cache_stats['cache_misses']}")
                    print(f"  Total cached responses: {cache_stats['cache_size']}")
                    if cache_stats["hit_rate"] > 0:
                        print(
                            f"  💰 Cost savings: ~${cache_stats['cache_hits'] * 0.002:.3f} (estimated)"
                        )

            # Perform policy verification and optimization
            verification_result = None
            try:
                # Read all Terraform files to get combined content
                terraform_content = ""
                for tf_file in check_terraform_files(directory):
                    file_path = os.path.join(directory, tf_file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            terraform_content += f.read() + "\n\n"
                    except Exception:
                        pass  # Skip files that can't be read

                verification_result = openai_analyzer.verify_and_optimize_policy(
                    statements, analyzer.resources, terraform_content, quiet
                )

                if not quiet and verification_result:
                    _display_verification_results(verification_result)

            except Exception as e:
                if not quiet:
                    print(
                        f"{CyberCLI.YELLOW}Warning: Policy verification failed: {e}{CyberCLI.END}"
                    )
                verification_result = None
        except Exception as e:
            print(f"{CyberCLI.YELLOW}Warning: OpenAI enhancement failed: {e}{CyberCLI.END}")
            if not quiet:
                print(f"{CyberCLI.YELLOW}Falling back to default explanations{CyberCLI.END}")

    # Generate output filename - always use repository name
    json_filename = os.path.join(output_dir, "tf-ai-permissions.json")

    # Prepare metadata
    analysis_metadata = {
        "terraform_directory": directory,
        "services_count": len(analyzer.aws_services),
        "services": list(analyzer.aws_services),
        "resources_count": len(analyzer.resources),
        "statements_count": len(statements),
        "permissions_count": sum(len(stmt.action) for stmt in statements),
        "openai_enabled": openai_enabled,
    }

    # Add verification results to metadata if available
    if openai_enabled and "verification_result" in locals() and verification_result:
        analysis_metadata["verification_results"] = {
            "verification_passed": verification_result.get("verification_passed", False),
            "security_score": verification_result.get("policy_statistics", {}).get(
                "security_score", 0
            ),
            "complexity_score": verification_result.get("terraform_statistics", {}).get(
                "complexity_score", 0
            ),
            "recommendations_count": sum(
                len(v)
                for v in verification_result.get("recommendations", {}).values()
                if isinstance(v, list)
            ),
        }

    # Save policy
    if not quiet:
        print(f"{CyberCLI.CYAN}💾 Saving IAM policy to JSON...{CyberCLI.END}")

    policy_size = PolicyGenerator.save_policy_clean(statements, analysis_metadata, json_filename)

    # Save markdown report if OpenAI was used
    files_info = []
    files_info.append(
        {
            "name": os.path.basename(json_filename),
            "size": policy_size,
            "description": "IAM Policy (JSON format)",
        }
    )

    if openai_enabled:
        if not quiet:
            print(f"{CyberCLI.CYAN}📝 Generating detailed AI analysis report...{CyberCLI.END}")

        md_filename = os.path.join(output_dir, "tf-ai-permissions-report.md")

        # Include verification results in markdown report if available
        enhanced_metadata = analysis_metadata.copy()
        if "verification_result" in locals() and verification_result:
            enhanced_metadata["verification_analysis"] = verification_result.get("raw_analysis", "")
            enhanced_metadata["verification_recommendations"] = verification_result.get(
                "recommendations", {}
            )
            enhanced_metadata["verification_passed"] = verification_result.get(
                "verification_passed", False
            )
            enhanced_metadata["policy_statistics"] = verification_result.get(
                "policy_statistics", {}
            )
            enhanced_metadata["terraform_statistics"] = verification_result.get(
                "terraform_statistics", {}
            )

        md_size = PolicyGenerator.save_markdown_report(statements, enhanced_metadata, md_filename)
        files_info.append(
            {
                "name": os.path.basename(md_filename),
                "size": md_size,
                "description": "Detailed Analysis Report with Verification (Markdown)",
            }
        )

    # Display summary
    if not quiet:
        summary_stats = {
            "services_count": len(analyzer.aws_services),
            "statements_count": len(statements),
            "permissions_count": sum(len(stmt.action) for stmt in statements),
            "output_files": len(files_info),
            "openai_enabled": openai_enabled,
            "files": files_info,
        }
        CyberCLI.print_summary(summary_stats)

        # Add optimization prompt if AI was enabled
        if openai_enabled and "verification_result" in locals() and verification_result:
            _show_optimization_prompt(
                verification_result,
                openai_analyzer,
                statements,
                analyzer.resources,
                directory,
                output_dir,
                quiet,
            )

        # Show future usage if in interactive mode
        if len(sys.argv) == 1:
            show_future_usage(directory, use_ai, output_dir, quiet)
    else:
        print(f"Analysis complete. Policy generated: {json_filename}")


if __name__ == "__main__":
    main()
