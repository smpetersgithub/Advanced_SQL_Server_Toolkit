# etl_system_catalog.py
import os
import sys
import json
import logging
import sqlite3
import configparser
import datetime as _dt
import decimal as _dec
from pathlib import Path
from datetime import datetime

import pyodbc

# ===================== Load Configuration =====================
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
    CONFIG_DIR = WORKSPACE_DIR / config.get('Paths', 'config_dir')
    LOG_DIR = WORKSPACE_DIR / config.get('Paths', 'log_dir')
    SQLITE_DIR = WORKSPACE_DIR / config.get('Paths', 'sqlite_dir')

    # Database configuration
    SQLITE_DB_NAME = config.get('Database', 'sqlite_db_name')
    BATCH_SIZE = config.getint('Database', 'batch_size', fallback=1000)

    # Logging configuration
    LOG_LEVEL = config.get('Logging', 'log_level')
    LOG_FORMAT = config.get('Logging', 'log_format')
    TIMESTAMP_FORMAT = config.get('Logging', 'timestamp_format')
    LOG_FILEMODE = config.get('Logging', 'log_filemode', fallback='a')

    # Configuration files
    SQL_SERVER_CONNECTIONS_FILE = config.get('Paths', 'sql_server_connections_file')
    DATA_MANAGEMENT_VIEWS_FILE = config.get('Paths', 'data_management_views_file')

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)

# Ensure directories exist
SQLITE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = SQLITE_DIR / SQLITE_DB_NAME

def load_json_config(filename):
    """Load JSON configuration file"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load JSON configurations
server_config = load_json_config(SQL_SERVER_CONNECTIONS_FILE)
dmv_config = load_json_config(DATA_MANAGEMENT_VIEWS_FILE)

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_0200_etl_system_catalog_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

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

logging.info("Starting ETL (Config=JSON, Target=SQLite, Source=SQL Server)")
logging.info(f"SQLite DB: {SQLITE_DB_PATH}")
logging.info(f"Log file: {LOG_FILE}")

# Get active servers from config
active_servers = [s for s in server_config['servers'] if s.get('active', False)]
if not active_servers:
    logging.error("No active servers found in config/sql_server_connections.json")
    sys.exit(1)

logging.info(f"Found {len(active_servers)} active server(s) in configuration")

# ---------- Helpers ----------
def build_sql_conn_str(server, user, password, db_name="master", driver_hint=None):
    """Build an ODBC connection string. Try Driver 17 by default; if hint='18', use 18."""
    driver = "ODBC Driver 17 for SQL Server" if driver_hint != "18" else "ODBC Driver 18 for SQL Server"
    return f"DRIVER={{{driver}}};SERVER={server};UID={user};PWD={password};DATABASE={db_name};"

def try_sqlserver_connect(conn_str):
    return pyodbc.connect(conn_str, timeout=10)

def get_user_databases(server, user, password):
    """Get user DBs from SQL Server. Try ODBC 17 then 18."""
    for drv in (None, "18"):
        try:
            conn_str = build_sql_conn_str(server, user, password, "master", driver_hint=drv)
            with try_sqlserver_connect(conn_str) as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT name
                    FROM sys.databases
                    WHERE name NOT IN ('master','tempdb','model','msdb') AND state = 0
                """)
                dbs = [row[0] for row in cur.fetchall()]
                logging.info(f"[{server}] Found {len(dbs)} user databases (driver={drv or '17'}).")
                return dbs, (drv or "17")
        except Exception as e:
            logging.warning(f"[DB List] Failed with driver {drv or '17'}: {e}")
    logging.error(f"[DB List] Could not connect to SQL Server {server} with ODBC Driver 17/18.")
    return [], None

