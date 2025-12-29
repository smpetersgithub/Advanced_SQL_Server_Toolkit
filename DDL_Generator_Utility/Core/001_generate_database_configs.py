# generate_database_configs.py
"""
Script to generate individual database configuration files.
For each active SQL Server, connects to master database and creates
a config file for each database found.
"""
import os
import sys
import json
import logging
import configparser
from pathlib import Path
from datetime import datetime

import pyodbc

# ===================== Configuration =====================
# Load configuration from config.ini
config = configparser.ConfigParser()
CONFIG_FILE = Path("C:/Advanced_SQL_Server_Toolkit/DDL_Generator_Utility/Config/config.ini")

if not CONFIG_FILE.exists():
    print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
    print("Please ensure config.ini exists in the Config directory.")
    sys.exit(1)

config.read(CONFIG_FILE)

# Read configuration values
try:
    WORKSPACE_DIR = Path(config.get('Paths', 'workspace_dir'))
    CONFIG_DIR = WORKSPACE_DIR / config.get('Paths', 'config_dir')
    DATABASE_CONFIG_DIR = WORKSPACE_DIR / config.get('Paths', 'database_config_dir')
    LOG_DIR = WORKSPACE_DIR / config.get('Paths', 'log_dir')

    # Logging configuration
    LOG_LEVEL = config.get('Logging', 'log_level')
    LOG_FORMAT = config.get('Logging', 'log_format')
    TIMESTAMP_FORMAT = config.get('Logging', 'timestamp_format')
    LOG_FILEMODE = config.get('Logging', 'log_filemode', fallback='w')

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.ini file for missing sections or options.")
    sys.exit(1)

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_001_generate_database_configs_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

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

logging.info("=" * 70)
logging.info("Database Configuration Generator")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Config Directory: {CONFIG_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Log File: {LOG_FILE}")

# ===================== Helper Functions =====================
def load_json_config(filename):
    """Load JSON configuration file"""
    config_path = CONFIG_DIR / filename
    
    if not config_path.exists():
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_sql_conn_str(server, user, password, db_name="master", driver_hint=None):
    """Build an ODBC connection string. Try Driver 17 by default; if hint='18', use 18."""
    driver = "ODBC Driver 17 for SQL Server" if driver_hint != "18" else "ODBC Driver 18 for SQL Server"
    return f"DRIVER={{{driver}}};SERVER={server};UID={user};PWD={password};DATABASE={db_name};"


def try_sqlserver_connect(conn_str):
    """Attempt to connect to SQL Server with timeout"""
    return pyodbc.connect(conn_str, timeout=10)


def get_all_databases(server, user, password):
    """
    Get all databases from SQL Server master database.
    Returns tuple: (list of database names, driver version used)
    """
    for drv in (None, "18"):
        try:
            conn_str = build_sql_conn_str(server, user, password, "master", driver_hint=drv)
            with try_sqlserver_connect(conn_str) as conn:
                cur = conn.cursor()
                # Query to get all databases (including system databases)
                cur.execute("""
                    SELECT 
                        name,
                        database_id,
                        create_date,
                        state_desc,
                        recovery_model_desc,
                        compatibility_level
                    FROM sys.databases
                    WHERE state = 0  -- Only online databases
                    ORDER BY name
                """)
                
                databases = []
                for row in cur.fetchall():
                    db_info = {
                        "name": row[0],
                        "database_id": row[1],
                        "create_date": row[2].isoformat() if row[2] else None,
                        "state": row[3],
                        "recovery_model": row[4],
                        "compatibility_level": row[5]
                    }
                    databases.append(db_info)
                
                driver_used = drv or "17"
                logging.info(f"[{server}] Found {len(databases)} databases (driver={driver_used})")
                return databases, driver_used
                
        except Exception as e:
            logging.warning(f"[{server}] Failed with driver {drv or '17'}: {e}")
    
    logging.error(f"[{server}] Could not connect to SQL Server with ODBC Driver 17/18")
    return [], None


def sanitize_filename(name):
    """Sanitize server name for use in filename"""
    # Replace invalid filename characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner filenames
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ',']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized


