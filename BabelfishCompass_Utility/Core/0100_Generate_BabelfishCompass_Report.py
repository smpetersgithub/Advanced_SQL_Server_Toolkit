"""
Generate Babelfish Compass Report (Step 1)

This script generates a Babelfish Compass assessment report by analyzing SQL files.

Usage:
    python Generate_BabelfishCompass_Report.py <report_name> <sql_source_dir>

Arguments:
    report_name     - Name for the report (e.g., MyReport)
    sql_source_dir  - Directory containing SQL files to analyze

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
    DEFAULT_SQL_SOURCE_DIR = os.path.join(MAIN_DIR, config.get('Paths', 'sql_examples_dir'))
    
    # Defaults
    DEFAULT_REPORT_NAME = config.get('Defaults', 'default_report_name')
    
    # BabelfishCompass
    STEP1_OPTIONS = config.get('BabelfishCompass', 'step1_options')
    
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
log_filename = f"log_0100_Generate_BabelfishCompass_Report_{timestamp}.log"
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

def print_header():
    """Print script header"""
    logging.info("=" * 80)
    logging.info("STEP 1: Generate Babelfish Compass Report")
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
        if result.returncode == 0:
            logging.info("[OK] Command completed successfully")
            return True
        else:
            logging.warning(f"[WARNING] Command exited with code {result.returncode}")
            # For BabelfishCompass, non-zero exit codes are common but not necessarily failures
            return True

    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return False


def generate_report(report_name, sql_source_dir):
    """
    Generate the Babelfish Compass Report

    Args:
        report_name: Name for the report
        sql_source_dir: Directory containing SQL files to analyze

    Returns:
        bool: True if successful, False otherwise
    """
    print_header()

    # Validate inputs
    if not os.path.exists(sql_source_dir):
        logging.error(f"SQL source directory not found: {sql_source_dir}")
        return False

    if not os.path.exists(BABELFISH_DIR):
        logging.error(f"BabelfishCompass directory not found: {BABELFISH_DIR}")
        return False

    # Build the command using config options
    command = (
        f"BabelfishCompass.bat {report_name} "
        f"\"{sql_source_dir}\" "
        f"{STEP1_OPTIONS}"
    )

    logging.info(f"Analyzing SQL files in: {sql_source_dir}")
    logging.info(f"Report name: {report_name}")
    logging.info(f"Options: {STEP1_OPTIONS}")

    success = run_command(command, cwd=BABELFISH_DIR)

    if success:
        report_location = os.path.join(os.path.expanduser('~'), 'Documents', 'BabelfishCompass', report_name)
        logging.info("")
        logging.info("[OK] Report generated successfully")
        logging.info(f"Report location: {report_location}")
    else:
        logging.error("")
        logging.error("[ERROR] Report generation failed")

    return success


def main():
    """Main entry point"""

    # Parse command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python 0100_Generate_BabelfishCompass_Report.py <report_name> <sql_source_dir>")
        print()
        print("Arguments:")
        print("  report_name     - Name for the report (e.g., MyReport)")
        print("  sql_source_dir  - Directory containing SQL files to analyze")
        print()
        print(f"Example:")
        print(f"  python 0100_Generate_BabelfishCompass_Report.py MyReport \"{DEFAULT_SQL_SOURCE_DIR}\"")
        sys.exit(1)

    report_name = sys.argv[1].strip()
    sql_source_dir = sys.argv[2].strip()

    # Log detailed information to file
    logging.info(f"Log file: {LOG_FILE}")
    logging.info("")

    # Generate the report
    success = generate_report(report_name, sql_source_dir)

    logging.info("")
    logging.info(f"Log file saved to: {LOG_FILE}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

