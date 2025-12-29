import os
import sys
import logging
import sqlite3
import configparser
from pathlib import Path
from datetime import datetime

# ===================== Configuration =====================
# Load config.ini
config = configparser.ConfigParser()
CONFIG_FILE = Path("C:/Advanced_SQL_Server_Toolkit/System_Catalog_Extractor_Utility/Config/config.ini")

if not CONFIG_FILE.exists():
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Config directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values
try:
    WORKSPACE_DIR = Path(config.get('Paths', 'workspace_dir'))
    LOG_DIR = WORKSPACE_DIR / config.get('Paths', 'log_dir')
    SQLITE_DIR = WORKSPACE_DIR / config.get('Paths', 'sqlite_dir')

    # Database configuration
    SQLITE_DB_NAME = config.get('Database', 'sqlite_db_name')

    # Logging configuration
    LOG_LEVEL = config.get('Logging', 'log_level')
    LOG_FORMAT = config.get('Logging', 'log_format')
    TIMESTAMP_FORMAT = config.get('Logging', 'timestamp_format')
    LOG_FILEMODE = config.get('Logging', 'log_filemode', fallback='a')

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)

# Ensure directories exist
SQLITE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = SQLITE_DIR / SQLITE_DB_NAME

# Summary table configuration
SUMMARY_TABLE_NAME = "summary_table_information"

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_0400_etl_summary_statistics_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

# Map log level string to logging constant
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

logging.info("=" * 80)
logging.info("Starting Summary Statistics ETL Script")
logging.info(f"Using database: {SQLITE_DB_PATH}")
logging.info(f"Log file: {LOG_FILE}")
logging.info("=" * 80)

conn = None
try:
    # ----- Connect to SQLite -----
    if not SQLITE_DB_PATH.exists():
        logging.error(f"SQLite database not found: {SQLITE_DB_PATH}")
        raise FileNotFoundError(f"Database file does not exist: {SQLITE_DB_PATH}")

    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cur = conn.cursor()
    logging.info("Connected to SQLite database")

    # ----- Create summary table if it doesn't exist -----
    logging.info(f"Creating summary table: {SUMMARY_TABLE_NAME}")
    create_summary_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {SUMMARY_TABLE_NAME} (
        table_name TEXT NOT NULL,
        full_domain_name TEXT,
        host_name TEXT,
        database_name TEXT,
        insert_date TEXT,
        row_count INTEGER NOT NULL,
        summary_generated_date TEXT NOT NULL,
        PRIMARY KEY (table_name, full_domain_name, host_name, database_name, insert_date)
    )
    """
    cur.execute(create_summary_table_sql)
    conn.commit()
    logging.info(f"Summary table '{SUMMARY_TABLE_NAME}' is ready")

    # ----- Truncate summary table -----
    logging.info(f"Truncating summary table: {SUMMARY_TABLE_NAME}")
    cur.execute(f"DELETE FROM {SUMMARY_TABLE_NAME}")
    conn.commit()
    logging.info(f"Summary table truncated")

    # ----- Get all tables except the summary table itself -----
    cur.execute(f"""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name != '{SUMMARY_TABLE_NAME}'
          AND name != 'sqlite_sequence'
        ORDER BY name
    """)
    all_tables = [row[0] for row in cur.fetchall()]
    logging.info(f"Found {len(all_tables)} tables to analyze")

    # ----- Process each table -----
    total_summary_rows = 0
    summary_generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for table_name in all_tables:
        try:
            logging.info(f"Processing table: {table_name}")

            # Check if table has the required columns
            cur.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cur.fetchall()]
            
            required_columns = ['full_domain_name', 'host_name', 'database_name', 'insert_date']
            has_required_columns = all(col in columns for col in required_columns)

            if not has_required_columns:
                logging.warning(f"  Table '{table_name}' does not have required columns. Skipping.")
                logging.warning(f"  Required: {required_columns}")
                logging.warning(f"  Found: {columns[:10]}...")  # Show first 10 columns
                continue

            # Generate summary statistics for this table
            summary_sql = f"""
                SELECT 
                    '{table_name}' as table_name,
                    full_domain_name,
                    host_name,
                    database_name,
                    insert_date,
                    COUNT(*) as row_count,
                    '{summary_generated_date}' as summary_generated_date
                FROM {table_name}
                GROUP BY full_domain_name, host_name, database_name, insert_date
            """
            
            cur.execute(summary_sql)
            summary_rows = cur.fetchall()

            if not summary_rows:
                logging.info(f"  Table '{table_name}' is empty. No summary rows generated.")
                continue

            # Insert summary rows into summary table
            insert_sql = f"""
                INSERT INTO {SUMMARY_TABLE_NAME} 
                (table_name, full_domain_name, host_name, database_name, insert_date, row_count, summary_generated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            cur.executemany(insert_sql, summary_rows)
            conn.commit()

            total_summary_rows += len(summary_rows)
            logging.info(f"  Generated {len(summary_rows)} summary row(s) for table '{table_name}'")

        except Exception as e:
            logging.error(f"  Error processing table '{table_name}': {e}")
            # Continue with next table instead of failing completely
            continue

    # ----- Final summary -----
    logging.info("=" * 80)
    logging.info(f"Summary Statistics ETL Complete!")
    logging.info(f"  Tables analyzed: {len(all_tables)}")
    logging.info(f"  Total summary rows generated: {total_summary_rows}")
    logging.info(f"  Summary table: {SUMMARY_TABLE_NAME}")
    logging.info("=" * 80)

    # ----- Show sample of summary table -----
    logging.info("Sample of summary table (first 10 rows):")
    cur.execute(f"""
        SELECT table_name, full_domain_name, host_name, database_name, insert_date, row_count
        FROM {SUMMARY_TABLE_NAME}
        ORDER BY table_name, database_name
        LIMIT 10
    """)
    sample_rows = cur.fetchall()
    for row in sample_rows:
        logging.info(f"  {row[0]}: {row[1]}/{row[2]}/{row[3]} ({row[4]}) = {row[5]} rows")

except Exception as e:
    logging.exception(f"Summary statistics ETL failed: {e}")
    if conn:
        try:
            conn.rollback()
        except Exception:
            pass
    raise
finally:
    if conn:
        try:
            if 'cur' in locals() and cur:
                try:
                    cur.close()
                except:
                    pass
            conn.close()
            logging.info("Connection closed.")
            # Execution complete - check log files
        except Exception as e:
            logging.warning(f"Error closing connection: {e}")

