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

logger = logging.getLogger(__name__)

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
        logger.error(f"Invalid JSON in config file {config_file_path}: {e}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"Failed to read config file {config_file_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading config file {config_file_path}: {e}", exc_info=True)
        return None


def get_all_database_config_files(database_config_dir: Path) -> List[Path]:
    """
    Get all database_config_*.json files from the database_config directory.

    Returns:
        List of Path objects for each config file found
    """
    if not database_config_dir.exists():
        logger.error(f"Database config directory not found: {database_config_dir}")
        return []

    config_files = list(database_config_dir.glob(DATABASE_CONFIG_PATTERN))
    logger.info(f"Found {len(config_files)} database config file(s)")
    return config_files


def create_directories_for_config(config_data: Dict, config_filename: str,
                                  generated_scripts_dir: Path) -> Tuple[int, int, int]:
    """
    Create directory structure for a single database config file.

    Args:
        config_data: Dictionary containing the database configuration
        config_filename: Name of the config file being processed
        generated_scripts_dir: Base path for generated scripts output

    Returns:
        Tuple of (dirs_created, dirs_already_exist, dirs_inactive)
    """
    try:
        server_info = config_data.get("server", {})
        parent_name = server_info.get("parent_name", "")
        servername = server_info.get("servername", "")

        if not parent_name or not servername:
            logger.warning(f"  Missing parent_name or servername in {config_filename}")
            return 0, 0, 0

        parent_name_clean = sanitize_dirname(parent_name)
        servername_clean = sanitize_dirname(servername)

        databases = config_data.get("databases", [])

        if not databases:
            logger.warning(f"  No databases found in {config_filename}")
            return 0, 0, 0

        active_count = sum(1 for db in databases if db.get("is_active", False))

        logger.info(f"  Parent Name: {parent_name}")
        logger.info(f"  Server Name: {servername}")
        logger.info(f"  Total Databases: {len(databases)} ({active_count} active)")

        dirs_created = 0
        dirs_already_exist = 0
        dirs_inactive = 0

        for db in databases:
            db_name = db.get("name", "")
            is_active = db.get("is_active", False)

            if not db_name:
                logger.warning(f"    Skipping database with no name")
                continue

            if not is_active:
                logger.debug(f"    Skipping inactive database: {db_name}")
                dirs_inactive += 1
                continue

            db_name_clean = sanitize_dirname(db_name)

            dir_path = generated_scripts_dir / parent_name_clean / servername_clean / db_name_clean

            try:
                if dir_path.exists():
                    logger.debug(f"    Directory already exists: {dir_path}")
                    dirs_already_exist += 1
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"    Created [ACTIVE]: {parent_name_clean}/{servername_clean}/{db_name_clean}")
                    dirs_created += 1
            except OSError as e:
                logger.error(f"    Failed to create directory {dir_path}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"    Unexpected error creating directory {dir_path}: {e}", exc_info=True)

        return dirs_created, dirs_already_exist, dirs_inactive

    except Exception as e:
        logger.error(f"  Error processing config {config_filename}: {e}", exc_info=True)
        return 0, 0, 0


# ===================== Main Processing =====================
def main():
    """Main processing function"""
    # Load configuration
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)

    # Read configuration values
    workspace_dir = config.get_workspace_dir()
    database_config_dir = config.get_database_config_dir()
    generated_scripts_dir = config.get_generated_scripts_dir()
    log_dir = config.get_log_dir()

    # Ensure directories exist
    database_config_dir.mkdir(parents=True, exist_ok=True)
    generated_scripts_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = config.setup_logging('02_create_directory_structure')

    logger.info("=" * 70)
    logger.info("Directory Structure Creator")
    logger.info("=" * 70)
    logger.info(f"Workspace: {workspace_dir}")
    logger.info(f"Database Config Directory: {database_config_dir}")
    logger.info(f"Generated Scripts Directory: {generated_scripts_dir}")
    logger.info(f"Log File: {log_file}")
    logger.info("")

    try:
        config_files = get_all_database_config_files(database_config_dir)

        if not config_files:
            logger.warning("No database config files found")
            return

        logger.info("")

        total_dirs_created = 0
        total_dirs_already_exist = 0
        total_dirs_inactive = 0
        total_configs_processed = 0

        for config_file in config_files:
            logger.info(f"Processing: {config_file.name}")

            config_data = load_database_config(config_file)

            if not config_data:
                logger.warning(f"  Skipping {config_file.name} due to load error")
                continue

            dirs_created, dirs_exist, dirs_inactive = create_directories_for_config(
                config_data, config_file.name, generated_scripts_dir
            )

            total_dirs_created += dirs_created
            total_dirs_already_exist += dirs_exist
            total_dirs_inactive += dirs_inactive
            total_configs_processed += 1

            logger.info(f"  Directories created: {dirs_created}, already exist: {dirs_exist}, inactive: {dirs_inactive}")
            logger.info("")

        logger.info("=" * 70)
        logger.info(f"Directory creation complete!")
        logger.info(f"Config files processed: {total_configs_processed}")
        logger.info(f"Total directories created: {total_dirs_created}")
        logger.info(f"Total directories already exist: {total_dirs_already_exist}")
        logger.info(f"Total inactive databases skipped: {total_dirs_inactive}")
        logger.info(f"Generated Scripts location: {generated_scripts_dir}")
        logger.info("=" * 70)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
