"""
Stored Procedure Java Tracer Utility Script

Date: 2026-01-29
"""

import subprocess
import os
import sys
import configparser
import json
import shutil
from pathlib import Path


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

# Load configuration from config.ini
CONFIG_FILE = SCRIPT_DIR / "Core" / "Python" / "config.ini"
config = configparser.ConfigParser()

# Check if config file exists
if not CONFIG_FILE.exists():
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Core/Python directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values (only what CLI needs for display/validation)
try:
    # Paths
    PROJECT_BASE_DIR = Path(config.get('Paths', 'project_base_dir'))
    OUTPUT_DIR = Path(config.get('Paths', 'output_dir'))
    LOG_DIR = Path(config.get('Paths', 'log_dir'))
    CORE_DIR = SCRIPT_DIR / "Core" / "Python"

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)


# ============================================================================
# FUNCTIONS
# ============================================================================

def print_header(step_num, title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}: {title}")
    print("=" * 80 + "\n")


def step1_extract_ui_mapping():
    """
    STEP 1: Extract Complete UI Mapping

    Calls the separate 01_extract_complete_ui_mapping.py script
    """
    script = CORE_DIR / "01_extract_complete_ui_mapping.py"

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False


def step2_generate_dependency_report():
    """
    STEP 2: Generate Dependency Report

    Calls the separate 02_generate_dependency_report.py script
    """
    script = CORE_DIR / "02_generate_dependency_report.py"

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False


def step3_create_final_ui_mappings():
    """
    STEP 3: Create Final UI Mappings

    Calls the separate 03_create_final_ui_mappings.py script
    """
    script = CORE_DIR / "03_create_final_ui_mappings.py"

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False

def run_complete_analysis():
    """
    Execute all three steps in sequence with user confirmation
    """
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}🚀 RUN COMPLETE ANALYSIS{Colors.RESET}")
    print("=" * 80)

    # Display configuration summary
    print(f"\n{Colors.CYAN}Configuration Summary:{Colors.RESET}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    print(f"  Log Directory:    {LOG_DIR}")
    print(f"  Core Scripts:     {CORE_DIR}")

    print(f"\n{Colors.YELLOW}This will execute all three steps in sequence:{Colors.RESET}")
    print("  1. Extract Complete UI Mapping")
    print("  2. Generate Dependency Report")
    print("  3. Create Final UI Mappings")

    # Ask for confirmation
    confirm = input(f"\n{Colors.BOLD}Do you want to proceed? (y/n): {Colors.RESET}").strip().lower()

    if confirm != 'y':
        print(f"\n{Colors.YELLOW}❌ Operation cancelled.{Colors.RESET}")
        input("\nPress any key to continue...")
        return

    print(f"\n{Colors.CYAN}Starting analysis...{Colors.RESET}")
    print("(Check log files for detailed output)\n")

    # Execute steps and track results
    results = []

    # Step 1
    print(f"{Colors.CYAN}[1/3] Extracting UI Mapping...{Colors.RESET}")
    step1_success = step1_extract_ui_mapping()
    results.append(("Step 1: Extract UI Mapping", step1_success))

    # Step 2 (only if Step 1 succeeded)
    if step1_success:
        print(f"{Colors.CYAN}[2/3] Generating Dependency Report...{Colors.RESET}")
        step2_success = step2_generate_dependency_report()
        results.append(("Step 2: Generate Dependency Report", step2_success))
    else:
        print(f"{Colors.RED}[2/3] Skipping (Step 1 failed){Colors.RESET}")
        results.append(("Step 2: Generate Dependency Report", False))
        step2_success = False

    # Step 3 (only if Step 2 succeeded)
    if step2_success:
        print(f"{Colors.CYAN}[3/3] Creating Final UI Mappings...{Colors.RESET}")
        step3_success = step3_create_final_ui_mappings()
        results.append(("Step 3: Create Final UI Mappings", step3_success))
    else:
        print(f"{Colors.RED}[3/3] Skipping (Step 2 failed){Colors.RESET}")
        results.append(("Step 3: Create Final UI Mappings", False))

    # Display summary
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}EXECUTION SUMMARY{Colors.RESET}")
    print("=" * 80)

    all_success = True
    for step_name, success in results:
        if success:
            print(f"  {Colors.GREEN}✅ {step_name}{Colors.RESET}")
        else:
            print(f"  {Colors.RED}❌ {step_name}{Colors.RESET}")
            all_success = False

    print("\n" + "=" * 80)

    if all_success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All steps completed successfully!{Colors.RESET}")
        print(f"\n{Colors.CYAN}Output files are located in:{Colors.RESET}")
        print(f"  {OUTPUT_DIR}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some steps failed.{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please check the log files for details:{Colors.RESET}")
        print(f"  {LOG_DIR}")

    input("\nPress any key to continue...")


