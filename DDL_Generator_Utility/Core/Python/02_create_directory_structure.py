# create_directory_structure.py
"""
Script to create directory structure for Generated_Scripts based on database_config files.
Creates directories in the format: Generated_Scripts/PARENTNAME/SERVERNAME/DATABASENAME/
"""
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from config_loader import ConfigLoader

# ===================== Configuration =====================
# Load configuration using ConfigLoader (reads from Config/config.json)
try:
    config = ConfigLoader()
except FileNotFoundError as e:
    print(f"[ERROR] {e}")
    print("Please ensure config.json exists in the Config directory.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.json file for errors.")
    sys.exit(1)

# Read configuration values
WORKSPACE_DIR = config.get_workspace_dir()
CONFIG_DIR = config.get_config_dir()
DATABASE_CONFIG_DIR = config.get_database_config_dir()
GENERATED_SCRIPTS_DIR = config.get_generated_scripts_dir()
LOG_DIR = config.get_log_dir()

# Ensure directories exist
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = config.setup_logging('02_create_directory_structure')

logging.info("=" * 70)
logging.info("Directory Structure Creator")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Generated Scripts Directory: {GENERATED_SCRIPTS_DIR}")
logging.info(f"Log File: {LOG_FILE}")
logging.info("")

# ===================== Constants =====================
DATABASE_CONFIG_PATTERN = "database_config_*.json"

# ===================== Helper Functions =====================
def sanitize_dirname(name: str) -> str:
    """
    Sanitize name for use in directory name.

    Args:
        name: Directory name to sanitize

    Returns:
        str: Sanitized directory-safe string
    """
    # Replace invalid directory characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner directory names
    invalid_chars = '<>:"/\\|?*,'
    translation_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))
    return name.translate(translation_table)


def load_database_config(config_file_path: Path) -> Optional[Dict]:
    """
    Load a database configuration file.

    Args:
        config_file_path: Path to the JSON configuration file

    Returns:
        Dict containing the configuration, or None if loading fails
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file {config_file_path}: {e}")
        return None
    except IOError as e:
        logging.error(f"Failed to read config file {config_file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading config file {config_file_path}: {e}", exc_info=True)
        return None


def get_all_database_config_files() -> List[Path]:
    """
    Get all database_config_*.json files from the database_config directory.

    Returns:
        List of Path objects for each config file found
    """
    if not DATABASE_CONFIG_DIR.exists():
        logging.error(f"Database config directory not found: {DATABASE_CONFIG_DIR}")
        return []

    config_files = list(DATABASE_CONFIG_DIR.glob(DATABASE_CONFIG_PATTERN))
    logging.info(f"Found {len(config_files)} database config file(s)")
    return config_files


def create_directories_for_config(config_data: Dict, config_filename: str) -> Tuple[int, int, int]:
    """
    Create directory structure for a single database config file.

    Args:
        config_data: Dictionary containing the database configuration
        config_filename: Name of the config file being processed

    Returns:
        Tuple of (dirs_created, dirs_already_exist, dirs_inactive)
    """
    try:
        # Extract server information
        server_info = config_data.get("server", {})
        parent_name = server_info.get("parent_name", "")
        servername = server_info.get("servername", "")
        
        if not parent_name or not servername:
            logging.warning(f"  Missing parent_name or servername in {config_filename}")
            return 0, 0
        
        # Sanitize parent_name and servername for directory names
        parent_name_clean = sanitize_dirname(parent_name)
        servername_clean = sanitize_dirname(servername)
        
        # Get databases list
        databases = config_data.get("databases", [])

        if not databases:
            logging.warning(f"  No databases found in {config_filename}")
            return 0, 0

        # Count active databases
        active_count = sum(1 for db in databases if db.get("is_active", False))

        logging.info(f"  Parent Name: {parent_name}")
        logging.info(f"  Server Name: {servername}")
        logging.info(f"  Total Databases: {len(databases)} ({active_count} active)")

        dirs_created = 0
        dirs_already_exist = 0
        dirs_inactive = 0

        # Create directory for each ACTIVE database only
        for db in databases:
            db_name = db.get("name", "")
            is_active = db.get("is_active", False)

            if not db_name:
                logging.warning(f"    Skipping database with no name")
                continue

            # Skip inactive databases
            if not is_active:
                logging.debug(f"    Skipping inactive database: {db_name}")
                dirs_inactive += 1
                continue

            # Sanitize database name for directory
            db_name_clean = sanitize_dirname(db_name)

            # Create full directory path: Generated_Scripts/PARENTNAME/SERVERNAME/DATABASENAME
            dir_path = GENERATED_SCRIPTS_DIR / parent_name_clean / servername_clean / db_name_clean

            # Create the directory
            try:
                if dir_path.exists():
                    logging.debug(f"    Directory already exists: {dir_path}")
                    dirs_already_exist += 1
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logging.info(f"    Created [ACTIVE]: {parent_name_clean}/{servername_clean}/{db_name_clean}")
                    dirs_created += 1
            except OSError as e:
                logging.error(f"    Failed to create directory {dir_path}: {e}")
            except Exception as e:
                logging.error(f"    Unexpected error creating directory {dir_path}: {e}", exc_info=True)

        return dirs_created, dirs_already_exist, dirs_inactive

    except Exception as e:
        logging.error(f"  Error processing config {config_filename}: {e}", exc_info=True)
        return 0, 0, 0


# ===================== Main Processing =====================
def main():
    """Main processing function"""
    try:
        # Get all database config files
        config_files = get_all_database_config_files()
        
        if not config_files:
            logging.warning("No database config files found")
            return
        
        logging.info("")
        
        # Process each config file
        total_dirs_created = 0
        total_dirs_already_exist = 0
        total_dirs_inactive = 0
        total_configs_processed = 0

        for config_file in config_files:
            logging.info(f"Processing: {config_file.name}")

            # Load config file
            config_data = load_database_config(config_file)

            if not config_data:
                logging.warning(f"  Skipping {config_file.name} due to load error")
                continue

            # Create directories for this config
            dirs_created, dirs_exist, dirs_inactive = create_directories_for_config(config_data, config_file.name)

            total_dirs_created += dirs_created
            total_dirs_already_exist += dirs_exist
            total_dirs_inactive += dirs_inactive
            total_configs_processed += 1

            logging.info(f"  Directories created: {dirs_created}, already exist: {dirs_exist}, inactive: {dirs_inactive}")
            logging.info("")

        # Summary
        logging.info("=" * 70)
        logging.info(f"Directory creation complete!")
        logging.info(f"Config files processed: {total_configs_processed}")
        logging.info(f"Total directories created: {total_dirs_created}")
        logging.info(f"Total directories already exist: {total_dirs_already_exist}")
        logging.info(f"Total inactive databases skipped: {total_dirs_inactive}")
        logging.info(f"Generated Scripts location: {GENERATED_SCRIPTS_DIR}")
        logging.info("=" * 70)
        
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

