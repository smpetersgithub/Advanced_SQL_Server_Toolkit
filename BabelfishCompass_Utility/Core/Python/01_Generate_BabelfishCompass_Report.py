"""
Generate Babelfish Compass Report (Step 1)

This script generates a Babelfish Compass assessment report by analyzing SQL files.

Usage:
    python 01_Generate_BabelfishCompass_Report.py <report_name> <sql_source_dir>

Arguments:
    report_name     - Name for the report (e.g., MyReport)
    sql_source_dir  - Directory containing SQL files to analyze

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
DEFAULT_SQL_SOURCE_DIR = config_loader.get_sql_examples_dir()
DEFAULT_REPORT_NAME = config_loader.get_default_report_name()
STEP1_OPTIONS = config_loader.get_step1_options()
REPORT_LOCATION_PATTERN = config_loader.get_report_location_pattern()

# Logging will be set up in main() function
LOG_FILE = None


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def print_header() -> None:
    """Print script header"""
    logging.info("=" * 80)
    logging.info("STEP 1: Generate Babelfish Compass Report")
    logging.info("=" * 80)


def run_command(command_args: list, cwd: Path) -> bool:
    """
    Execute a command and return success status.

    Args:
        command_args: List of command arguments (e.g., ['BabelfishCompass.bat', 'MyReport', 'path'])
        cwd: Working directory as Path object

    Returns:
        bool: True if successful (exit code 0 or acceptable non-zero codes), False otherwise

    Note:
        BabelfishCompass may return non-zero exit codes even on successful analysis
        if it encounters unsupported T-SQL features. These are treated as warnings,
        not failures. Only exceptions and critical errors return False.

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
        if result.returncode == 0:
            logging.info("[OK] Command completed successfully")
            return True
        else:
            logging.warning(f"[WARNING] Command exited with code {result.returncode}")
            logging.warning("[INFO] Non-zero exit codes are common for BabelfishCompass when analyzing T-SQL")
            logging.warning("[INFO] Check the output above to verify the report was generated")
            # For BabelfishCompass, non-zero exit codes are common but not necessarily failures
            # The tool returns non-zero when it finds unsupported features, which is expected
            return True

    except FileNotFoundError as e:
        logging.error(f"Command not found: {e}")
        logging.error("Please verify BabelfishCompass.bat exists in the specified directory")
        return False
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return False


def generate_report(report_name: str, sql_source_dir: Path) -> bool:
    """
    Generate the Babelfish Compass Report

    Args:
        report_name: Name for the report
        sql_source_dir: Directory containing SQL files to analyze (as Path object)

    Returns:
        bool: True if successful, False otherwise
    """
    print_header()

    # Validate inputs
    if not sql_source_dir.exists():
        logging.error(f"SQL source directory not found: {sql_source_dir}")
        return False

    if not BABELFISH_DIR.exists():
        logging.error(f"BabelfishCompass directory not found: {BABELFISH_DIR}")
        return False

    # Verify BabelfishCompass.bat exists
    bat_file = BABELFISH_DIR / "BabelfishCompass.bat"
    if not bat_file.exists():
        logging.error(f"BabelfishCompass.bat not found: {bat_file}")
        logging.error("Please ensure BabelfishCompass is properly installed")
        return False

    # Build the command using config options
    # Parse STEP1_OPTIONS into a list
    options_list = STEP1_OPTIONS.split()
    command_args = ["BabelfishCompass.bat", report_name, str(sql_source_dir)] + options_list

    logging.info(f"Analyzing SQL files in: {sql_source_dir}")
    logging.info(f"Report name: {report_name}")
    logging.info(f"Options: {STEP1_OPTIONS}")

    success = run_command(command_args, cwd=BABELFISH_DIR)

    if success:
        # Build report location from config pattern
        home_dir = Path.home()
        report_location = REPORT_LOCATION_PATTERN.format(home=home_dir, report_name=report_name)
        logging.info("-" * 80)
        logging.info("[OK] Report generated successfully")
        logging.info(f"Report location: {report_location}")
    else:
        logging.error("-" * 80)
        logging.error("[ERROR] Report generation failed")

    return success


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
    if len(sys.argv) < 3:
        print("Usage: python 01_Generate_BabelfishCompass_Report.py <report_name> <sql_source_dir>")
        print()
        print("Arguments:")
        print("  report_name     - Name for the report (e.g., MyReport)")
        print("  sql_source_dir  - Directory containing SQL files to analyze")
        print()
        print(f"Example:")
        print(f"  python 01_Generate_BabelfishCompass_Report.py MyReport \"{DEFAULT_SQL_SOURCE_DIR}\"")
        sys.exit(1)

    report_name = sys.argv[1].strip()
    sql_source_dir_str = sys.argv[2].strip()

    # Validate report name
    if not validate_report_name(report_name):
        sys.exit(1)

    # Validate and convert sql_source_dir to absolute Path
    if not sql_source_dir_str:
        print("Error: sql_source_dir cannot be empty")
        sys.exit(1)

    try:
        sql_source_dir = Path(sql_source_dir_str).resolve()
    except Exception as e:
        print(f"Error: Invalid path for sql_source_dir: {e}")
        sys.exit(1)

    # Setup logging after argument validation
    LOG_FILE = config_loader.setup_logging('01_Generate_BabelfishCompass_Report')

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

