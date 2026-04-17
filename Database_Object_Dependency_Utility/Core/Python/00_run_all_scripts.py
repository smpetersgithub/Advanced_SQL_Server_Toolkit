"""
Master script to run all Python scripts in order.

This script:
1. Cleans the Output directory
2. Runs all scripts in sequence:
   - 01_extract_complete_ui_mapping.py
   - 02_generate_dependency_report_reverse_ui_lookup.py
   - 03_create_final_ui_mappings.py
   - 04_generate_dependency_report_reverse.py
   - 05_generate_dependency_report_forward.py
   - 06_create_final_excel_file.py
   - 07_format_excel_file.py
   - 08_open_excel_file.py
"""

import os
import sys
import shutil
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def setup_logging(log_dir):
    """
    Configure logging for the master script.

    Args:
        log_dir: Directory for log files

    Returns:
        Logger instance
    """
    # Create log directory if it doesn't exist
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir_path / f'00_run_all_scripts_{timestamp}.log'

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def clean_output_directory(output_dir, logger):
    """
    Delete all contents of the output directory.

    Args:
        output_dir: Path to the output directory
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("="*60)
    logger.info("CLEANING OUTPUT DIRECTORY")
    logger.info("="*60)
    logger.info(f"Output directory: {output_dir}")

    output_path = Path(output_dir)

    if not output_path.exists():
        logger.info(f"Output directory does not exist. Creating: {output_dir}")
        output_path.mkdir(parents=True, exist_ok=True)
        return True

    try:
        # Get list of files and directories
        items = list(output_path.iterdir())

        if not items:
            logger.info("Output directory is already empty.")
            return True

        logger.info(f"Found {len(items)} items to delete:")

        # Delete all files and subdirectories
        for item in items:
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                    logger.info(f"  Deleted file: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"  Deleted directory: {item.name}")
            except Exception as e:
                logger.error(f"  ERROR deleting {item.name}: {e}")
                return False

        logger.info("Output directory cleaned successfully!")
        return True

    except Exception as e:
        logger.error(f"ERROR: Failed to clean output directory: {e}")
        return False

def run_script(script_name, script_dir, logger):
    """
    Run a Python script and return success status.

    Args:
        script_name: Name of the script to run
        script_dir: Directory containing the script
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("\n" + "="*60)
    logger.info(f"RUNNING: {script_name}")
    logger.info("="*60)

    script_path = Path(script_dir) / script_name

    if not script_path.exists():
        logger.error(f"ERROR: Script not found: {script_path}")
        return False

    try:
        # Run the script using subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_dir),
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"\n✓ {script_name} completed successfully!")
            return True
        else:
            logger.error(f"\n✗ {script_name} failed with return code: {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"\n✗ ERROR running {script_name}: {e}")
        return False

def main():
    """Main execution function."""
    start_time = datetime.now()

    # Load configuration first (before logging setup)
    try:
        config = ConfigLoader()
    except Exception as e:
        print(f"FATAL ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    # Get paths (config loader now returns absolute paths)
    script_dir = Path(__file__).parent
    output_dir = Path(config.get_output_dir())
    log_dir = Path(config.get_log_dir())

    # Setup logging
    logger = setup_logging(log_dir)

    logger.info("\n" + "="*60)
    logger.info("MASTER SCRIPT - RUN ALL PYTHON SCRIPTS")
    logger.info("="*60)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    logger.info(f"Script directory: {script_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Log directory: {log_dir}")

    # Step 1: Clean output directory
    if not clean_output_directory(output_dir, logger):
        logger.error("\n" + "="*60)
        logger.error("FAILED: Could not clean output directory")
        logger.error("="*60)
        sys.exit(1)

    # Step 2: Run all scripts in order
    scripts = [
        "01_extract_complete_ui_mapping.py",
        "02_generate_dependency_report_reverse_ui_lookup.py",
        "03_create_final_ui_mappings.py",
        "04_generate_dependency_report_reverse.py",
        "05_generate_dependency_report_forward.py",
        "06_create_final_excel_file.py",
        "07_format_excel_file.py",
        "08_open_excel_file.py"
    ]

    failed_scripts = []

    for script in scripts:
        if not run_script(script, script_dir, logger):
            failed_scripts.append(script)
            logger.warning(f"\n⚠ WARNING: {script} failed. Stopping execution.")
            break

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "="*60)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*60)
    logger.info(f"Start time:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"End time:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration:      {duration}")
    logger.info(f"Total scripts: {len(scripts)}")

    if failed_scripts:
        logger.error(f"Failed:        {len(failed_scripts)}")
        logger.error(f"Failed scripts: {', '.join(failed_scripts)}")
        logger.error("="*60)
        logger.error("STATUS: FAILED ✗")
        logger.error("="*60)
        sys.exit(1)
    else:
        logger.info(f"Completed:     {len(scripts)}")
        logger.info("="*60)
        logger.info("STATUS: SUCCESS ✓")
        logger.info("="*60)

if __name__ == "__main__":
    main()

