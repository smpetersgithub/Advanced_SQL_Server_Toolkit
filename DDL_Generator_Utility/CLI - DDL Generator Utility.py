"""
DDL Generator Utility - CLI

A command-line interface for generating SQL Server DDL scripts.
Provides an interactive menu for managing database configurations and generating scripts.
"""

import subprocess
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple


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

# Define paths
CORE_DIR = SCRIPT_DIR / "Core"
PYTHON_DIR = CORE_DIR / "Python"
CONFIG_DIR = SCRIPT_DIR / "Config"
GENERATED_SCRIPTS_DIR = SCRIPT_DIR / "Generated_Scripts"
DATABASE_CONFIG_DIR = CONFIG_DIR / "database_config"
SQL_SERVER_CONNECTIONS_FILE = CONFIG_DIR / "database-config.json"
ASCII_ART_FILE = CORE_DIR / "ascii_art.txt"

# Setup logging - Console output only
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run_python_script(script_path: Path, description: str) -> Tuple[bool, str, str]:
    """
    Execute a Python script and return the result.

    Args:
        script_path: Path to the Python script to execute
        description: Description of the script for error messages

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Script execution timed out after 1 hour"
    except subprocess.SubprocessError as e:
        return False, "", f"Subprocess error: {e}"
    except Exception as e:
        return False, "", f"Unexpected error: {e}"


def get_user_confirmation(prompt: str = "Are you sure you want to proceed?") -> bool:
    """
    Get yes/no confirmation from user.

    Args:
        prompt: The confirmation prompt to display

    Returns:
        bool: True if user confirmed, False otherwise
    """
    while True:
        response = input(f"\n⚠️  {prompt} (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("❌ Invalid input. Please enter 'yes' or 'no'.")


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def generate_database_configs() -> None:
    """
    STEP 1: Generate Database Configs

    Connects to each SQL Server and retrieves database lists,
    creating configuration files for each server.
    """
    print("\n" + "="*80)
    print("📊 GENERATE DATABASE CONFIGS")
    print("="*80)
    logging.info("Generating database configuration files")

    print("\n⏳ Logging into each server and retrieving database lists...")
    print(f"📁 Config files will be saved to: {DATABASE_CONFIG_DIR}")

    # Path to the script
    script_path = PYTHON_DIR / "01_generate_database_configs.py"

    # Run the script
    success, stdout, stderr = run_python_script(script_path, "Generate Database Configs")

    if success:
        print("\n✅ Database configuration files generated successfully!")
        print(f"📁 Location: {DATABASE_CONFIG_DIR}")
        print("\n💡 To whitelist databases, modify the 'is_active' property in the config files")
        logging.info("Database configuration files generated successfully")
    else:
        print("\n❌ ERROR: Failed to generate database configs. Please check the logs.")
        if stderr:
            print(f"   Error details: {stderr[:200]}")  # Show first 200 chars of error
        logging.error(f"Failed to generate database configs: {stderr[:200] if stderr else 'Unknown error'}")

    input("\nPress any key to continue...")


def display_database_configs() -> bool:
    """
    Display all database configurations from database_config files.

    Returns:
        bool: True if configs exist and were displayed, False otherwise
    """
    if not DATABASE_CONFIG_DIR.exists():
        print(f"\n❌ ERROR: Database config directory not found: {DATABASE_CONFIG_DIR}")
        print("💡 Please run 'Generate Database Configs' first (Option 1)")
        return False

    # Get all database config files
    config_files = [f for f in DATABASE_CONFIG_DIR.iterdir() if f.name.startswith("database_config_") and f.name.endswith(".json")]

    if not config_files:
        print(f"\n❌ ERROR: No database config files found in: {DATABASE_CONFIG_DIR}")
        print("💡 Please run 'Generate Database Configs' first (Option 1)")
        return False

    print("\n" + "="*80)
    print("📋 DATABASE CONFIGURATIONS SUMMARY")
    print("="*80)

    total_servers = 0
    total_databases = 0
    total_active_databases = 0

    for config_file in sorted(config_files):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            server_info = config.get("server", {})
            databases = config.get("databases", [])

            total_servers += 1
            total_databases += len(databases)

            # Count active databases
            active_dbs = [db for db in databases if db.get("is_active", False)]
            total_active_databases += len(active_dbs)

            print(f"\n🖥️ {server_info.get('servername', 'Unknown')}")
            print(f"   Parent: {server_info.get('parent_name', 'Unknown')}")
            print(f"   Total Databases: {len(databases)}")
            print(f"   Active Databases: {len(active_dbs)}")

            if active_dbs:
                print(f"   Active Database List:")
                for db in active_dbs:
                    print(f"      • {db.get('name', 'Unknown')} ({db.get('state', 'Unknown')})")
            else:
                print(f"   ⚠️  No active databases configured")

        except json.JSONDecodeError as e:
            print(f"\n❌ ERROR: Invalid JSON in {config_file.name}: {e}")
        except IOError as e:
            print(f"\n❌ ERROR: Could not read {config_file.name}: {e}")
        except Exception as e:
            print(f"\n❌ ERROR: Unexpected error reading {config_file.name}: {e}")

    print("\n" + "="*80)
    print(f"📊 TOTALS:")
    print(f"   Servers: {total_servers}")
    print(f"   Total Databases: {total_databases}")
    print(f"   Active Databases: {total_active_databases}")
    print("="*80)

    return True


def generate_ddl_scripts() -> None:
    """
    STEP 2: Generate DDL Scripts

    Creates directory structure and executes mssql-scripter to generate
    DDL scripts for all active databases.
    """
    print("\n" + "="*80)
    print("📝 GENERATE DDL SCRIPTS")
    print("="*80)
    logging.info("Starting DDL script generation")

    # Display database configurations
    if not display_database_configs():
        input("\nPress any key to continue...")
        return

    # Ask for confirmation
    if not get_user_confirmation("Are you sure you want to proceed?"):
        print("\n❌ DDL generation cancelled by user.")
        logging.info("DDL generation cancelled by user")
        input("\nPress any key to continue...")
        return

    print("\n⏳ Creating directory structure...")

    # Step 2a: Create directory structure
    script_path_1 = PYTHON_DIR / "02_create_directory_structure.py"
    success_1, stdout_1, stderr_1 = run_python_script(script_path_1, "Create Directory Structure")

    if not success_1:
        print("\n❌ ERROR: Failed to create directory structure. Please check the logs.")
        if stderr_1:
            print(f"   Error details: {stderr_1[:200]}")
        input("\nPress any key to continue...")
        return

    print("\n✅ Directory structure created successfully!")
    print("\n⏳ Executing mssql-scripter commands...")

    # Step 2b: Execute mssql-scripter
    script_path_2 = PYTHON_DIR / "03_execute_mssql_scripter.py"
    success_2, stdout_2, stderr_2 = run_python_script(script_path_2, "Execute mssql-scripter")

    if success_2:
        print("\n✅ DDL scripts generated successfully!")
        print(f"📁 Location: {GENERATED_SCRIPTS_DIR}")
        logging.info("DDL scripts generated successfully")
    else:
        print("\n❌ ERROR: Failed to generate DDL scripts. Please check the logs.")
        if stderr_2:
            print(f"   Error details: {stderr_2[:200]}")
        logging.error(f"Failed to generate DDL scripts: {stderr_2[:200] if stderr_2 else 'Unknown error'}")

    input("\nPress any key to continue...")


def execute_cleanup() -> None:
    """
    Execute cleanup based on cleanup configuration.

    Deletes folders and files as specified in cleanup-config.json.
    """
    cleanup_config_file = CONFIG_DIR / 'cleanup-config.json'

    if not cleanup_config_file.exists():
        print(f"\n❌ ERROR: Cleanup configuration file not found: {cleanup_config_file}")
        input("\nPress any key to continue...")
        return

    print("\n" + "="*80)
    print("🗑  EXECUTE CLEANUP")
    print("="*80)
    logging.info("Starting cleanup operation")

    # Load cleanup configuration
    try:
        with open(cleanup_config_file, 'r', encoding='utf-8') as f:
            cleanup_config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON in cleanup configuration: {e}")
        input("\nPress any key to continue...")
        return
    except IOError as e:
        print(f"\n❌ ERROR: Could not read cleanup configuration: {e}")
        input("\nPress any key to continue...")
        return
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error loading cleanup configuration: {e}")
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
            print(f"\n📁  DELETE ENTIRE FOLDER: {path}")
        elif action == 'delete_contents':
            print(f"\n📁 DELETE CONTENTS ONLY: {path}")

        print(f"   {description}")

    # Confirm
    print("\n" + "="*80)
    if not get_user_confirmation("Are you sure you want to proceed?"):
        print('\n❌ Operation cancelled.')
        logging.info("Cleanup operation cancelled by user")
        input("\nPress any key to continue...")
        return

    # Perform cleanup
    print("\n" + "="*80)
    print("🗑️ PERFORMING CLEANUP...")
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

        except PermissionError as e:
            print(f"❌ Permission denied: {path} - {e}")
            error_count += 1
        except OSError as e:
            print(f"❌ OS error processing {path}: {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ Unexpected error processing {path}: {e}")
            error_count += 1

    print("\n" + "="*80)
    print(f"✅ Cleanup completed!")
    print(f"   Items deleted: {deleted_count}")
    if error_count > 0:
        print(f"   ⚠️  Errors: {error_count}")
    print("="*80)
    logging.info(f"Cleanup completed: {deleted_count} items deleted, {error_count} errors")

    input("\nPress any key to continue...")


def view_sql_server_connections() -> None:
    """
    View SQL Server connections configuration file in a formatted way.

    Displays all configured servers with their connection details and status.
    """
    print("\n" + "="*80)
    print("📋  SQL SERVER CONFIGURATIONS")
    print("="*80)

    if not SQL_SERVER_CONNECTIONS_FILE.exists():
        print(f"\n❌ ERROR: Configuration file not found: {SQL_SERVER_CONNECTIONS_FILE}")
        input("\nPress any key to continue...")
        return

    try:
        with open(SQL_SERVER_CONNECTIONS_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        servers = config_data.get("servers", [])

        if not servers:
            print("\n⚠️  No servers configured.")
        else:
            for i, server in enumerate(servers, 1):
                is_active = server.get('active', False)
                if is_active:
                    status = f'{Colors.GREEN}✓ ACTIVE{Colors.RESET}'
                else:
                    status = f'{Colors.RED}✗ INACTIVE{Colors.RESET}'

                print(f'\n🖥️ {server.get("servername", "Unknown")} [{status}]')
                print(f'   Port: {server.get("port", "N/A")}')
                print(f'   Username: {server.get("username", "N/A")}')
                print(f'   Password: {"*" * len(server.get("password", ""))}')

                databases_include = server.get('databases_include', [])
                if databases_include:
                    print(f'   Databases: {", ".join(databases_include)}')
                else:
                    print(f'   Databases: ALL (no filter)')

    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON format: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: Could not read configuration file: {e}")

    print("\n" + "="*80)
    input("\nPress any key to continue...")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def display_ascii_art() -> None:
    """
    Print ASCII art from file.

    Silently fails if file is not found or cannot be read.
    """
    try:
        with open(ASCII_ART_FILE, 'r', encoding='utf-8') as f:
            print(f.read())
    except (FileNotFoundError, IOError):
        # If file not found or cannot be read, just skip the ASCII art
        pass


def main_menu() -> None:
    """
    Display main menu and handle user choices.

    Provides an interactive loop for the user to select operations.
    """
    logging.info("DDL Generator Utility started")

    # Display ASCII art on first iteration
    first_run = True

    while True:
        if first_run:
            display_ascii_art()
            first_run = False

        print("\n" + "=" * 80)
        print(f"{Colors.BLUE}SQL SERVER DDL GENERATOR UTILITY{Colors.RESET}")
        print("=" * 80)
        print('\n❗  To execute, perform the following steps.')
        print('   • Generate the database configuration files (Option 1)')
        print('   • Modify the configuration files to whitelist any databases - or leave the value empty to include all databases')
        print('   • Generate the DDL Scripts (Option 2)')
        print()
        print("\n1. 📊 Generate Database Configs")
        print("   • Logs into each server and retrieves the list of databases")
        print(f"   • {DATABASE_CONFIG_DIR}")
        print("   • To whitelist any databases, modify the config files 'is_active' property")
        print("\n2. 📝 Generate DDL Scripts")
        print("   • Creates the DDL Scripts in the Generated_Scripts folder")
        print("\n3. 🔍 View SQL Server Connections")
        print("   • Displays the database-config.json configuration file")
        print("\n4. 🗑️  Execute Cleanup")
        print("   • Deletes folders and files as defined in the cleanup-config.json file")
        print("\n5. 🚪 Exit")
        print("   • Closes the application")

        choice = input("\n👉 Enter your choice (1-5): ").strip()

        if choice == '1':
            generate_database_configs()
        elif choice == '2':
            generate_ddl_scripts()
        elif choice == '3':
            view_sql_server_connections()
        elif choice == '4':
            execute_cleanup()
        elif choice == '5':
            logging.info("User exited application")
            print("\n👋 Goodbye!")
            break
        elif choice == '':
            print("\n❌ No input received. Please enter a number between 1-5.")
        else:
            print(f"\n❌ Invalid choice '{choice}'. Please enter a number between 1-5.")


def main() -> None:
    """
    Main entry point for the CLI application.

    Initializes and runs the main menu loop.
    """
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

