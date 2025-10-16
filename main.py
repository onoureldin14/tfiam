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
            break
        print(f"{CyberCLI.RED}Please enter a valid API key.{CyberCLI.END}")

    # Ask if user wants to save it permanently
    save = input(
        f"{CyberCLI.CYAN}Would you like to save this key to your shell profile? (y/n): {CyberCLI.END}"
    ).lower()
    if save in ["y", "yes"]:
        save_key_to_profile(key)

    return key


def save_key_to_profile(key):
    """Save OpenAI API key to shell profile."""
    shell = os.environ.get("SHELL", "/bin/bash")

    # Determine profile file
    if "zsh" in shell:
        profile_file = os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
        profile_file = os.path.expanduser("~/.bashrc")
    else:
        profile_file = os.path.expanduser("~/.profile")

    # Check if key already exists in profile
    try:
        with open(profile_file, "r") as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                print(
                    f"{CyberCLI.YELLOW}OpenAI API key already exists in {profile_file}{CyberCLI.END}"
                )
                return
    except FileNotFoundError:
        pass

    # Add key to profile
    export_line = f'\nexport OPENAI_API_KEY="{key}"\n'
    try:
        with open(profile_file, "a") as f:
            f.write(export_line)
        print(f"{CyberCLI.GREEN}✅ OpenAI API key saved to {profile_file}{CyberCLI.END}")
        print(
            f"{CyberCLI.CYAN}Please run 'source {profile_file}' or restart your terminal to use the key.{CyberCLI.END}"
        )
    except Exception as e:
        print(f"{CyberCLI.RED}❌ Failed to save key to {profile_file}: {e}{CyberCLI.END}")


def check_terraform_files(directory):
    """Check if directory contains Terraform files."""
    tf_files = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common non-Terraform directories
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ["node_modules", "venv", "__pycache__"]
        ]
        tf_files.extend([f for f in files if f.endswith(".tf")])
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
            f"{CyberCLI.CYAN}📁 Enter the path to your Terraform directory: {CyberCLI.END}"
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
    print(f"{CyberCLI.GRAY}1. Enable AI explanations (requires OpenAI API key){CyberCLI.END}")
    print(f"{CyberCLI.GRAY}2. Skip AI explanations (faster, basic explanations){CyberCLI.END}")

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

    # Get output directory
    output_dir = input(
        f"{CyberCLI.CYAN}📂 Output directory (press Enter for 'tfiam-output'): {CyberCLI.END}"
    ).strip()
    if not output_dir:
        output_dir = "tfiam-output"

    # Get quiet mode preference
    quiet = input(f"{CyberCLI.CYAN}🔇 Quiet mode? (y/n): {CyberCLI.END}").lower() in ["y", "yes"]

    return {"directory": directory, "use_ai": use_ai, "output_dir": output_dir, "quiet": quiet}


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
    analyzer.scan_directory(directory)

    if not quiet:
        print(
            f"{CyberCLI.GREEN}✅ Found {len(analyzer.resources)} AWS resources across {len(analyzer.aws_services)} services{CyberCLI.END}"
        )

    # Generate permissions
    statements = analyzer.generate_permissions()

    # OpenAI enhancement
    openai_enabled = False
    if use_ai:
        try:
            openai_key = get_openai_key()
            openai_analyzer = OpenAIAnalyzer(openai_key)
            statements = openai_analyzer.enhance_statements(statements)
            openai_enabled = True
            if not quiet:
                print(f"{CyberCLI.MAGENTA}🤖 Enhanced statements with AI explanations{CyberCLI.END}")
        except Exception as e:
            print(f"{CyberCLI.YELLOW}Warning: OpenAI enhancement failed: {e}{CyberCLI.END}")
            if not quiet:
                print(f"{CyberCLI.YELLOW}Falling back to default explanations{CyberCLI.END}")

    # Generate output filename
    directory_name = os.path.basename(os.path.abspath(directory))
    json_filename = os.path.join(output_dir, f"{directory_name}.json")

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

    # Save policy
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
        md_filename = os.path.join(output_dir, f"{directory_name}-report.md")
        md_size = PolicyGenerator.save_markdown_report(statements, analysis_metadata, md_filename)
        files_info.append(
            {
                "name": os.path.basename(md_filename),
                "size": md_size,
                "description": "Detailed Analysis Report (Markdown)",
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

        # Show future usage if in interactive mode
        if len(sys.argv) == 1:
            show_future_usage(directory, use_ai, output_dir, quiet)
    else:
        print(f"Analysis complete. Policy generated: {json_filename}")


if __name__ == "__main__":
    main()
