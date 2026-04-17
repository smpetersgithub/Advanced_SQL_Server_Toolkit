"""
Run All Query Store Analysis Scripts

This script orchestrates the execution of all Python scripts in the correct order:
1. Extract query store data
2. Extract XML execution plans (if include_execution_plans is enabled)
3. Extract table names from XML plans (if include_execution_plans is enabled)
4. Extract index and statistics for tables (if analyze_indexes is enabled)
5. Create JSON execution plans (if include_execution_plans is enabled)

The script reads configuration from:
- Config/config.json (Python script settings and paths)
- Config/database-config.json (Database connection: servername, database, username, password)
- Config/reports-config.json (Report definitions)
- Config/active-report-config.json (Active report selection)
"""

import sys
import subprocess
from pathlib import Path
import logging
from config_loader import ConfigLoader


def run_script(script_path, logger):
    """Run a Python script and return success status.

    Args:
        script_path: Path to the Python script to execute
        logger: Logger instance

    Returns:
        bool: True if script executed successfully, False otherwise

    Raises:
        FileNotFoundError: If script doesn't exist
    """
    # Validate script exists
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if not script_path.is_file():
        raise ValueError(f"Path is not a file: {script_path}")

    script_name = script_path.name
    logger.info(f"{'='*80}")
    logger.info(f"Starting: {script_name}")
    logger.info(f"{'='*80}")

    try:
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=3600  # 1 hour timeout to prevent hanging
        )

        # Log the output
        if result.stdout:
            logger.info(f"Output from {script_name}:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")

        # Check for errors
        if result.returncode != 0:
            logger.error(f"ERROR: {script_name} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output:")
                for line in result.stderr.splitlines():
                    logger.error(f"  {line}")
            return False

        logger.info(f"SUCCESS: {script_name} completed successfully")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {script_name} exceeded 1 hour execution time")
        return False
    except Exception as e:
        logger.error(f"EXCEPTION: Failed to run {script_name}: {str(e)}")
        return False


def main():
    """Main orchestration function."""
    # Initialize config loader
    try:
        config = ConfigLoader()
        active_report_key, report_settings = config.get_active_report_settings()
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {str(e)}")
        sys.exit(1)

    # Setup logging - returns the log file path
    log_file = config.setup_logging('run_all_scripts')

    # Get logger instance
    logger = logging.getLogger(__name__)

    logger.info("="*80)
    logger.info("Query Store Analysis - Running All Scripts")
    logger.info("="*80)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"Report Name: {report_settings['name']}")

    # Get processing settings
    processing = report_settings.get('processing', {})
    include_execution_plans = processing.get('include_execution_plans', True)
    analyze_indexes = processing.get('analyze_indexes', True)

    logger.info(f"Include Execution Plans: {include_execution_plans}")
    logger.info(f"Analyze Indexes: {analyze_indexes}")
    logger.info("")

    # Get the Python scripts directory
    scripts_dir = Path(__file__).parent

    # Define all available scripts
    all_scripts = {
        'extract_data': scripts_dir / "01_extract_query_store_data.py",
        'extract_plans': scripts_dir / "02_extract_xml_execution_plans.py",
        'extract_tables': scripts_dir / "03_extract_table_names_from_xml_plans.py",
        'extract_indexes': scripts_dir / "04_extract_index_and_statistics_for_tables.py",
        'create_json_plans': scripts_dir / "05_create_json_execution_plans.py"
    }

    # Build the list of scripts to run based on configuration
    scripts_to_run = []

    # Script 1 always runs
    scripts_to_run.append(all_scripts['extract_data'])

    # Scripts 2, 3, 5 only run if include_execution_plans is enabled
    if include_execution_plans:
        scripts_to_run.append(all_scripts['extract_plans'])
        scripts_to_run.append(all_scripts['extract_tables'])

        # Script 4 runs if either analyze_indexes is enabled OR include_execution_plans is enabled
        if analyze_indexes:
            scripts_to_run.append(all_scripts['extract_indexes'])

        scripts_to_run.append(all_scripts['create_json_plans'])
    else:
        # If execution plans are disabled but analyze_indexes is enabled, still run script 4
        if analyze_indexes:
            logger.info("Note: Execution plans disabled, but analyze_indexes is enabled")
            logger.info("      Index analysis will be limited without table names from plans")
            scripts_to_run.append(all_scripts['extract_indexes'])

    # Verify all scripts exist
    for script in scripts_to_run:
        if not script.exists():
            logger.error(f"ERROR: Script not found: {script}")
            sys.exit(1)

    logger.info(f"Scripts to execute: {len(scripts_to_run)}")
    for i, script in enumerate(scripts_to_run, 1):
        logger.info(f"  {i}. {script.name}")
    logger.info("")
    
    # Run each script in sequence
    success_count = 0
    failed_scripts = []

    for i, script in enumerate(scripts_to_run, 1):
        logger.info(f"[{i}/{len(scripts_to_run)}] Executing: {script.name}")

        if run_script(script, logger):
            success_count += 1
        else:
            failed_scripts.append(script.name)
            logger.error(f"Script {script.name} failed. Stopping execution.")
            break

    # Final summary
    logger.info("")
    logger.info("="*80)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total scripts: {len(scripts_to_run)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {len(failed_scripts)}")

    if failed_scripts:
        logger.error(f"Failed scripts: {', '.join(failed_scripts)}")
        logger.error("Analysis incomplete - please check the logs for errors")
        sys.exit(1)
    else:
        logger.info("All scripts completed successfully!")
        logger.info("Analysis complete - results are available in the Output directory")
        sys.exit(0)


if __name__ == "__main__":
    main()

