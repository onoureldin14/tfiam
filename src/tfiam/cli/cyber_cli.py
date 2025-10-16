"""Cyberpunk-themed CLI interface for TFIAM."""

from typing import Any, Dict


class CyberCLI:
    """Cyberpunk-themed CLI display utilities."""

    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    END = "\033[0m"

    @staticmethod
    def print_header():
        """Print the cyberpunk header."""
        print(f"{CyberCLI.CYAN}{CyberCLI.BOLD}")
        print("╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                              ║")
        print("║    ████████╗███████╗██╗ █████╗ ███╗   ███╗                                  ║")
        print("║    ╚══██╔══╝██╔════╝██║██╔══██╗████╗ ████║                                  ║")
        print("║       ██║   █████╗  ██║███████║██╔████╔██║                                  ║")
        print("║       ██║   ██╔══╝  ██║██╔══██║██║╚██╔╝██║                                  ║")
        print("║       ██║   ███████╗██║██║  ██║██║ ╚═╝ ██║                                  ║")
        print("║       ╚═╝   ╚══════╝╚═╝╚═╝  ╚═╝╚═╝     ╚═╝                                  ║")
        print("║                                                                              ║")
        print("║                    🌐 TERRAFORM IAM ANALYZER 🌐                             ║")
        print("║                                                                              ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")
        print(f"{CyberCLI.END}\n")

    @staticmethod
    def print_summary(stats: Dict[str, Any]):
        """Print final summary."""
        print(
            f"\n{CyberCLI.GREEN}{CyberCLI.BOLD}╔══════════════════════════════════════════════════════════════════════════════╗{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║                           {CyberCLI.WHITE}ANALYSIS COMPLETE{CyberCLI.GREEN}                           ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}╠══════════════════════════════════════════════════════════════════════════════╣{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║                                                                              ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║  {CyberCLI.WHITE}Services Analyzed:     {CyberCLI.CYAN}{stats['services_count']:>3}{CyberCLI.GREEN}                                    ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║  {CyberCLI.WHITE}IAM Statements:        {CyberCLI.CYAN}{stats['statements_count']:>3}{CyberCLI.GREEN}                                    ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║  {CyberCLI.WHITE}Total Permissions:     {CyberCLI.CYAN}{stats['permissions_count']:>3}{CyberCLI.GREEN}                                    ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║  {CyberCLI.WHITE}Output Files:          {CyberCLI.CYAN}{stats['output_files']:>3}{CyberCLI.GREEN}                                    ║{CyberCLI.END}"
        )
        ai_status = "✓ Enabled" if stats.get("openai_enabled", False) else "✗ Disabled"
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║  {CyberCLI.WHITE}AI Analysis:           {CyberCLI.CYAN}{ai_status:<10}{CyberCLI.GREEN}                                    ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}║                                                                              ║{CyberCLI.END}"
        )
        print(
            f"{CyberCLI.GREEN}{CyberCLI.BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{CyberCLI.END}"
        )

        print(f"\n{CyberCLI.CYAN}{CyberCLI.BOLD}📁 OUTPUT FILES:{CyberCLI.END}")
        for file_info in stats["files"]:
            size_kb = file_info["size"] / 1024
            print(
                f"{CyberCLI.YELLOW}├─{CyberCLI.END} {CyberCLI.WHITE}{file_info['name']}{CyberCLI.END} {CyberCLI.CYAN}({size_kb:.1f}KB){CyberCLI.END}"
            )
            print(f"{CyberCLI.YELLOW}│  {CyberCLI.GRAY}→ {file_info['description']}{CyberCLI.END}")

        print(
            f"\n{CyberCLI.GREEN}{CyberCLI.BOLD}✅ Mission Complete! Your IAM policies are ready for deployment.{CyberCLI.END}\n"
        )


def print_cyberpunk_help():
    """Print cyberpunk-themed help message."""
    print(f"{CyberCLI.CYAN}{CyberCLI.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                           🌐 TFIAM HELP MATRIX 🌐                          ║")
    print("╠══════════════════════════════════════════════════════════════════════════════╣")
    print("║                                                                              ║")
    print("║  USAGE:                                                                      ║")
    print("║    tfiam <directory> [OPTIONS]                                              ║")
    print("║                                                                              ║")
    print("║  ARGUMENTS:                                                                  ║")
    print("║    directory          Path to Terraform repository                          ║")
    print("║                                                                              ║")
    print("║  OPTIONS:                                                                   ║")
    print("║    -ai                Enable AI explanations (requires OpenAI API key)     ║")
    print("║    -no-ai             Skip AI analysis (default)                           ║")
    print("║    --output-dir DIR   Output directory (default: tfiam-output)              ║")
    print("║    --quiet, -q        Minimal output                                       ║")
    print("║    --help, -h         Show this help message                               ║")
    print("║                                                                              ║")
    print("║  INTERACTIVE MODE:                                                          ║")
    print("║    Run without arguments for guided setup                                  ║")
    print("║                                                                              ║")
    print("║  EXAMPLES:                                                                  ║")
    print("║    python main.py                                                           ║")
    print("║    python main.py ./my-terraform -ai                                        ║")
    print("║    python main.py ./infra -no-ai --output-dir policies                     ║")
    print("║                                                                              ║")
    print("║  🌟 TFIAM analyzes Terraform files and generates IAM policies with        ║")
    print("║     comprehensive AWS permissions and AI-powered explanations!             ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{CyberCLI.END}")
