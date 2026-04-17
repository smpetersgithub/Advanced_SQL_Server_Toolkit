"""
Generate DAT File for Database Import (Step 2)

This script generates a DAT file from a Babelfish Compass report.
It attempts to import into PostgreSQL (which typically fails), but the DAT file is still created.

Usage:
    python 02_Generate_DAT_File.py <report_name>

Arguments:
    report_name - Name of the report (must match Step 1 report name)

Date: 2026-03-19
"""

import subprocess
import sys
import logging
from pathlib import Path
from config_loader import ConfigLoader

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load configuration using ConfigLoader
config_loader = ConfigLoader()

# Get configuration values
BABELFISH_DIR = config_loader.get_babelfish_dir()
DEFAULT_REPORT_NAME = config_loader.get_default_report_name()
PG_CONNECTION = config_loader.get_pg_connection()
DAT_FILE_PATTERN = config_loader.get_dat_file_pattern()
REPORT_LOCATION_PATTERN = config_loader.get_report_location_pattern()

# Logging will be set up in main() function
LOG_FILE = None


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def get_username() -> str:
    """
    Get the current username (cross-platform).

    Returns:
        str: Username from environment variables (Windows: USERNAME, Unix: USER)
    """
    # Try Windows first, then Unix, then fallback
    import os
    return os.getenv('USERNAME') or os.getenv('USER') or 'YourUsername'


def print_header() -> None:
    """Print script header"""
    logging.info("=" * 80)
    logging.info("STEP 2: Generate DAT File for Database Import")
    logging.info("=" * 80)


def run_command(command_args: list, cwd: Path) -> bool:
    """
    Execute a command and return success status.

    Args:
        command_args: List of command arguments (e.g., ['BabelfishCompass.bat', 'MyReport', '-pgimport', '...'])
        cwd: Working directory as Path object

    Returns:
        bool: Always returns True unless an exception occurs

    Note:
        This function always returns True (even for non-zero exit codes) because:
        1. The PostgreSQL import typically fails (expected behavior)
        2. The DAT file is still created successfully despite the failure
        3. Success is determined by checking if the DAT file exists, not the exit code
        Only exceptions (e.g., command not found) return False.

        On Windows, .bat files require shell=True, but we use list arguments
        to prevent shell injection attacks.
    """
    command_str = ' '.join(str(arg) for arg in command_args)
    logging.info(f"Executing command in {cwd}:")
    logging.info(f"  {command_str}")
    logging.info("")

    try:
        # On Windows, .bat files need shell=True, but using list args prevents injection
        import platform
        use_shell = platform.system() == 'Windows'

        result = subprocess.run(
            command_args,
            shell=use_shell,  # True on Windows for .bat files, False on Unix
            cwd=str(cwd),
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
        logging.info(f"Command exited with code {result.returncode}")
        if result.returncode != 0:
            logging.warning("[INFO] Non-zero exit code is expected - PostgreSQL import typically fails")
            logging.warning("[INFO] The DAT file should still be created successfully")
        return True

    except FileNotFoundError as e:
        logging.error(f"Command not found: {e}")
        logging.error("Please verify BabelfishCompass.bat exists in the specified directory")
        return False
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return False


def generate_dat_file(report_name: str) -> bool:
    """
    Generate DAT file for database import

    Args:
        report_name: Name of the report

    Returns:
        bool: True if DAT file was created, False otherwise
    """
    print_header()

    # Validate BabelfishCompass directory exists
    if not BABELFISH_DIR.exists():
        logging.error(f"BabelfishCompass directory not found: {BABELFISH_DIR}")
        return False

    # Verify BabelfishCompass.bat exists
    bat_file = BABELFISH_DIR / "BabelfishCompass.bat"
    if not bat_file.exists():
        logging.error(f"BabelfishCompass.bat not found: {bat_file}")
        logging.error("Please ensure BabelfishCompass is properly installed")
        return False

    # Verify Step 1 report exists
    home_dir = Path.home()
    report_dir = Path(REPORT_LOCATION_PATTERN.format(home=home_dir, report_name=report_name))
    if not report_dir.exists():
        logging.error(f"Report directory not found: {report_dir}")
        logging.error("Please run Step 1 first to generate the report")
        logging.error(f"Expected report name: {report_name}")
        return False

    # Build the command using argument list (security: prevent shell injection)
    command_args = ["BabelfishCompass.bat", report_name, "-pgimport", PG_CONNECTION]

    # Build DAT file path from config pattern
    username = get_username()
    dat_file_path = Path(DAT_FILE_PATTERN.format(username=username, report_name=report_name))

    logging.info(f"Generating DAT file for report: {report_name}")
    logging.info(f"Expected DAT file location: {dat_file_path}")
    logging.info("")
    logging.info("Note: PostgreSQL import may fail - this is expected.")
    logging.info("      The DAT file will still be created for SQLite import.")

    # Run the command
    run_command(command_args, cwd=BABELFISH_DIR)

    # Check if DAT file was created (even if command failed)
    logging.info("")
    if dat_file_path.exists():
        file_size = dat_file_path.stat().st_size
        logging.info("[OK] DAT file created successfully")
        logging.info(f"DAT file location: {dat_file_path}")
        logging.info(f"File size: {file_size:,} bytes")
        return True
    else:
        logging.error(f"DAT file not found at expected location: {dat_file_path}")
        logging.error("-" * 80)
        logging.error("Possible reasons:")
        logging.error("  1. Step 1 report was not generated")
        logging.error("  2. Report name does not match Step 1")
        logging.error("  3. BabelfishCompass failed to create the DAT file")
        return False


def validate_report_name(report_name: str) -> bool:
    """
    Validate report name for invalid characters.

    Args:
        report_name: The report name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not report_name:
        print("Error: report_name cannot be empty")
        return False

    # Check for path separators and other invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in report_name:
            print(f"Error: report_name cannot contain '{char}' character")
            print(f"Invalid characters: {' '.join(invalid_chars)}")
            return False

    return True


def main() -> None:
    """Main entry point"""
    global LOG_FILE

    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python 02_Generate_DAT_File.py <report_name>")
        print()
        print("Arguments:")
        print("  report_name - Name of the report (must match Step 1 report name)")
        print()
        print(f"Example:")
        print(f"  python 02_Generate_DAT_File.py {DEFAULT_REPORT_NAME}")
        print()
        print("Note: This script attempts to import into PostgreSQL (which typically fails),")
        print("      but the DAT file is still created for SQLite import in Step 3.")
        sys.exit(1)

    report_name = sys.argv[1].strip()

    # Validate report name
    if not validate_report_name(report_name):
        sys.exit(1)

    # Setup logging after argument validation
    LOG_FILE = config_loader.setup_logging('02_Generate_DAT_File')

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