def open_output_folder():
    """Open the Output folder in Windows Explorer"""
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}📂 OPEN OUTPUT FOLDER{Colors.RESET}")
    print("=" * 80)

    print(f"\n📁 Opening: {OUTPUT_DIR}")

    try:
        subprocess.run(['explorer', str(OUTPUT_DIR)])
        print(f"\n{Colors.GREEN}✅ Output folder opened{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: Could not open Output folder: {e}{Colors.RESET}")

    input("\nPress any key to continue...")


def open_logs_folder():
    """Open the Logs folder in Windows Explorer"""
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}📋 OPEN LOGS FOLDER{Colors.RESET}")
    print("=" * 80)

    print(f"\n📁 Opening: {LOG_DIR}")

    try:
        subprocess.run(['explorer', str(LOG_DIR)])
        print(f"\n{Colors.GREEN}✅ Logs folder opened{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: Could not open Logs folder: {e}{Colors.RESET}")

    input("\nPress any key to continue...")


def open_stored_procedures_input():
    """Open the Stored Procedures Input.txt file for editing"""
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}📝 OPEN STORED PROCEDURES INPUT{Colors.RESET}")
    print("=" * 80)

    input_file = PROJECT_BASE_DIR / "Config" / "Stored Procedures Input.txt"

    print(f"\n📄 Opening: {input_file}")
    print(f"\n{Colors.YELLOW}Note: The file will open in your default text editor.{Colors.RESET}")
    print(f"{Colors.YELLOW}      Make your changes and save the file before running the analysis.{Colors.RESET}")

    try:
        # Use 'start' command to open with default text editor
        subprocess.run(['cmd', '/c', 'start', '', str(input_file)], shell=True)
        print(f"\n{Colors.GREEN}✅ File opened in default text editor{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: Could not open file: {e}{Colors.RESET}")


def cleanup_files():
    """Clean up log files and output files based on cleanup_config.json"""
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}🗑️ CLEANUP FILES{Colors.RESET}")
    print("=" * 80)

    cleanup_config_file = PROJECT_BASE_DIR / "Config" / "cleanup_config.json"

    # Check if cleanup config file exists
    if not cleanup_config_file.exists():
        print(f"\n{Colors.RED}❌ ERROR: Cleanup configuration file not found:{Colors.RESET}")
        print(f"  {cleanup_config_file}")
        input("\nPress any key to continue...")
        return

    try:
        # Read cleanup configuration
        with open(cleanup_config_file, 'r') as f:
            cleanup_config = json.load(f)

        operations = cleanup_config.get('cleanup_operations', [])

        if not operations:
            print(f"\n{Colors.YELLOW}⚠️  No cleanup operations defined in configuration file.{Colors.RESET}")
            input("\nPress any key to continue...")
            return

        # Display operations
        print(f"\n{Colors.CYAN}The following items will be deleted:{Colors.RESET}")
        for i, operation in enumerate(operations, 1):
            print(f"\n  {i}. {operation.get('description', 'Unknown')}")
            print(f"     Path: {operation.get('path', 'Unknown')}")

        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  WARNING: This action cannot be undone!{Colors.RESET}")

        # Ask for confirmation
        confirm = input(f"\n{Colors.BOLD}Do you want to proceed? (y/n): {Colors.RESET}").strip().lower()

        if confirm != 'y':
            print(f"\n{Colors.YELLOW}❌ Cleanup cancelled.{Colors.RESET}")
            input("\nPress any key to continue...")
            return

        # Perform cleanup operations
        print(f"\n{Colors.CYAN}Starting cleanup...{Colors.RESET}\n")

        for operation in operations:
            path = operation.get('path', '')
            description = operation.get('description', 'Unknown')
            action = operation.get('action', '')

            if action == 'delete_folder':
                folder_path = Path(path)

                if folder_path.exists():
                    try:
                        shutil.rmtree(folder_path)
                        print(f"  {Colors.GREEN}✅ Deleted: {description}{Colors.RESET}")
                        print(f"     Path: {path}")
                    except Exception as e:
                        print(f"  {Colors.RED}❌ Failed to delete: {description}{Colors.RESET}")
                        print(f"     Path: {path}")
                        print(f"     Error: {e}")
                else:
                    print(f"  {Colors.YELLOW}ℹ️  Folder does not exist: {description}{Colors.RESET}")
                    print(f"     Path: {path}")

        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Cleanup completed!{Colors.RESET}")

    except json.JSONDecodeError as e:
        print(f"\n{Colors.RED}❌ ERROR: Invalid JSON in cleanup configuration file:{Colors.RESET}")
        print(f"  {e}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: Cleanup failed:{Colors.RESET}")
        print(f"  {e}")

    input("\nPress any key to continue...")


