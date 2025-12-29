"""
Generate DAT File for Database Import (Step 2)

This script generates a DAT file from a Babelfish Compass report.
It attempts to import into PostgreSQL (which typically fails), but the DAT file is still created.

Usage:
    python Generate_DAT_File.py <report_name>

Arguments:
    report_name - Name of the report (must match Step 1 report name)

Date: 2025-11-26
"""

import subprocess
import os
import sys
import configparser
import logging
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory where this script is located (Core directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the main directory
MAIN_DIR = os.path.dirname(SCRIPT_DIR)

# Setup logging directory
LOGS_DIR = os.path.join(MAIN_DIR, "Logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Load configuration from config.ini
CONFIG_FILE = os.path.join(MAIN_DIR, "Config", "config.ini")
config = configparser.ConfigParser()

# Check if config file exists
if not os.path.exists(CONFIG_FILE):
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Config directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values
try:
    # Paths
    BABELFISH_DIR = os.path.join(MAIN_DIR, config.get('Paths', 'babelfish_dir'))
    
    # Defaults
    DEFAULT_REPORT_NAME = config.get('Defaults', 'default_report_name')
    
    # PostgreSQL
    PG_CONNECTION = config.get('PostgreSQL', 'pg_connection')
    
    # BabelfishCompass
    DAT_FILE_PATTERN = config.get('BabelfishCompass', 'dat_file_pattern')
    
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)


# ============================================================================
# LOGGING SETUP
# ============================================================================

# Read logging configuration from config.ini
try:
    LOG_FORMAT = config.get('Logging', 'log_format')
    LOG_LEVEL = config.get('Logging', 'log_level')
    TIMESTAMP_FORMAT = config.get('Logging', 'timestamp_format')
    LOG_FILEMODE = config.get('Logging', 'log_filemode', fallback='w')
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    # Fallback to defaults if logging section is missing
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_LEVEL = 'INFO'
    TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
    LOG_FILEMODE = 'w'

# Create log filename with timestamp
timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
log_filename = f"log_0200_Generate_DAT_File_{timestamp}.log"
LOG_FILE = os.path.join(LOGS_DIR, log_filename)

# Map log level string to logging constant
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
log_level_value = log_level_map.get(LOG_LEVEL.upper(), logging.INFO)

# Configure logging - file only, no console output
logging.basicConfig(
    filename=LOG_FILE,
    level=log_level_value,
    format=LOG_FORMAT,
    filemode=LOG_FILEMODE
)


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def get_username():
    """Get the current Windows username"""
    return os.getenv('USERNAME', 'YourUsername')


def print_header():
    """Print script header"""
    logging.info("=" * 80)
    logging.info("STEP 2: Generate DAT File for Database Import")
    logging.info("=" * 80)


def run_command(command, cwd):
    """Execute a shell command and return success status"""
    logging.info(f"Executing command in {cwd}:")
    logging.info(f"  {command}")
    logging.info("")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Log stdout
        if result.stdout:
            for line in result.stdout.splitlines():
                logging.info(line)

        # Log stderr
        if result.stderr:
            for line in result.stderr.splitlines():
                logging.warning(line)

        logging.info("")
        # Note: We don't check return code because PostgreSQL import typically fails
        # but the DAT file is still created
        logging.info(f"Command exited with code {result.returncode}")
        return True

    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return False


def generate_dat_file(report_name):
    """
    Generate DAT file for database import

    Args:
        report_name: Name of the report

    Returns:
        bool: True if DAT file was created, False otherwise
    """
    print_header()

    # Validate BabelfishCompass directory exists
    if not os.path.exists(BABELFISH_DIR):
        logging.error(f"BabelfishCompass directory not found: {BABELFISH_DIR}")
        return False

    # Build the command
    command = (
        f"BabelfishCompass.bat {report_name} "
        f"-pgimport \"{PG_CONNECTION}\""
    )

    # Build DAT file path from config pattern
    username = get_username()
    dat_file_path = DAT_FILE_PATTERN.format(username=username, report_name=report_name)

    logging.info(f"Generating DAT file for report: {report_name}")
    logging.info(f"Expected DAT file location: {dat_file_path}")
    logging.info("")
    logging.info("Note: PostgreSQL import may fail - this is expected.")
    logging.info("      The DAT file will still be created for SQLite import.")

    # Run the command
    run_command(command, cwd=BABELFISH_DIR)

    # Check if DAT file was created (even if command failed)
    logging.info("")
    if os.path.exists(dat_file_path):
        file_size = os.path.getsize(dat_file_path)
        logging.info("[OK] DAT file created successfully")
        logging.info(f"DAT file location: {dat_file_path}")
        logging.info(f"File size: {file_size:,} bytes")
        return True
    else:
        logging.error(f"DAT file not found at expected location: {dat_file_path}")
        logging.error("")
        logging.error("Possible reasons:")
        logging.error("  1. Step 1 report was not generated")
        logging.error("  2. Report name does not match Step 1")
        logging.error("  3. BabelfishCompass failed to create the DAT file")
        return False


def main():
    """Main entry point"""

    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python 0200_Generate_DAT_File.py <report_name>")
        print()
        print("Arguments:")
        print("  report_name - Name of the report (must match Step 1 report name)")
        print()
        print(f"Example:")
        print(f"  python 0200_Generate_DAT_File.py {DEFAULT_REPORT_NAME}")
        print()
        print("Note: This script attempts to import into PostgreSQL (which typically fails),")
        print("      but the DAT file is still created for SQLite import in Step 3.")
        sys.exit(1)

    report_name = sys.argv[1].strip()

    # Log detailed information to file
    logging.info(f"Log file: {LOG_FILE}")
    logging.info("")

    # Generate the DAT file
    success = generate_dat_file(report_name)

    logging.info("")
    logging.info(f"Log file saved to: {LOG_FILE}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

