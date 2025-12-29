# create_directory_structure.py
"""
Script to create directory structure for Generated_Scripts based on database_config files.
Creates directories in the format: Generated_Scripts/PARENTNAME/SERVERNAME/DATABASENAME/
"""
import os
import sys
import json
import logging
import configparser
from pathlib import Path
from datetime import datetime

# ===================== Configuration =====================
# Load configuration from config.ini
config = configparser.ConfigParser()
CONFIG_FILE = Path("C:/Advanced_SQL_Server_Toolkit/DDL_Generator_Utility/Config/config.ini")

if not CONFIG_FILE.exists():
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Config directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values
try:
    WORKSPACE_DIR = Path(config.get('Paths', 'workspace_dir'))
    CONFIG_DIR = WORKSPACE_DIR / config.get('Paths', 'config_dir')
    DATABASE_CONFIG_DIR = WORKSPACE_DIR / config.get('Paths', 'database_config_dir')
    GENERATED_SCRIPTS_DIR = WORKSPACE_DIR / config.get('Paths', 'generated_scripts_dir')
    LOG_DIR = WORKSPACE_DIR / config.get('Paths', 'log_dir')

    # Logging configuration
    LOG_LEVEL = config.get('Logging', 'log_level')
    LOG_FORMAT = config.get('Logging', 'log_format')
    TIMESTAMP_FORMAT = config.get('Logging', 'timestamp_format')
    LOG_FILEMODE = config.get('Logging', 'log_filemode', fallback='w')

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)

# Ensure directories exist
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_002_create_directory_structure_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level_value = log_level_map.get(LOG_LEVEL.upper(), logging.INFO)

# Configure logging - file only, no console output
logging.basicConfig(
    filename=str(LOG_FILE),
    level=log_level_value,
    format=LOG_FORMAT,
    filemode=LOG_FILEMODE
)

logging.info("=" * 70)
logging.info("Directory Structure Creator")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Generated Scripts Directory: {GENERATED_SCRIPTS_DIR}")
logging.info(f"Log File: {LOG_FILE}")
logging.info("")

# ===================== Helper Functions =====================
def sanitize_dirname(name):
    """Sanitize name for use in directory name"""
    # Replace invalid directory characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner directory names
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ',']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized


def load_database_config(config_file_path):
    """Load a database configuration file"""
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_file_path}: {e}")
        return None


def get_all_database_config_files():
    """Get all database_config_*.json files from the database_config directory"""
    if not DATABASE_CONFIG_DIR.exists():
        logging.error(f"Database config directory not found: {DATABASE_CONFIG_DIR}")
        return []
    
    config_files = list(DATABASE_CONFIG_DIR.glob("database_config_*.json"))
    logging.info(f"Found {len(config_files)} database config file(s)")
    return config_files


def create_directories_for_config(config_data, config_filename):
    """
    Create directory structure for a single database config file.
    
    Args:
        config_data: Dictionary containing the database configuration
        config_filename: Name of the config file being processed
    
    Returns:
        Tuple of (total_dirs_created, total_dirs_skipped)
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
        dirs_skipped = 0

        # Create directory for each ACTIVE database only
        for db in databases:
            db_name = db.get("name", "")
            is_active = db.get("is_active", False)

            if not db_name:
                logging.warning(f"    Skipping database with no name")
                dirs_skipped += 1
                continue

            # Skip inactive databases
            if not is_active:
                logging.debug(f"    Skipping inactive database: {db_name}")
                dirs_skipped += 1
                continue

            # Sanitize database name for directory
            db_name_clean = sanitize_dirname(db_name)

            # Create full directory path: Generated_Scripts/PARENTNAME/SERVERNAME/DATABASENAME
            dir_path = GENERATED_SCRIPTS_DIR / parent_name_clean / servername_clean / db_name_clean

            # Create the directory
            try:
                if dir_path.exists():
                    logging.debug(f"    Directory already exists: {dir_path}")
                    dirs_skipped += 1
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logging.info(f"    Created [ACTIVE]: {parent_name_clean}/{servername_clean}/{db_name_clean}")
                    dirs_created += 1
            except Exception as e:
                logging.error(f"    Failed to create directory {dir_path}: {e}")
                dirs_skipped += 1
        
        return dirs_created, dirs_skipped
        
    except Exception as e:
        logging.error(f"  Error processing config {config_filename}: {e}")
        return 0, 0


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
        total_dirs_skipped = 0
        total_configs_processed = 0
        
        for config_file in config_files:
            logging.info(f"Processing: {config_file.name}")
            
            # Load config file
            config_data = load_database_config(config_file)
            
            if not config_data:
                logging.warning(f"  Skipping {config_file.name} due to load error")
                continue
            
            # Create directories for this config
            dirs_created, dirs_skipped = create_directories_for_config(config_data, config_file.name)
            
            total_dirs_created += dirs_created
            total_dirs_skipped += dirs_skipped
            total_configs_processed += 1
            
            logging.info(f"  Directories created: {dirs_created}, skipped: {dirs_skipped}")
            logging.info("")
        
        # Summary
        logging.info("=" * 70)
        logging.info(f"Directory creation complete!")
        logging.info(f"Config files processed: {total_configs_processed}")
        logging.info(f"Total directories created: {total_dirs_created}")
        logging.info(f"Total directories skipped (already exist): {total_dirs_skipped}")
        logging.info(f"Generated Scripts location: {GENERATED_SCRIPTS_DIR}")
        logging.info("=" * 70)
        
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

