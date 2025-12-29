import os
import re
import sys
import logging
import configparser
from datetime import datetime
from pathlib import Path
from firebird.driver import connect, DatabaseError

# === Load script_executer_config.ini ===
def load_config():
    """Load configuration from script_executer_config.ini in Core directory"""
    # Navigate from Core/Utilities/Export_Scripts to Core directory
    script_path = Path(__file__).resolve().parent.parent.parent
    config_path = script_path / "script_executer_config.ini"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

config = load_config()

# Extract configuration values
DEFAULT_DB_PATH = config.get("Paths", "DB_PATH")
DB_USER = config.get("Database", "DB_USER")
DB_PASS = config.get("Database", "DB_PASSWORD")
DB_CHARSET = config.get("Database", "DB_CHARSET")
ADMIN_USER = config.get("Database", "ADMIN_USER", fallback="").strip()

# Database table names
PYTHON_SCRIPT_TABLE = config.get("Database_Queries", "PYTHON_SCRIPT_TABLE", fallback="repository_python_script_detail")
PYTHON_SCRIPT_ID_COLUMN = config.get("Database_Queries", "PYTHON_SCRIPT_ID_COLUMN", fallback="pythonscriptsummaryid")
SQL_SCRIPT_TABLE = config.get("Database_Queries", "SQL_SCRIPT_TABLE", fallback="repository_sql_script_detail")
SQL_SCRIPT_ID_COLUMN = config.get("Database_Queries", "SQL_SCRIPT_ID_COLUMN", fallback="sqlscriptsummaryid")
MASTER_VIEWS_TABLE = config.get("Database_Queries", "MASTER_VIEWS_TABLE", fallback="repository_powershell_master_views")

# === Setup Logging ===
script_dir = Path(__file__).resolve().parent
logs_dir = script_dir / "Logs"
logs_dir.mkdir(parents=True, exist_ok=True)  # Create Logs folder if it doesn't exist
log_filename = f"log_Export_Scripts_From_Firebird_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
logger.info("Export Scripts From Firebird - Started")
logger.info("="*80)

# === Firebird connection helper ===
def prompt_db_path(default_path: str) -> str:
    """Prompt user to confirm or change DB path."""
    print("\nCurrent database path:")
    print(f"  {default_path}")
    choice = input("\nUse this database? [Y]es / [N]o to enter a different path: ").strip().lower()
    if choice in ("", "y", "yes"):
        return default_path

    while True:
        newp = input("\nEnter full path to the Firebird .FDB (or press Enter to use the default): ").strip()
        if not newp:
            return default_path
        candidate = Path(newp.strip('"')).expanduser()
        candidate = Path(str(candidate).replace("%20", " "))
        if candidate.exists():
            return str(candidate)
        print(f"Path not found: {candidate}\nPlease try again.")

# === Ask user for DB path ===
logger.info(f"Default database path: {DEFAULT_DB_PATH}")
db_path = prompt_db_path(DEFAULT_DB_PATH)
logger.info(f"Using database path: {db_path}")

# === Firebird connection ===
print("\n📡 Connecting to Firebird database...")
logger.info("Attempting to connect to Firebird database...")
try:
    conn = connect(
        database=db_path,
        user=DB_USER,
        password=DB_PASS,
        charset=DB_CHARSET
    )
    print("✅ Connected.")
    logger.info("Successfully connected to Firebird database")
except DatabaseError as e:
    error_msg = f"Failed to connect to database: {e}"
    print(f"❌ {error_msg}")
    logger.error(error_msg)
    input("Press any key to exit...")
    exit(1)

# Activate admin role if configured
if ADMIN_USER and DB_USER.lower() == ADMIN_USER.lower():
    conn.execute_immediate("SET ROLE RDB$ADMIN")
    conn.commit()
    logger.info(f"Admin role activated for user: {DB_USER}")

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Exported_Scripts")
os.makedirs(output_dir, exist_ok=True)
print(f"📁 Output directory: {output_dir}")
logger.info(f"Output directory: {output_dir}")

def make_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]

