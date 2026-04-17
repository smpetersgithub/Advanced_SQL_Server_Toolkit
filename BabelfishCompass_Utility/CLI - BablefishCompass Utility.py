"""
BabelfishCompass Utility Script

Date: 2026-03-19
"""

import subprocess
import os
import sys
import json
import shutil
import re
import platform
import logging
import time
from pathlib import Path
from typing import Optional

# Add Core/Python directory to path to import config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "Core" / "Python"))

from config_loader import ConfigLoader


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

# Load configuration using ConfigLoader
config_loader = ConfigLoader()

# Get configuration values (only what CLI needs for display/validation)
BABELFISH_DIR = config_loader.get_babelfish_dir()
DEFAULT_SQL_SOURCE_DIR = config_loader.get_sql_examples_dir()
SQLITE_DIR = config_loader.get_sqlite_dir()
CORE_DIR = config_loader.get_core_dir()
DEFAULT_REPORT_NAME = config_loader.get_default_report_name()
DAT_FILE_PATTERN = config_loader.get_dat_file_pattern()
ASCII_ART_FILE = config_loader.get_ascii_art_file()

# Setup logging for CLI orchestration - Console output only
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
LOG_FILE = None  # No log file, console only


# ============================================================================
# FUNCTIONS
# ============================================================================

def print_header(step_num: int, title: str) -> None:
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}: {title}")
    print("=" * 80 + "\n")


def validate_report_name(name: str) -> str:
    """
    Validate report name for invalid characters.

    Uses the same validation logic as core scripts for consistency.

    Args:
        name: The report name to validate

    Returns:
        str: The validated report name

    Raises:
        ValueError: If the report name contains invalid characters
    """
    if not name or not name.strip():
        raise ValueError("Report name cannot be empty")

    # Check for path separators and other invalid characters
    # Same validation as core scripts
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            raise ValueError(
                f"Report name cannot contain '{char}' character. "
                f"Invalid characters: {' '.join(invalid_chars)}"
            )

    # Check length (reasonable limit for filesystem)
    if len(name) > 100:
        raise ValueError(f"Report name too long (max 100 characters): '{name}'")

    return name