def get_active_dmvs():
    """Get list of active DMVs from config (excludes DMFs)"""
    active_dmvs = [
        dmv['data_management_view']
        for dmv in dmv_config['data_management_objects']
        if dmv.get('isactive', 0) == 1 and dmv.get('object_type', 'dmv') == 'dmv'
    ]

    # Count excluded DMFs for logging
    excluded_dmfs = [
        dmv['data_management_view']
        for dmv in dmv_config['data_management_objects']
        if dmv.get('isactive', 0) == 1 and dmv.get('object_type', 'dmv') == 'dmf'
    ]

    logging.info(f"Loaded {len(active_dmvs)} active DMVs from configuration")
    if excluded_dmfs:
        logging.info(f"Excluded {len(excluded_dmfs)} active DMFs (require parameters): {', '.join(excluded_dmfs)}")

    return active_dmvs

def sanitize_table_name(name: str) -> str:
    """Convert DMV name to valid SQLite table name"""
    return name.replace(".", "_").replace("-", "_")

# ---- Type mapping for SQLite DDL from pyodbc cursor.description ----
def _sqlite_type_from_desc(desc):
    """
    Map pyodbc column description to a SQLite type.
    desc: (name, type_code, display_size, internal_size, precision, scale, null_ok)
    """
    name, tcode, dsize, isize, prec, scale, nullok = desc

    # Dates/Times
    if tcode in (_dt.datetime, _dt.date, _dt.time):
        return "TEXT"

    # Numerics
    if tcode is int:
        return "INTEGER"
    if tcode is float:
        return "REAL"
    if tcode is _dec.Decimal:
        return "REAL"

    # Binary
    if tcode in (bytes, bytearray, memoryview):
        return "BLOB"

    # Text / everything else
    return "TEXT"

def _uniquify(cols):
    """Ensure unique column names (keep order, suffix _2, _3 on dup)."""
    seen = {}
    out = []
    for c in cols:
        base = c
        i = 1
        while base.lower() in seen:
            i += 1
            base = f"{c}_{i}"
        seen[base.lower()] = True
        out.append(base)
    return out

def build_sqlite_columns_from_description(description):
    """
    Take pyodbc cursor.description and produce list[(colname, sqlite_type_sql)].
    - Ensures unique column names.
    """
    names = [d[0] for d in description]
    names = _uniquify(names)
    types = [_sqlite_type_from_desc(d) for d in description]
    cols = list(zip(names, types))
    return cols

def table_exists(sqlite_cur, table_name: str) -> bool:
    """Check if table exists in SQLite"""
    sqlite_cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return sqlite_cur.fetchone() is not None

def create_table_if_needed(sqlite_conn, sqlite_cur, table_name: str, description):
    """
    Create target table from pyodbc description if it doesn't exist.
    """
    if table_exists(sqlite_cur, table_name):
        return False

    cols = build_sqlite_columns_from_description(description)
    ddl_cols = [f'"{n}" {t}' for n, t in cols]
    ddl = f"CREATE TABLE \"{table_name}\" ({', '.join(ddl_cols)})"
    sqlite_cur.execute(ddl)
    sqlite_conn.commit()
    logging.info(f"[SQLite] Created table: {table_name} with {len(cols)} columns")
    return True

def truncate_table(sqlite_cur, table_name: str):
    sqlite_cur.execute(f'DELETE FROM "{table_name}"')
    logging.info(f"[SQLite] Cleared table: {table_name}")

# ---- SQLite Database Setup ----
def ensure_sqlite_db_exists(db_path):
    """Create SQLite database if it doesn't exist"""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.close()
        logging.info(f"SQLite database ready: {db_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create SQLite database: {e}")
        return False

# ---------- Get active DMVs from config ----------
system_tables = get_active_dmvs()
if not system_tables:
    logging.error("No active DMVs found in configuration")
    sys.exit(1)

# ---------- Ensure SQLite DB exists ----------
if not ensure_sqlite_db_exists(SQLITE_DB_PATH):
    sys.exit(1)

# ---------- Connect to SQLite DB ----------
try:
    sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
    sqlite_cur = sqlite_conn.cursor()
    logging.info(f"Connected to SQLite DB: {SQLITE_DB_PATH}")
except Exception as e:
    logging.exception(f"Failed to connect to SQLite DB: {e}")
    sys.exit(1)