try:
    with conn.cursor() as cur:
        print("🔍 Querying Python script metadata...")
        logger.info("Querying Python script metadata...")
        cur.execute(f"""
            SELECT DISTINCT {PYTHON_SCRIPT_ID_COLUMN}, FILENAME, FILETYPE
            FROM {PYTHON_SCRIPT_TABLE}
            WHERE FILETYPE = 'py'
        """)
        python_scripts = cur.fetchall()
        print(f"📦 Found {len(python_scripts)} Python script(s).")
        logger.info(f"Found {len(python_scripts)} Python script(s)")

        for i, (summary_id, filename, filetype) in enumerate(python_scripts, 1):
            try:
                print(f"\n➡️ [{i}/{len(python_scripts)}] Processing script ID: {summary_id}, File: {filename}")
                logger.info(f"[{i}/{len(python_scripts)}] Processing Python script ID: {summary_id}, File: {filename}")
                cur.execute(f"""
                    SELECT SCRIPTTEXT
                    FROM {PYTHON_SCRIPT_TABLE}
                    WHERE {PYTHON_SCRIPT_ID_COLUMN} = ?
                    ORDER BY LINENUMBER
                """, (summary_id,))
                rows = cur.fetchall()
                print(f"📝 Retrieved {len(rows)} line(s) of script text).")
                logger.info(f"Retrieved {len(rows)} line(s) of script text")

                if not rows:
                    print("⚠️ Skipped: No script lines found.")
                    logger.warning(f"Skipped script ID {summary_id}: No script lines found")
                    continue

                lines = [row[0] for row in rows]
                content = '\n'.join(lines)
                timestamp = make_timestamp()
                safe_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
                final_name = f"{filetype}_{summary_id}_{safe_filename}_{timestamp}.{filetype}"
                final_path = os.path.join(output_dir, final_name)

                with open(final_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Python Exported: {final_name}")
                logger.info(f"Successfully exported Python script: {final_name}")

            except Exception as script_err:
                error_msg = f"Error exporting script ID {summary_id}: {script_err}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)

        print("\n🔍 Querying SQL script metadata...")
        logger.info("Querying SQL script metadata...")
        cur.execute(f"""
            SELECT DISTINCT {SQL_SCRIPT_ID_COLUMN}, FILENAME, FILETYPE
            FROM {SQL_SCRIPT_TABLE}
            WHERE FILETYPE = 'sql'
        """)
        sql_scripts = cur.fetchall()
        print(f"📦 Found {len(sql_scripts)} SQL script(s).")
        logger.info(f"Found {len(sql_scripts)} SQL script(s)")

        for i, (summary_id, filename, filetype) in enumerate(sql_scripts, 1):
            try:
                print(f"\n➡️ [{i}/{len(sql_scripts)}] Processing SQL script ID: {summary_id}, File: {filename}")
                logger.info(f"[{i}/{len(sql_scripts)}] Processing SQL script ID: {summary_id}, File: {filename}")
                cur.execute(f"""
                    SELECT SCRIPTTEXT
                    FROM {SQL_SCRIPT_TABLE}
                    WHERE {SQL_SCRIPT_ID_COLUMN} = ?
                    ORDER BY LINENUMBER
                """, (summary_id,))
                rows = cur.fetchall()
                print(f"📝 Retrieved {len(rows)} line(s) of script text).")
                logger.info(f"Retrieved {len(rows)} line(s) of script text")

                if not rows:
                    print("⚠️ Skipped: No script lines found.")
                    logger.warning(f"Skipped SQL script ID {summary_id}: No script lines found")
                    continue

                lines = [row[0] for row in rows]
                content = '\n'.join(lines)
                timestamp = make_timestamp()
                safe_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
                final_name = f"{filetype}_{summary_id}_{safe_filename}_{timestamp}.{filetype}"
                final_path = os.path.join(output_dir, final_name)

                with open(final_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ SQL Exported: {final_name}")
                logger.info(f"Successfully exported SQL script: {final_name}")

            except Exception as script_err:
                error_msg = f"Error exporting SQL script ID {summary_id}: {script_err}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)

        print("\n🔍 Querying PowerShell master views...")
        logger.info("Querying PowerShell master views...")
        cur.execute(f"""
            SELECT POWERSHELLMASTERVIEWSID, VIEWNAME, VIEWTYPE
            FROM {MASTER_VIEWS_TABLE}
        """)
        views = cur.fetchall()
        print(f"📦 Found {len(views)} PowerShell view(s).")
        logger.info(f"Found {len(views)} PowerShell view(s)")

        for view_id, view_name, view_type in views:
            try:
                print(f"\n➡️ Processing PowerShell View: {view_name} (ID: {view_id})")
                logger.info(f"Processing PowerShell View: {view_name} (ID: {view_id})")

                cur.execute(f"SELECT DISTINCT FILENAME FROM {view_name}")
                filenames = [row[0] for row in cur.fetchall()]
                print(f"📁 Found {len(filenames)} file(s) in view {view_name}.")
                logger.info(f"Found {len(filenames)} file(s) in view {view_name}")

                for filename in filenames:
                    print(f"📄 Processing file: {filename}")
                    logger.info(f"Processing PowerShell file: {filename}")
                    cur.execute(f"""
                        SELECT COMMAND
                        FROM {view_name}
                        WHERE FILENAME = ?
                        ORDER BY FILENAME, ORDERTYPE, ROWID
                    """, (filename,))
                    lines = [row[0] for row in cur.fetchall()]
                    if not lines:
                        print(f"⚠️ Skipped: No command lines for {filename}.")
                        logger.warning(f"Skipped {filename}: No command lines found")
                        continue

                    content = '\n'.join(lines)
                    timestamp = make_timestamp()
                    safe_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
                    final_name = f"{view_type}_{view_id}_{safe_filename}_{timestamp}.ps1"
                    final_path = os.path.join(output_dir, final_name)

                    with open(final_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ PowerShell Exported: {final_name}")
                    logger.info(f"Successfully exported PowerShell script: {final_name}")
            except Exception as ps_err:
                error_msg = f"Error processing PowerShell view {view_name}: {ps_err}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)

except DatabaseError as db_err:
    error_msg = f"Firebird DB error: {db_err}"
    print(f"❌ {error_msg}")
    logger.error(error_msg)
except Exception as e:
    error_msg = f"General error: {e}"
    print(f"❌ {error_msg}")
    logger.error(error_msg)
finally:
    conn.close()
    logger.info("Database connection closed")
    logger.info("="*80)
    logger.info("Export Scripts From Firebird - Completed")
    logger.info("="*80)
    logger.info(f"Log file saved to: {log_path}")
    print("\n✅ All exports completed.")
    print(f"📄 Log file saved to: {log_path}")
    print('')
    input("Press any key to continue...")
