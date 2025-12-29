import os
import csv
import sys
import json
import logging
import configparser
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

# === Load script_executer_config.ini ===
def load_config():
    """Load configuration from script_executer_config.ini in Core directory"""
    # Navigate from Core/Utilities/Import_Scripts to Core directory
    script_path = Path(__file__).resolve().parent.parent.parent
    config_path = script_path / "script_executer_config.ini"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

config = load_config()

# Extract configuration values
PYTHON_SCRIPT_TABLE = config.get("Database_Queries", "PYTHON_SCRIPT_TABLE", fallback="repository_python_script_detail")
PYTHON_SCRIPT_ID_COLUMN = config.get("Database_Queries", "PYTHON_SCRIPT_ID_COLUMN", fallback="pythonscriptsummaryid")

# === Setup Logging ===
script_dir_path = Path(__file__).resolve().parent
logs_dir = script_dir_path / "Logs"
logs_dir.mkdir(parents=True, exist_ok=True)  # Create Logs folder if it doesn't exist
log_filename = f"log_Create_Insert_Statements_From_Scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_path = logs_dir / log_filename

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Log file created: {log_path}")
logger.info("="*80)
logger.info("Create Insert Statements From Scripts - Started")
logger.info("="*80)

def script_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def parse_args():
    p = ArgumentParser(description="Generate INSERT statements from CSV + script files")
    p.add_argument("--csv", dest="csv_path", default=None,
                   help="Path to script_import_manifest.csv (defaults to script folder)")
    return p.parse_args()

def print_csv_as_json(csv_path: str):
    print("\n📄 Previewing contents of CSV as JSON:")
    logger.info(f"Reading CSV file: {csv_path}")
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            if not rows:
                print("⚠️ CSV file is empty.")
                logger.warning("CSV file is empty")
            else:
                print(json.dumps(rows, indent=4))
                logger.info(f"CSV contains {len(rows)} row(s)")
    except Exception as e:
        error_msg = f"Could not read CSV file: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

    # Ask user to confirm
    choice = input("\nProceed with processing this file? [Y]es / [N]o: ").strip().lower()
    if choice not in ("", "y", "yes"):
        print("❌ Operation cancelled by user.")
        logger.info("Operation cancelled by user")
        sys.exit(0)
    logger.info("User confirmed to proceed with processing")

def main():
    args = parse_args()
    base_dir = script_dir()
    logger.info(f"Script directory: {base_dir}")

    csv_path = args.csv_path or os.path.join(base_dir, "script_import_manifest.csv")
    logger.info(f"CSV path: {csv_path}")

    if not os.path.exists(csv_path):
        error_msg = f"CSV file not found: {csv_path}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

    # ✅ Preview CSV as JSON and confirm
    print_csv_as_json(csv_path)

    # Output setup
    csv_folder = os.path.dirname(csv_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(csv_folder, "Output")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    output_sql_path = os.path.join(
        output_dir,
        f"Output_Insert_Statements_{timestamp}.sql"
    )
    logger.info(f"Output SQL file: {output_sql_path}")

    try:
        logger.info("Starting to process CSV and generate INSERT statements")
        total_files_processed = 0
        total_lines_processed = 0

        with open(csv_path, 'r', encoding='utf-8', newline='') as csv_file, \
             open(output_sql_path, 'w', encoding='utf-8') as sql_file:

            reader = csv.reader(csv_file)
            headers = next(reader, None)
            logger.info(f"CSV headers: {headers}")

            for row_num, row in enumerate(reader, start=2):
                if len(row) != 5:
                    warning_msg = f"Skipping row {row_num}: expected 5 columns, got {len(row)} → {row}"
                    print(warning_msg)
                    logger.warning(warning_msg)
                    continue

                summary_id, filepath, filename, filetype, notes = row
                summary_id = summary_id.strip()
                logger.info(f"Processing row {row_num}: ID={summary_id}, File={filename}, Type={filetype}")

                if not os.path.isabs(filepath):
                    filepath = os.path.join(csv_folder, filepath)

                if not os.path.exists(filepath):
                    warning_msg = f"File not found: {filepath}"
                    print(warning_msg)
                    logger.warning(warning_msg)
                    continue

                logger.info(f"Reading script file: {filepath}")
                line_count = 0

                with open(filepath, 'r', encoding='utf-8', errors='replace') as script_file:
                    for i, line in enumerate(script_file, start=1):
                        sanitized_line = line.rstrip('\n').replace("'", "''")
                        sql = (
                            f"INSERT INTO {PYTHON_SCRIPT_TABLE} "
                            f"({PYTHON_SCRIPT_ID_COLUMN}, linenumber, filename, filetype, scripttext, notes) "
                            f"VALUES ({summary_id}, {i}, '{filename}', '{filetype}', '{sanitized_line}', '{notes}');\n"
                        )
                        sql_file.write(sql)
                        line_count += 1

                logger.info(f"Generated {line_count} INSERT statements for {filename}")
                total_files_processed += 1
                total_lines_processed += line_count

        print(f"\n✅ SQL insert file created: {output_sql_path}")
        logger.info(f"SQL insert file created: {output_sql_path}")
        logger.info(f"Total files processed: {total_files_processed}")
        logger.info(f"Total INSERT statements generated: {total_lines_processed}")

    except Exception as e:
        error_msg = f"Error: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)

    logger.info("="*80)
    logger.info("Create Insert Statements From Scripts - Completed")
    logger.info("="*80)
    logger.info(f"Log file saved to: {log_path}")

    print('')
    print(f"📄 Log file saved to: {log_path}")
    print('')
    input("\nPress any key to continue...")

if __name__ == "__main__":
    main()