def create_server_config(server_info, databases, output_dir):
    """
    Create a configuration file for a server with all its databases.

    Args:
        server_info: Dictionary containing server connection information
        databases: List of database information dictionaries
        output_dir: Path to output directory for config files
    """
    # Create config filename: database_config_{servername}.json
    server_name_clean = sanitize_filename(server_info["servername"])
    config_filename = f"database_config_{server_name_clean}.json"
    config_path = output_dir / config_filename

    # Get databases_include list
    databases_include = server_info.get("databases_include", [])

    # System databases to exclude when databases_include is empty/null
    system_databases = ['master', 'tempdb', 'model', 'msdb']

    # Determine which databases should be active
    def is_database_active(db_name):
        """Determine if a database should be marked as active"""
        if databases_include:
            # If databases_include is not empty, only activate databases in the list
            return True if db_name in databases_include else False
        else:
            # If databases_include is empty/null, activate all except system databases
            return False if db_name in system_databases else True

    # Build configuration object
    config = {
        "server": {
            "parent_name": server_info.get("parent_name", ""),
            "servername": server_info["servername"],
            "port": server_info.get("port", 1433),
            "databases_include": databases_include
        },
        "databases": [
            {
                "name": db_info["name"],
                "database_id": db_info.get("database_id"),
                "create_date": db_info.get("create_date"),
                "state": db_info.get("state"),
                "recovery_model": db_info.get("recovery_model"),
                "compatibility_level": db_info.get("compatibility_level"),
                "is_active": is_database_active(db_info["name"])
            }
            for db_info in databases
        ],
        "metadata": {
            "config_generated_date": datetime.now().isoformat(),
            "config_generator_script": "generate_database_configs.py",
            "total_databases": len(databases),
            "active_databases": sum(1 for db in databases if is_database_active(db["name"]) == "yes")
        }
    }

    # Write config file
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        active_count = config["metadata"]["active_databases"]
        logging.info(f"  Created config: {config_filename} ({len(databases)} databases, {active_count} active)")
        return True
    except Exception as e:
        logging.error(f"  Failed to create config {config_filename}: {e}")
        return False


# ===================== Main Processing =====================
def main():
    """Main processing function"""
    try:
        # Load SQL Server connections configuration
        logging.info("Loading SQL Server connections configuration...")
        server_config = load_json_config("sql_server_connections.json")
        
        # Get active servers
        active_servers = [
            s for s in server_config.get('servers', [])
            if s.get('active', False)
        ]
        
        if not active_servers:
            logging.warning("No active servers found in configuration")
            return
        
        logging.info(f"Found {len(active_servers)} active server(s)")
        logging.info("")
        
        # Process each active server
        total_configs_created = 0

        for server_info in active_servers:
            server_name = server_info['servername']
            parent_name = server_info.get('parent_name', server_name)
            username = server_info['username']
            password = server_info['password']

            logging.info(f"Processing server: {parent_name} ({server_name})")
            logging.info(f"  Username: {username}")

            # Get all databases from master
            databases, driver_version = get_all_databases(server_name, username, password)

            if not databases:
                logging.warning(f"  No databases found or connection failed. Skipping server.")
                logging.info("")
                continue

            # Create single config file for this server with all databases
            if create_server_config(server_info, databases, DATABASE_CONFIG_DIR):
                total_configs_created += 1

            logging.info("")

        # Summary
        logging.info("=" * 70)
        logging.info(f"Configuration generation complete!")
        logging.info(f"Total config files created: {total_configs_created}")
        logging.info(f"Config files location: {DATABASE_CONFIG_DIR}")
        logging.info("=" * 70)
        
    except FileNotFoundError as e:
        logging.error(f"Configuration file error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

