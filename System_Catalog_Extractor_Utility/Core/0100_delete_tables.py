import os
import sys
import logging
import sqlite3
import configparser
from pathlib import Path
from datetime import datetime

# ===================== Configuration =====================
# Load configuration from config.ini
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
    COMMIT_EVERY_N_TABLES = config.getint('Database', 'commit_every_n_tables', fallback=10)

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

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_0100_delete_tables_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

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
logging.info("Starting SQLite cleanup script")
logging.info(f"Using database: {SQLITE_DB_PATH}")
logging.info(f"Log file: {LOG_FILE}")

conn = None
try:
    # ----- Connect -----
    if not SQLITE_DB_PATH.exists():
        logging.info(f"SQLite database not found: {SQLITE_DB_PATH}")
        logging.info("Database does not exist yet - nothing to delete. Skipping cleanup.")
        # Execution complete - check log files
        exit(0)  # Exit successfully

    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cur = conn.cursor()
    logging.info("Connected to SQLite database: %s", SQLITE_DB_PATH)

    # ----- Discover all tables -----
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    all_tables = [row[0] for row in cur.fetchall()]
    logging.info("Found %d tables.", len(all_tables))

    # ----- Truncate all tables -----
    # SQLite doesn't have TRUNCATE, so we use DELETE
    # We don't need to worry about FK order since we're clearing everything
    total_deleted = 0
    processed = 0

    for tbl in all_tables:
        stmt = f'DELETE FROM "{tbl}"'
        try:
            cur.execute(stmt)
            count = cur.rowcount if cur.rowcount is not None else 0
            total_deleted += (count if count and count > 0 else 0)
            processed += 1
            logging.info("Cleared table %s (deleted %s rows)", tbl, count)
            if processed % COMMIT_EVERY_N_TABLES == 0:
                conn.commit()
                logging.info("Intermediate commit after %d tables", processed)
        except Exception as e:
            logging.error("Failed to clear table %s: %s", tbl, e)
            raise

    conn.commit()
    logging.info("All deletes committed. Total rows deleted: %s", total_deleted)

    # ----- Reset SQLite autoincrement sequences -----
    # SQLite stores autoincrement info in sqlite_sequence table
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        if cur.fetchone():
            cur.execute("DELETE FROM sqlite_sequence")
            logging.info("Reset all autoincrement sequences")
            conn.commit()
        else:
            logging.info("No autoincrement sequences to reset")
    except Exception as e:
        logging.warning("Could not reset autoincrement sequences: %s", e)

    # ----- VACUUM database to reclaim space and optimize -----
    logging.info("Running VACUUM to reclaim space and optimize database...")
    try:
        # VACUUM cannot be run inside a transaction, so we need to commit first
        conn.commit()
        # Close cursor before VACUUM
        cur.close()
        # VACUUM requires isolation_level=None (autocommit mode)
        conn.isolation_level = None
        vacuum_cur = conn.cursor()
        vacuum_cur.execute("VACUUM")
        vacuum_cur.close()
        logging.info("VACUUM completed successfully")

        # Get database file size
        db_size_mb = SQLITE_DB_PATH.stat().st_size / (1024 * 1024)
        logging.info(f"Database size after VACUUM: {db_size_mb:.2f} MB")
    except Exception as e:
        logging.error("VACUUM failed: %s", e)
        raise

    logging.info("Cleanup complete.")
    # Execution complete - check log files

except Exception as e:
    logging.exception("Cleanup failed: %s", e)
    try:
        if conn:
            conn.rollback()
    except Exception:
        pass
    raise
finally:
    if conn:
        try:
            # Close cursor if it exists
            if 'cur' in locals() and cur:
                try:
                    cur.close()
                except:
                    pass
            # Close connection
            conn.close()
            logging.info("Connection closed.")
        except Exception as e:
            logging.warning("Error closing connection: %s", e)