# ---------- Process each active server ----------
for server_info in active_servers:
    server_name = server_info['servername']
    username = server_info['username']
    password = server_info['password']
    databases_include = server_info.get('databases_include', [])  # Get include list, default to empty

    logging.info(f"Processing server: {server_name}")
    logging.info(f"  Username: {username}")
    logging.info(f"  Password length: {len(password)} characters")
    logging.debug(f"  Full server config: {server_info}")

    # ---------- Get user DBs on SQL Server ----------
    db_list, chosen_driver = get_user_databases(server_name, username, password)
    if not db_list:
        logging.warning(f"No user databases found on {server_name}. Skipping.")
        continue

    # ---------- Filter databases based on databases_include ----------
    if databases_include:
        original_count = len(db_list)
        db_list = [db for db in db_list if db in databases_include]
        logging.info(f"  Filtered databases: {original_count} -> {len(db_list)} (include list: {databases_include})")

    if not db_list:
        logging.warning(f"No databases to process after filtering on {server_name}. Skipping.")
        continue

    # ---------- First pass: create/clear target tables ----------
    prepared = set()  # avoid recreate/clear per DB for same target table
    for db_name in db_list:
        for sys_table in system_tables:
            tgt_table = sanitize_table_name(sys_table)
            try:
                conn_str = build_sql_conn_str(server_name, username, password, db_name, driver_hint=chosen_driver)
                with pyodbc.connect(conn_str, timeout=15) as msconn:
                    mscur = msconn.cursor()
                    query = f"""
                        SELECT '{server_name}' AS full_domain_name,
                               @@SERVERNAME  AS host_name,
                               '{db_name}'   AS database_name,
                               GETDATE()     AS insert_date,
                               *
                        FROM {sys_table};
                    """
                    mscur.execute(query)

                    if tgt_table not in prepared:
                        create_table_if_needed(sqlite_conn, sqlite_cur, tgt_table, mscur.description)
                        truncate_table(sqlite_cur, tgt_table)
                        sqlite_conn.commit()
                        prepared.add(tgt_table)
            except Exception as e:
                logging.error(f"[Create/Clear] {server_name} | {db_name} | {sys_table} : {e}")

    logging.info(f"First pass complete for {server_name}: target tables created/cleared.")

    # ---------- Second pass: fetch & insert ----------
    def coerce_for_sqlite(value, _colname):
        """Pass through native types; normalize bytes-like to bytes."""
        if value is None:
            return None
        if isinstance(value, (bytearray, memoryview)):
            return bytes(value)
        # Convert datetime objects to ISO format strings
        if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
            return value.isoformat()
        return value

    for db_name in db_list:
        for sys_table in system_tables:
            tgt_table = sanitize_table_name(sys_table)
            try:
                conn_str = build_sql_conn_str(server_name, username, password, db_name, driver_hint=chosen_driver)
                with pyodbc.connect(conn_str, timeout=30) as msconn:
                    mscur = msconn.cursor()
                    query = f"""
                        SELECT '{server_name}' AS full_domain_name,
                               @@SERVERNAME  AS host_name,
                               '{db_name}'   AS database_name,
                               GETDATE()     AS insert_date,
                               *
                        FROM {sys_table};
                    """
                    mscur.execute(query)
                    colnames = [d[0] for d in mscur.description]
                    colnames = _uniquify(colnames)  # must match DDL uniqueness
                    rows = mscur.fetchall()

                    col_list = ", ".join(f'"{c}"' for c in colnames)
                    placeholders = ", ".join(["?"] * len(colnames))
                    insert_sql = f'INSERT INTO "{tgt_table}" ({col_list}) VALUES ({placeholders})'

                    out_rows = [tuple(coerce_for_sqlite(v, c) for v, c in zip(r, colnames)) for r in rows]

                    sqlite_cur.executemany(insert_sql, out_rows)
                    sqlite_conn.commit()
                    logging.info(f"Inserted {len(out_rows)} rows into {tgt_table} from {server_name} | {db_name}")
            except Exception as e:
                logging.error(f"[Insert] {server_name} | {db_name} | {sys_table} : {e}")

# ---------- Close ----------
try:
    sqlite_conn.close()
except Exception:
    pass

logging.info("ETL completed. SQLite DB populated.")
# Execution complete - check log files