"""
Script to open the Final Excel Report.

This script reads the configuration and opens the formatted Excel file
in the default application (typically Microsoft Excel).
"""

import os
import sys
import subprocess
import platform
import logging
from config_loader import ConfigLoader

# Constants
SEPARATOR = "=" * 60

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def open_excel_file(file_path):
    """
    Open an Excel file using the default application.

    Args:
        file_path: Full path to the Excel file

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        # Determine the operating system and use appropriate command
        system = platform.system()

        if system == 'Windows':
            # Windows: use os.startfile
            os.startfile(file_path)
        elif system == 'Darwin':
            # macOS: use 'open' command
            subprocess.run(['open', file_path], check=True)
        elif system == 'Linux':
            # Linux: use 'xdg-open' command
            subprocess.run(['xdg-open', file_path], check=True)
        else:
            logger.error(f"Unsupported operating system: {system}")
            return False

        logger.info(f"Opening Excel file: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return False

def main():
    """Main function to open the final Excel report."""
    # Load configuration
    config = ConfigLoader()

    # Get configuration values
    output_dir = config.get_output_dir()

    # Try to open the formatted file first, fall back to unformatted if not found
    formatted_file = os.path.join(output_dir, config.get_final_excel_report_formatted())
    unformatted_file = os.path.join(output_dir, config.get_final_excel_report())

    logger.info(SEPARATOR)
    logger.info("Opening Final Excel Report")
    logger.info(SEPARATOR)

    # Check which file exists
    if os.path.exists(formatted_file):
        logger.info(f"Found formatted file: {formatted_file}")
        success = open_excel_file(formatted_file)
    elif os.path.exists(unformatted_file):
        logger.warning(f"Formatted file not found. Opening unformatted file: {unformatted_file}")
        success = open_excel_file(unformatted_file)
    else:
        logger.error("No Excel report files found!")
        logger.error(f"  Formatted file:   {formatted_file}")
        logger.error(f"  Unformatted file: {unformatted_file}")
        logger.error("\nPlease run the following scripts first:")
        logger.error("  1. 06_create_final_excel_file.py")
        logger.error("  2. 07_format_excel_file.py (optional)")
        sys.exit(1)

    if success:
        logger.info(SEPARATOR)
        logger.info("SUCCESS!")
        logger.info(SEPARATOR)
    else:
        logger.error(SEPARATOR)
        logger.error("FAILED!")
        logger.error(SEPARATOR)
        sys.exit(1)

if __name__ == "__main__":
    main()