def main_menu():
    """Display main menu and handle user choices"""
    first_run = True

    while True:
        # Clear screen on subsequent runs
        if not first_run:
            os.system('cls' if os.name == 'nt' else 'clear')
        first_run = False

        # Display ASCII art
        ascii_art_file = CORE_DIR / "ascii_art.txt"
        if ascii_art_file.exists():
            try:
                with open(ascii_art_file, 'r', encoding='utf-8') as f:
                    ascii_art = f.read()
                print(f"\n{Colors.CYAN}{ascii_art}{Colors.RESET}")
            except Exception:
                pass  # If ASCII art fails to load, just skip it

        print("\n" + "=" * 80)
        print(f"{Colors.BLUE}{Colors.BOLD}STORED PROCEDURE JAVA TRACER UTILITY{Colors.RESET}")
        print("=" * 80)

        print(f"\n{Colors.CYAN}1. 🚀  Run Complete Analysis{Colors.RESET}")
        print("   • Executes all three steps in sequence")
        print("   • Step 1: Extract UI Mapping")
        print("   • Step 2: Generate Dependency Report")
        print("   • Step 3: Create Final UI Mappings")

        print(f"\n{Colors.CYAN}2. 📝 Edit Stored Procedures Input{Colors.RESET}")
        print("   • Opens the input file for editing")
        print("   • Modify the list of stored procedures to analyze")

        print(f"\n{Colors.CYAN}3. 📂 Open Output Folder{Colors.RESET}")
        print("   • Opens the folder containing generated reports")

        print(f"\n{Colors.CYAN}4. 📋 Open Logs Folder{Colors.RESET}")
        print("   • Opens the folder containing execution logs")

        print(f"\n{Colors.CYAN}5. 🗑️ Cleanup Files{Colors.RESET}")
        print("   • Deletes log files and output files")
        print("   • WARNING: This action cannot be undone")

        print(f"\n{Colors.CYAN}6. 🚪 Exit{Colors.RESET}")
        print("   • Closes the application")

        choice = input(f"\n{Colors.BOLD}👉 Enter your choice (1-6): {Colors.RESET}").strip()

        if choice == '1':
            run_complete_analysis()
        elif choice == '2':
            open_stored_procedures_input()
        elif choice == '3':
            open_output_folder()
        elif choice == '4':
            open_logs_folder()
        elif choice == '5':
            cleanup_files()
        elif choice == '6':
            print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.RESET}\n")
            break
        else:
            print(f"\n{Colors.RED}❌ Invalid choice. Please enter 1-6.{Colors.RESET}")
            input("\nPress any key to continue...")


def main():
    """Main entry point."""
    main_menu()


if __name__ == "__main__":
    main()
