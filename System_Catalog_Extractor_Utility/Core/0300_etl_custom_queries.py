# etl_custom_queries.py
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
    SQL_SCRIPTS_DIR = WORKSPACE_DIR / config.get('Paths', 'sql_scripts_dir')

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
    CUSTOM_QUERIES_FILE = config.get('Paths', 'custom_queries_file')

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

def load_sql_file(filepath):
    """Load SQL from external file"""
    # Try relative to workspace first, then as provided
    sql_path = WORKSPACE_DIR / filepath
    if not sql_path.exists():
        sql_path = Path(filepath)

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {filepath}")

    with open(sql_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

# Load JSON configurations
server_config = load_json_config(SQL_SERVER_CONNECTIONS_FILE)
custom_queries_config = load_json_config(CUSTOM_QUERIES_FILE)

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_0300_etl_custom_queries_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

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

logging.info("Starting Custom Queries ETL (Config=JSON, Target=SQLite, Source=SQL Server)")
logging.info(f"SQLite DB: {SQLITE_DB_PATH}")
logging.info(f"Log file: {LOG_FILE}")

# Get active servers from config
active_servers = [s for s in server_config['servers'] if s.get('active', False)]
if not active_servers:
    logging.error("No active servers found in config/sql_server_connections.json")
    sys.exit(1)

logging.info(f"Found {len(active_servers)} active server(s) in configuration")

# Get active custom queries
active_queries = [q for q in custom_queries_config['custom_queries'] if q.get('isactive', 0) == 1]
if not active_queries:
    logging.warning("No active custom queries found in config/custom_queries.json")
    sys.exit(0)

logging.info(f"Found {len(active_queries)} active custom quer{'y' if len(active_queries) == 1 else 'ies'} in configuration")

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

# ---------- SQLite Connection ----------
if not SQLITE_DB_PATH.exists():
    logging.info(f"SQLite database does not exist. Creating: {SQLITE_DB_PATH}")

sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
sqlite_cur = sqlite_conn.cursor()
logging.info(f"Connected to SQLite DB: {SQLITE_DB_PATH}")

# ---------- Process Each Server ----------
for srv_info in active_servers:
    server = srv_info['servername']
    user = srv_info['username']
    password = srv_info['password']
    databases_include = srv_info.get('databases_include', [])  # Get include list, default to empty

    logging.info(f"Processing server: {server}")
    logging.info(f"  Username: {user}")
    logging.info(f"  Password length: {len(password)} characters")

    # Get list of user databases
    user_dbs, driver_version = get_user_databases(server, user, password)
    if not user_dbs:
        logging.warning(f"[{server}] No user databases found or connection failed. Skipping server.")
        continue

    # Filter databases based on databases_include
    if databases_include:
        original_count = len(user_dbs)
        user_dbs = [db for db in user_dbs if db in databases_include]
        logging.info(f"  Filtered databases: {original_count} -> {len(user_dbs)} (include list: {databases_include})")

    if not user_dbs:
        logging.warning(f"[{server}] No databases to process after filtering. Skipping server.")
        continue
    
    # Process each custom query
    for query_config in active_queries:
        query_name = query_config['query_name']
        description = query_config.get('description', '')
        execution_scope = query_config.get('execution_scope', 'database')
        sqlite_table_name = query_config['sqlite_table_name']
        sqlite_ddl_file = query_config['sqlite_ddl_file']
        sqlserver_query_file = query_config['sqlserver_query_file']
        truncate_before_insert = query_config.get('truncate_before_insert', False)
        
        logging.info(f"[{server}] Processing custom query: {query_name}")
        logging.info(f"  Description: {description}")
        logging.info(f"  Execution scope: {execution_scope}")
        logging.info(f"  Target table: {sqlite_table_name}")
        
        # Load SQL files
        try:
            ddl_sql = load_sql_file(sqlite_ddl_file)
            query_sql = load_sql_file(sqlserver_query_file)
        except FileNotFoundError as e:
            logging.error(f"[{server}] {query_name}: {e}")
            continue
        
        # Create table in SQLite
        try:
            sqlite_cur.execute(ddl_sql)
            sqlite_conn.commit()
            logging.info(f"[SQLite] Table created/verified: {sqlite_table_name}")
        except Exception as e:
            logging.error(f"[SQLite] Failed to create table {sqlite_table_name}: {e}")
            continue
        
        # Truncate table if requested
        if truncate_before_insert:
            try:
                sqlite_cur.execute(f'DELETE FROM "{sqlite_table_name}"')
                sqlite_conn.commit()
                logging.info(f"[SQLite] Truncated table: {sqlite_table_name}")
            except Exception as e:
                logging.error(f"[SQLite] Failed to truncate table {sqlite_table_name}: {e}")
                continue
        
        # Execute query based on scope
        if execution_scope == "server":
            # Run once per server (e.g., server-level DMVs)
            databases_to_process = ["master"]
        else:
            # Run once per database
            databases_to_process = user_dbs
        
        total_rows_inserted = 0
        
        for db_name in databases_to_process:
            try:
                conn_str = build_sql_conn_str(server, user, password, db_name, driver_hint=driver_version)
                with try_sqlserver_connect(conn_str) as sql_conn:
                    sql_cur = sql_conn.cursor()
                    sql_cur.execute(query_sql)
                    
                    # Get column names from cursor
                    columns = [desc[0] for desc in sql_cur.description]
                    
                    # Fetch all rows
                    rows = sql_cur.fetchall()
                    
                    if rows:
                        # Prepare INSERT statement
                        placeholders = ','.join(['?' for _ in columns])
                        column_names = ','.join([f'"{c}"' for c in columns])
                        insert_sql = f'INSERT INTO "{sqlite_table_name}" ({column_names}) VALUES ({placeholders})'
                        
                        # Insert rows into SQLite
                        for row in rows:
                            # Convert row to list and handle special types
                            row_data = []
                            for val in row:
                                if isinstance(val, (_dt.datetime, _dt.date, _dt.time)):
                                    row_data.append(str(val))
                                elif isinstance(val, _dec.Decimal):
                                    row_data.append(float(val))
                                else:
                                    row_data.append(val)
                            
                            sqlite_cur.execute(insert_sql, row_data)
                        
                        sqlite_conn.commit()
                        total_rows_inserted += len(rows)
                        
                        if execution_scope == "database":
                            logging.info(f"[{server}] {query_name}: Inserted {len(rows)} rows from database '{db_name}'")
                    else:
                        if execution_scope == "database":
                            logging.info(f"[{server}] {query_name}: No rows returned from database '{db_name}'")
                
            except Exception as e:
                logging.error(f"[{server}] {query_name} | {db_name}: {e}")
                continue
        
        if execution_scope == "server":
            logging.info(f"[{server}] {query_name}: Total rows inserted: {total_rows_inserted}")
        else:
            logging.info(f"[{server}] {query_name}: Total rows inserted across all databases: {total_rows_inserted}")

# ---------- Cleanup ----------
sqlite_cur.close()
sqlite_conn.close()
logging.info("Custom Queries ETL completed. SQLite DB populated.")
# Execution complete - check log files

