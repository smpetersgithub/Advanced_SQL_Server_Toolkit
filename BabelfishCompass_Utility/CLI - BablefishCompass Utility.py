"""
BabelfishCompass Utility Script

Date: 2025-11-06
"""

import subprocess
import os
import sys
import configparser
import json
import shutil
from pathlib import Path
from datetime import datetime


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
CONFIG_FILE = SCRIPT_DIR / "Config" / "config.ini"
config = configparser.ConfigParser()

# Check if config file exists
if not CONFIG_FILE.exists():
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Config directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values (only what CLI needs for display/validation)
try:
    # Paths
    BABELFISH_DIR = SCRIPT_DIR / config.get('Paths', 'babelfish_dir')
    DEFAULT_SQL_SOURCE_DIR = SCRIPT_DIR / config.get('Paths', 'sql_examples_dir')
    SQLITE_DIR = SCRIPT_DIR / config.get('Paths', 'sqlite_dir')
    CORE_DIR = SCRIPT_DIR / config.get('Paths', 'core_dir')

    # Defaults
    DEFAULT_REPORT_NAME = config.get('Defaults', 'default_report_name')

    # BabelfishCompass (for display purposes)
    DAT_FILE_PATTERN = config.get('BabelfishCompass', 'dat_file_pattern')

    # Display
    ASCII_ART_FILE = config.get('Display', 'ascii_art_file')

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


