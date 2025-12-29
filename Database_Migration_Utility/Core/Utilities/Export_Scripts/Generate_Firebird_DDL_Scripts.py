import re
import sys
import logging
import subprocess
import configparser
from pathlib import Path
from datetime import datetime

# ===== Load script_executer_config.ini =====
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
ISQL_EXE   = r"C:\Program Files\Firebird\Firebird_5_0\isql.exe"  # You can move this to config if needed
DB_PATH    = config.get("Paths", "DB_PATH")
DB_USER    = config.get("Database", "DB_USER")
DB_PASS    = config.get("Database", "DB_PASSWORD")
DB_CHARSET = config.get("Database", "DB_CHARSET")

# === Setup Logging ===
script_dir = Path(__file__).resolve().parent
logs_dir = script_dir / "Logs"
logs_dir.mkdir(parents=True, exist_ok=True)  # Create Logs folder if it doesn't exist
log_filename = f"log_Generate_Firebird_DDL_Scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
logger.info("Generate Firebird DDL Scripts - Started")
logger.info("="*80)

def export_ddl(isql_exe: str, db_path: str, user: str, pwd: str, charset: str, out_file: Path):
    logger.info(f"Executing isql command to export DDL")
    logger.info(f"Database: {db_path}")
    logger.info(f"Output file: {out_file}")
    cmd = [isql_exe, "-user", user, "-password", pwd, "-ch", charset, "-a", db_path]
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "wb") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error_msg = f"isql failed (exit {proc.returncode}).\n{proc.stderr.decode(errors='replace')}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    logger.info("DDL export command completed successfully")

def prompt_db_path(default_path: str) -> str:
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

def main():
    base = Path(__file__).resolve().parent
    out_dir = base / "Generated_Firebird_DDL"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {out_dir}")

    # --- Prompt user to confirm or change DB path ---
    logger.info(f"Default database path: {DB_PATH}")
    chosen_db = prompt_db_path(DB_PATH)
    logger.info(f"Using database path: {chosen_db}")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    db_stem = Path(chosen_db).stem
    ddl_file = out_dir / f"{db_stem}.DDL_{ts}.sql"

    print(f"\n📄 Exporting full DDL to: {ddl_file}")
    logger.info(f"DDL output file: {ddl_file}")

    if not Path(ISQL_EXE).exists():
        error_msg = f"isql.exe not found: {ISQL_EXE}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)
    if not Path(chosen_db).exists():
        error_msg = f"Database not found: {chosen_db}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

    logger.info(f"isql.exe path: {ISQL_EXE}")

    try:
        export_ddl(ISQL_EXE, chosen_db, DB_USER, DB_PASS, DB_CHARSET, ddl_file)
        print(f"\n✅ DDL export complete: {ddl_file}")
        logger.info(f"DDL export completed successfully: {ddl_file}")
    except Exception as ex:
        error_msg = f"DDL export failed: {ex}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

    logger.info("="*80)
    logger.info("Generate Firebird DDL Scripts - Completed")
    logger.info("="*80)
    logger.info(f"Log file saved to: {log_path}")

if __name__ == "__main__":
    main()
    print(f"\n📄 Log file saved to: {log_path}")
    print("")
    input("Press any key to continue...")