def validate_sql_directory(path_str: str) -> Path:
    """
    Validate SQL source directory path.

    Args:
        path_str: The directory path to validate

    Returns:
        Path: The validated Path object

    Raises:
        ValueError: If the path is invalid or doesn't exist
    """
    if not path_str or not path_str.strip():
        raise ValueError("SQL source directory cannot be empty")

    try:
        path = Path(path_str).resolve()
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

    if not path.exists():
        raise ValueError(f"Directory not found: {path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    return path


def is_safe_path(path: Path, base_path: Path) -> bool:
    """
    Ensure path is within base directory to prevent directory traversal attacks.

    Args:
        path: The path to validate
        base_path: The base directory that path should be within

    Returns:
        bool: True if path is safe, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        resolved_path = Path(path).resolve()
        resolved_base = Path(base_path).resolve()

        # Check if the resolved path is relative to the base path
        resolved_path.relative_to(resolved_base)
        return True
    except (ValueError, RuntimeError):
        # ValueError: path is not relative to base
        # RuntimeError: infinite loop in path resolution
        return False





def step1_generate_report(report_name: str, sql_source_dir: str) -> bool:
    """
    STEP 1: Generate the Babelfish Compass Report

    Calls the separate 01_Generate_BabelfishCompass_Report.py script
    """
    # Path to the 01_Generate_BabelfishCompass_Report.py script
    report_script = CORE_DIR / "Python" / "01_Generate_BabelfishCompass_Report.py"

    # Verify script exists
    if not report_script.exists():
        logging.error(f"Required script not found: {report_script}")
        print(f"❌ ERROR: Required script not found: {report_script}")
        return False

    # Run the report generation script
    try:
        logging.info(f"Executing Step 1: Generate Report for '{report_name}'")
        result = subprocess.run(
            [sys.executable, str(report_script), report_name, sql_source_dir],
            capture_output=True,
            text=True
        )
        success = result.returncode == 0
        logging.info(f"Step 1 completed with exit code: {result.returncode}")
        return success
    except Exception as e:
        logging.error(f"Failed to execute report generation script: {e}")
        print(f"❌ ERROR: Failed to execute report generation script: {e}")
        return False


def step2_generate_dat_file(report_name: str) -> bool:
    """
    STEP 2: Generate DAT File for Database Import

    Calls the separate 02_Generate_DAT_File.py script
    """
    # Path to the 02_Generate_DAT_File.py script
    dat_script = CORE_DIR / "Python" / "02_Generate_DAT_File.py"

    # Verify script exists
    if not dat_script.exists():
        logging.error(f"Required script not found: {dat_script}")
        print(f"❌ ERROR: Required script not found: {dat_script}")
        return False

    # Run the DAT file generation script
    try:
        logging.info(f"Executing Step 2: Generate DAT File for '{report_name}'")
        result = subprocess.run(
            [sys.executable, str(dat_script), report_name],
            capture_output=True,
            text=True
        )
        success = result.returncode == 0
        logging.info(f"Step 2 completed with exit code: {result.returncode}")
        return success
    except Exception as e:
        logging.error(f"Failed to execute DAT file generation script: {e}")
        print(f"❌ ERROR: Failed to execute DAT file generation script: {e}")
        return False


# ============================================================================
# NOTE: All business logic moved to separate Core/Python scripts
# ============================================================================
# This CLI script now acts as a menu-driven orchestrator that calls separate
# Python scripts in the Core/Python folder for each step:
#
#   Step 1: Core/Python/01_Generate_BabelfishCompass_Report.py
#   Step 2: Core/Python/02_Generate_DAT_File.py
#   Step 3: Core/Python/03_Import_DAT_to_SQLite.py
#
# This modular design allows:
#   - Each script can be run independently
#   - Business logic is separated from UI/menu logic
#   - Easier testing and maintenance
#   - All scripts share the same config.json file
# ============================================================================


def step3_import_to_sqlite(report_name: str) -> bool:
    """
    STEP 3: Import DAT File into SQLite Database

    Calls the separate 03_Import_DAT_to_SQLite.py script
    """
    # Path to the 03_Import_DAT_to_SQLite.py script
    import_script = CORE_DIR / "Python" / "03_Import_DAT_to_SQLite.py"

    # Verify script exists
    if not import_script.exists():
        logging.error(f"Required script not found: {import_script}")
        print(f"❌ ERROR: Required script not found: {import_script}")
        return False

    # Run the import script
    try:
        logging.info(f"Executing Step 3: Import to SQLite for '{report_name}'")
        result = subprocess.run(
            [sys.executable, str(import_script), report_name],
            capture_output=True,
            text=True
        )
        success = result.returncode == 0
        logging.info(f"Step 3 completed with exit code: {result.returncode}")
        return success
    except Exception as e:
        logging.error(f"Failed to execute SQLite import script: {e}")
        print(f"❌ ERROR: Failed to execute SQLite import script: {e}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def display_ascii_art() -> None:
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


def run_report() -> bool:
    """Run a single report - returns True to continue, False to exit"""

    # Prompt for report name
    print(f"\n📝 Enter report name (or press Enter for default: '{DEFAULT_REPORT_NAME}'):")
    report_name_input = input("Report name: ").strip()

    # Validate report name
    try:
        REPORT_NAME = validate_report_name(report_name_input if report_name_input else DEFAULT_REPORT_NAME)
    except ValueError as e:
        logging.warning(f"Invalid report name: {e}")
        print(f"\n❌ ERROR: {e}")
        input("\nPress any key to continue...")
        return True  # Return to menu

    # Prompt for SQL source directory
    print(f"\n📁 Enter SQL source directory path (or press Enter for default):")
    print(f"Default: {DEFAULT_SQL_SOURCE_DIR}")
    sql_dir_input = input("SQL directory: ").strip()

    # Validate SQL source directory
    try:
        if sql_dir_input:
            SQL_SOURCE_DIR_PATH = validate_sql_directory(sql_dir_input)
            SQL_SOURCE_DIR = str(SQL_SOURCE_DIR_PATH)
        else:
            SQL_SOURCE_DIR = str(DEFAULT_SQL_SOURCE_DIR)
            # Verify default directory exists
            if not DEFAULT_SQL_SOURCE_DIR.exists():
                raise ValueError(f"Default SQL directory not found: {DEFAULT_SQL_SOURCE_DIR}")
    except ValueError as e:
        logging.warning(f"Invalid SQL directory: {e}")
        print(f"\n❌ ERROR: {e}")
        input("\nPress any key to continue...")
        return True  # Return to menu

    # Build DAT file path from config pattern (cross-platform username)
    username = os.getenv('USERNAME') or os.getenv('USER') or 'YourUsername'
    dat_file_path = DAT_FILE_PATTERN.format(username=username, report_name=REPORT_NAME)

    # Log user selections
    logging.info("=" * 80)
    logging.info("User initiated report generation")
    logging.info(f"Report name: {REPORT_NAME}")
    logging.info(f"SQL source directory: {SQL_SOURCE_DIR}")
    logging.info(f"Username: {username}")
    logging.info("=" * 80)

    print(f"\n⚙️  Configuration:")
    print(f"  📊 Report Name: {REPORT_NAME}")
    print(f"  📁 SQL Source Directory: {SQL_SOURCE_DIR}")
    print(f"  🐟 Babelfish Directory: {BABELFISH_DIR}")
    print(f"  📄 DAT file Directory: {dat_file_path}")

    # Verify directories exist
    if not BABELFISH_DIR.exists():
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
        logging.info("User aborted report generation")
        print("❌ Aborted by user.")
        return True  # Return to menu instead of exiting

    # Execute the steps with progress feedback
    print("\n" + "="*80)
    print("⏳ PROCESSING")
    print("="*80)
    print()

    results = []

    # Step 1: Generate Report
    print("⏳ Step 1: Generating Babelfish Compass report...")
    print("   (This may take several minutes depending on the size of your SQL files)")
    step1_result = step1_generate_report(REPORT_NAME, SQL_SOURCE_DIR)
    results.append(("Step 1: Generate Report", step1_result))
    if step1_result:
        print("✅ Step 1: Report generated successfully")
    else:
        print("❌ Step 1: Report generation failed")
    print()

    # Step 2: Generate DAT File
    if results[0][1]:  # Only proceed if Step 1 succeeded
        print("⏳ Step 2: Generating DAT file...")
        step2_result = step2_generate_dat_file(REPORT_NAME)
        results.append(("Step 2: Generate DAT File", step2_result))
        if step2_result:
            print("✅ Step 2: DAT file generated successfully")
        else:
            print("❌ Step 2: DAT file generation failed")
    else:
        results.append(("Step 2: Generate DAT File", False))
        print("⏭️  Step 2: Skipped (Step 1 failed)")
    print()

    # Step 3: Import to SQLite
    if results[1][1]:  # Only proceed if Step 2 succeeded
        print("⏳ Step 3: Importing data to SQLite database...")
        step3_result = step3_import_to_sqlite(REPORT_NAME)
        results.append(("Step 3: Import to SQLite", step3_result))
        if step3_result:
            print("✅ Step 3: Data imported successfully")
        else:
            print("❌ Step 3: Data import failed")
    else:
        results.append(("Step 3: Import to SQLite", False))
        print("⏭️  Step 3: Skipped (Step 2 failed)")
    print()

    # Overall result
    all_success = all(result[1] for result in results)

    # Print detailed summary
    print("="*80)
    if all_success:
        logging.info("All steps completed successfully")
        print("✅ SUCCESS: All steps completed!")
        print()
        print(f"📊 Your SQLite database is ready at:")
        print(f"   {SQLITE_DIR / f'{REPORT_NAME}.db'}")
    else:
        logging.error("Processing failed - one or more steps failed")
        print("❌ ERROR: Processing failed")
        print()
        print("Step Results:")
        for step_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - {step_name}")
        print()
        print(f"📋 Please check the log files for details:")
        print(f"   Step Logs: {config_loader.get_logs_dir()}")
    print("="*80)

    print()
    input("Press any key to continue...")

    return True  # Continue to main menu


def execute_cleanup() -> None:
    """Execute cleanup based on cleanup configuration."""
    cleanup_config_file = Path(SCRIPT_DIR) / 'Config' / 'cleanup-config.json'

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

    # Check if any operation will delete the Logs folder
    logs_dir = config_loader.get_logs_dir()
    will_delete_logs = False
    for operation in operations:
        path_str = operation.get('path', '')
        path_obj = Path(path_str)
        dir_name = path_obj.name
        path_mapping = {
            'Logs': logs_dir,
            'SQLite': config_loader.get_sqlite_dir(),
        }
        resolved_path = path_mapping.get(dir_name, path_obj)

        if resolved_path == logs_dir or str(resolved_path).startswith(str(logs_dir)):
            will_delete_logs = True
            break

    # Map of known directory names to ConfigLoader methods
    # This allows cleanup-config.json to use absolute paths, but we resolve them
    # using ConfigLoader to ensure they're correct for the current installation
    path_mapping = {
        'Logs': config_loader.get_logs_dir(),
        'SQLite': config_loader.get_sqlite_dir(),
    }

    # Show what will be deleted
    print("\n" + "="*80)
    print("⚠️  WARNING: The following will be deleted:")
    print("="*80)

    for operation in operations:
        path_str = operation.get('path', '')
        description = operation.get('description', '')
        action = operation.get('action', '')

        # Resolve path using ConfigLoader by extracting the directory name
        # from the absolute path and mapping it to the correct location
        path_obj = Path(path_str)
        dir_name = path_obj.name  # Get the last component (e.g., 'Logs', 'SQLite')

        # Use mapped path if available, otherwise use the path as-is
        resolved_path = path_mapping.get(dir_name, path_obj)

        if action == 'delete_folder':
            print(f"\n📁️  DELETE ENTIRE FOLDER: {resolved_path}")
        elif action == 'delete_contents':
            print(f"\n📁 DELETE CONTENTS ONLY: {resolved_path}")

        print(f"   {description}")

    # Confirm
    print("\n" + "="*80)
    confirm = input('\n⚠️  Are you sure you want to proceed? (yes/no): ').strip().lower()

    if confirm not in ['yes', 'y']:
        print('\n❌ Operation cancelled.')
        input("\nPress any key to continue...")
        return

    # Note: No need to close log file since we're logging to console only
    # (Keeping this section for reference in case file logging is re-enabled)

    # Perform cleanup
    print("\n" + "="*80)
    print("🗑  PERFORMING CLEANUP...")
    print("="*80)

    deleted_count = 0
    error_count = 0

    for operation in operations:
        path_str = operation.get('path', '')
        action = operation.get('action', '')

        # Resolve path using ConfigLoader by extracting the directory name
        path_obj = Path(path_str)
        dir_name = path_obj.name  # Get the last component (e.g., 'Logs', 'SQLite')

        # Use mapped path if available, otherwise use the path as-is
        resolved_path = path_mapping.get(dir_name, path_obj)

        # Security check: Ensure path is within project directory
        if not is_safe_path(resolved_path, SCRIPT_DIR):
            print(f"⚠️  SECURITY: Refusing to delete path outside project directory: {resolved_path}")
            error_count += 1
            continue

        if action == 'delete_folder':
            # Delete entire folder (contents first, then folder itself)
            if resolved_path.exists():
                items_deleted = 0
                failed_items = []

                # First, delete all contents
                try:
                    for item in resolved_path.iterdir():
                        deleted = False
                        # Try up to 2 times with a delay for locked files
                        for attempt in range(2):
                            try:
                                if item.is_file():
                                    item.unlink()
                                    items_deleted += 1
                                    deleted = True
                                    break
                                elif item.is_dir():
                                    shutil.rmtree(item)
                                    items_deleted += 1
                                    deleted = True
                                    break
                            except (PermissionError, OSError) as e:
                                if attempt == 0:
                                    # First attempt failed, wait a bit
                                    time.sleep(0.2)
                                else:
                                    # Second attempt failed, give up
                                    failed_items.append(str(item.name))

                        if not deleted and str(item.name) not in failed_items:
                            failed_items.append(str(item.name))

                except Exception as e:
                    print(f"⚠️  Error listing folder contents: {e}")

                # Then try to delete the folder itself
                if not failed_items:
                    try:
                        resolved_path.rmdir()
                        print(f"✅ Deleted folder: {resolved_path}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️  Deleted contents but could not remove folder: {resolved_path}")
                        print(f"   Reason: {e}")
                        error_count += 1
                else:
                    print(f"⚠️  Could not delete folder {resolved_path} - {len(failed_items)} item(s) in use:")
                    for item_name in failed_items[:5]:
                        print(f"   - {item_name}")
                    if len(failed_items) > 5:
                        print(f"   ... and {len(failed_items) - 5} more")
                    if items_deleted > 0:
                        print(f"   (Deleted {items_deleted} other item(s))")

                    # Check if locked files are CLI logs
                    cli_logs = [f for f in failed_items if 'CLI_BabelfishCompass' in f]
                    if cli_logs:
                        print(f"   💡 Note: {len(cli_logs)} CLI log file(s) may be from previous sessions")
                        print(f"      These will be cleaned up on next application restart")

                    error_count += len(failed_items)
            else:
                print(f"ℹ️  Folder does not exist (already deleted): {resolved_path}")

        elif action == 'delete_contents':
            # Delete only contents
            if resolved_path.exists():
                items_deleted = 0
                failed_items = []
                for item in resolved_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                            items_deleted += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            items_deleted += 1
                    except (PermissionError, OSError) as e:
                        failed_items.append(str(item.name))

                if items_deleted > 0:
                    print(f"✅ Deleted {items_deleted} item(s) from: {resolved_path}")
                    deleted_count += items_deleted

                if failed_items:
                    print(f"⚠️  Could not delete {len(failed_items)} item(s) (may be in use):")
                    for item_name in failed_items[:5]:  # Show first 5
                        print(f"   - {item_name}")
                    if len(failed_items) > 5:
                        print(f"   ... and {len(failed_items) - 5} more")
                    error_count += len(failed_items)
            else:
                print(f"ℹ️  Folder does not exist: {resolved_path}")

    print("\n" + "="*80)
    if error_count == 0:
        print(f"✅ Cleanup completed successfully!")
        print(f"   Items deleted: {deleted_count}")
    else:
        print(f"⚠️  Cleanup completed with warnings")
        print(f"   Items deleted: {deleted_count}")
        print(f"   Items skipped: {error_count}")
        print()
        print("💡 Tip: Some files may be in use by other processes.")
        print("   Try closing other applications and running cleanup again.")
    print("="*80)

    # Log cleanup results (console only, no file)
    logging.info(f"Cleanup completed: {deleted_count} items deleted, {error_count} errors")

    input("\nPress any key to continue...")


def open_documents_folder() -> None:
    """Open the user's Documents folder containing Babelfish Compass output (cross-platform)."""
    print("\n" + "="*80)
    print("📂 OPEN DOCUMENTS FOLDER")
    print("="*80)

    # Get Documents folder path (cross-platform)
    system = platform.system()
    if system == 'Windows':
        documents_path = Path(os.environ.get('USERPROFILE', os.path.expanduser('~'))) / 'Documents'
    else:
        # macOS and Linux
        documents_path = Path.home() / 'Documents'

    print(f"\n📁 Opening: {documents_path}")
    print("\n💡 Note: You can manually delete the BabelfishCompass folder contents")
    print("      after the data has been imported to SQLite.")

    try:
        # Use platform-specific command to open file explorer
        if system == 'Windows':
            subprocess.run(['explorer', str(documents_path)], check=False)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', str(documents_path)], check=False)
        else:  # Linux and other Unix-like systems
            subprocess.run(['xdg-open', str(documents_path)], check=False)

        print("\n✅ Documents folder opened")
    except Exception as e:
        print(f"\n❌ ERROR: Could not open Documents folder: {e}")
        print(f"   Please manually navigate to: {documents_path}")

    input("\nPress any key to continue...")


def main_menu() -> None:
    """Display main menu and handle user choices"""
    logging.info("CLI application started")

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
        print("   • Deletes folders and files as defined in the cleanup-config.json file")
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
            logging.info("User exited application")
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-4.")


def main() -> None:
    """Main entry point."""
    main_menu()


if __name__ == "__main__":
    main()