def step1_generate_report(report_name, sql_source_dir):
    """
    STEP 1: Generate the Babelfish Compass Report

    Calls the separate 0100_Generate_BabelfishCompass_Report.py script
    """
    # Path to the 0100_Generate_BabelfishCompass_Report.py script
    report_script = CORE_DIR / "0100_Generate_BabelfishCompass_Report.py"

    # Run the report generation script
    try:
        result = subprocess.run(
            [sys.executable, str(report_script), report_name, sql_source_dir],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False


def step2_generate_dat_file(report_name):
    """
    STEP 2: Generate DAT File for Database Import

    Calls the separate 0200_Generate_DAT_File.py script
    """
    # Path to the 0200_Generate_DAT_File.py script
    dat_script = CORE_DIR / "0200_Generate_DAT_File.py"

    # Run the DAT file generation script
    try:
        result = subprocess.run(
            [sys.executable, str(dat_script), report_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False


def step3_import_to_sqlite(report_name):
    """
    STEP 3: Import DAT File into SQLite Database

    Calls the separate 0300_Import_DAT_to_SQLite.py script
    """
    # Path to the 0300_Import_DAT_to_SQLite.py script
    import_script = CORE_DIR / "0300_Import_DAT_to_SQLite.py"

    # Run the import script
    try:
        result = subprocess.run(
            [sys.executable, str(import_script), report_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def display_ascii_art():
    """Print ASCII art from config-specified file"""
    ascii_art_file = CORE_DIR / ASCII_ART_FILE
    try:
        with open(ascii_art_file, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        # If file not found, just skip the ASCII art
        pass
    except Exception as e:
        # If any other error, just skip the ASCII art
        pass


def run_report():
    """Run a single report - returns True to continue, False to exit"""

    # Prompt for report name
    print(f"\n📝 Enter report name (or press Enter for default: '{DEFAULT_REPORT_NAME}'):")
    report_name_input = input("Report name: ").strip()
    REPORT_NAME = report_name_input if report_name_input else DEFAULT_REPORT_NAME

    # Prompt for SQL source directory
    print(f"\n📁 Enter SQL source directory path (or press Enter for default):")
    print(f"Default: {DEFAULT_SQL_SOURCE_DIR}")
    sql_dir_input = input("SQL directory: ").strip()
    SQL_SOURCE_DIR = sql_dir_input if sql_dir_input else DEFAULT_SQL_SOURCE_DIR

    # Build DAT file path from config pattern
    username = os.getenv('USERNAME', 'YourUsername')
    dat_file_path = DAT_FILE_PATTERN.format(username=username, report_name=REPORT_NAME)

    print(f"\n⚙️  Configuration:")
    print(f"  📊 Report Name: {REPORT_NAME}")
    print(f"  📁 SQL Source Directory: {SQL_SOURCE_DIR}")
    print(f"  🐟 Babelfish Directory: {BABELFISH_DIR}")
    print(f"  📄 DAT file Directory: {dat_file_path}")

    # Verify directories exist
    if not Path(BABELFISH_DIR).exists():
        print(f"\n❌ ERROR: Babelfish directory not found: {BABELFISH_DIR}")
        return True  # Return to menu instead of exiting

    if not Path(SQL_SOURCE_DIR).exists():
        print(f"\n❌ ERROR: SQL source directory not found: {SQL_SOURCE_DIR}")
        return True  # Return to menu instead of exiting

    # Ask user to confirm
    print("\n" + "="*80)
    print()
    response = input("⚠️  Are you sure you want to proceed? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Aborted by user.")
        return True  # Return to menu instead of exiting

    # Execute the steps silently
    print("\n⏳ Processing...")
    print()

    results = []

    # Step 1: Generate Report
    results.append(("Step 1: Generate Report", step1_generate_report(REPORT_NAME, SQL_SOURCE_DIR)))

    # Step 2: Generate DAT File
    if results[0][1]:  # Only proceed if Step 1 succeeded
        results.append(("Step 2: Generate DAT File", step2_generate_dat_file(REPORT_NAME)))
    else:
        results.append(("Step 2: Generate DAT File", False))

    # Step 3: Import to SQLite
    if results[1][1]:  # Only proceed if Step 2 succeeded
        results.append(("Step 3: Import to SQLite", step3_import_to_sqlite(REPORT_NAME)))
    else:
        results.append(("Step 3: Import to SQLite", False))

    # Overall result
    all_success = all(result[1] for result in results)

    # Print simple summary
    if all_success:
        print(f"✅ Your SQLite database is ready at:")
        print(f"   {SQLITE_DIR / f'{REPORT_NAME}.db'}")
        print()
        print("📋 Please check the log files for details")
    else:
        print("❌ ERROR: Processing failed. Please check the log files for details.")

    print()
    input("Press any key to continue...")

    return True  # Continue to main menu


def execute_cleanup():
    """Execute cleanup based on cleanup configuration."""
    cleanup_config_file = Path(SCRIPT_DIR) / 'Config' / 'cleanup_config.json'

    if not cleanup_config_file.exists():
        print(f"\n❌ ERROR: Cleanup configuration file not found: {cleanup_config_file}")
        input("\nPress any key to continue...")
        return

    print("\n" + "="*80)
    print("🗑  EXECUTE CLEANUP")
    print("="*80)

    # Load cleanup configuration
    try:
        with open(cleanup_config_file, 'r', encoding='utf-8') as f:
            cleanup_config = json.load(f)
    except Exception as e:
        print(f"\n❌ ERROR: Could not read cleanup configuration: {e}")
        input("\nPress any key to continue...")
        return

    operations = cleanup_config.get('cleanup_operations', [])

    if not operations:
        print("\n⚠️  WARNING: No cleanup operations configured")
        input("\nPress any key to continue...")
        return

    # Show what will be deleted
    print("\n" + "="*80)
    print("⚠️  WARNING: The following will be deleted:")
    print("="*80)

    for operation in operations:
        path = operation.get('path', '')
        description = operation.get('description', '')
        action = operation.get('action', '')

        if action == 'delete_folder':
            print(f"\n📁️  DELETE ENTIRE FOLDER: {path}")
        elif action == 'delete_contents':
            print(f"\n📁 DELETE CONTENTS ONLY: {path}")

        print(f"   {description}")

    # Confirm
    print("\n" + "="*80)
    confirm = input('\n⚠️  Are you sure you want to proceed? (yes/no): ').strip().lower()

    if confirm not in ['yes', 'y']:
        print('\n❌ Operation cancelled.')
        input("\nPress any key to continue...")
        return

    # Perform cleanup
    print("\n" + "="*80)
    print("🗑  PERFORMING CLEANUP...")
    print("="*80)

    deleted_count = 0
    error_count = 0

    for operation in operations:
        path_str = operation.get('path', '')
        action = operation.get('action', '')

        path = Path(path_str)

        try:
            if action == 'delete_folder':
                # Delete entire folder
                if path.exists():
                    shutil.rmtree(path)
                    print(f"✅ Deleted folder: {path}")
                    deleted_count += 1
                else:
                    print(f"ℹ️  Folder does not exist (already deleted): {path}")

            elif action == 'delete_contents':
                # Delete only contents
                if path.exists():
                    items_deleted = 0
                    for item in path.iterdir():
                        if item.is_file():
                            item.unlink()
                            items_deleted += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            items_deleted += 1
                    print(f"✅ Deleted {items_deleted} item(s) from: {path}")
                    deleted_count += items_deleted
                else:
                    print(f"ℹ️  Folder does not exist: {path}")

        except Exception as e:
            print(f"❌ Error processing {path}: {e}")
            error_count += 1

    print("\n" + "="*80)
    print(f"✅ Cleanup completed!")
    print(f"   Items deleted: {deleted_count}")
    if error_count > 0:
        print(f"   ⚠️  Errors: {error_count}")
    print("="*80)

    input("\nPress any key to continue...")


def open_documents_folder():
    """Open the user's Documents folder containing Babelfish Compass output."""
    print("\n" + "="*80)
    print("📂 OPEN DOCUMENTS FOLDER")
    print("="*80)

    documents_path = Path(os.environ['USERPROFILE']) / 'Documents'

    print(f"\n📁 Opening: {documents_path}")
    print("\n💡 Note: You can manually delete the BabelfishCompass folder contents")
    print("      after the data has been imported to SQLite.")

    try:
        subprocess.run(['explorer', str(documents_path)])
        print("\n✅ Documents folder opened")
    except Exception as e:
        print(f"\n❌ ERROR: Could not open Documents folder: {e}")

    input("\nPress any key to continue...")


def main_menu():
    """Display main menu and handle user choices"""
    # Display ASCII art on first iteration
    first_run = True

    while True:
        if first_run:
            display_ascii_art()
            first_run = False

        print("\n" + "=" * 80)
        print(f"{Colors.BLUE}SQL SERVER BABELFISH COMPASS UTILITY{Colors.RESET}")
        print("=" * 80)
        print("\n1. 📊  Generate Babelfish Compass Report")
        print("   • Executes the Babelfish Compass Report and imports the results into an SQLite database")
        print(f"   • {SQLITE_DIR}")
        print("   • Provide a report name and the directory path to your SQL files when prompted")
        print("\n2. 🗑️  Clean Workspace")
        print("   • Deletes folders and files as defined in the cleanup_config.json file")
        print("\n3. 📂 Open Documents Folder")
        print("   • Opens the folder containing the Babelfish Compass output")
        print("   • The contents can be manually deleted after import")
        print("\n4. 🚪 Exit")
        print("   • Closes the application")

        choice = input("\n👉 Enter your choice (1-4): ").strip()

        if choice == '1':
            run_report()
        elif choice == '2':
            execute_cleanup()
        elif choice == '3':
            open_documents_folder()
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-4.")


def main():
    """Main entry point."""
    main_menu()


if __name__ == "__main__":
    main()

