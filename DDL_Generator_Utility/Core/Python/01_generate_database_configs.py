# generate_database_configs.py
"""
Script to generate individual database configuration files.
For each active SQL Server, connects to master database and creates
a config file for each database found.
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pyodbc
from config_loader import ConfigLoader

# ===================== Configuration =====================
# Load configuration using ConfigLoader (reads from Config/config.json)
try:
    config = ConfigLoader()
except FileNotFoundError as e:
    print(f"[ERROR] {e}")
    print("Please ensure config.json exists in the Config directory.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.json file for errors.")
    sys.exit(1)

# Read configuration values
WORKSPACE_DIR = config.get_workspace_dir()
CONFIG_DIR = config.get_config_dir()
DATABASE_CONFIG_DIR = config.get_database_config_dir()
LOG_DIR = config.get_log_dir()

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = config.setup_logging('01_generate_database_configs')

logging.info("=" * 70)
logging.info("Database Configuration Generator")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Config Directory: {CONFIG_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Log File: {LOG_FILE}")

# ===================== Constants =====================
SYSTEM_DATABASES = ['master', 'tempdb', 'model', 'msdb']

SQL_GET_DATABASES = """
    SELECT
        name,
        database_id,
        create_date,
        state_desc,
        recovery_model_desc,
        compatibility_level
    FROM sys.databases
    WHERE state = 0
    ORDER BY name
"""

# ===================== Helper Functions =====================
def load_json_config(filename: str) -> Dict:
    """Load JSON configuration file"""
    config_path = CONFIG_DIR / filename
    
    if not config_path.exists():
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_sql_conn_str(server: str, user: str, password: str, db_name: str = "master",
                       driver_hint: Optional[str] = None) -> str:
    """
    Build an ODBC connection string.

    Args:
        server: SQL Server hostname or IP
        user: SQL Server username
        password: SQL Server password
        db_name: Database name (default: "master")
        driver_hint: ODBC driver version hint ("18" for Driver 18, None for Driver 17)

    Returns:
        str: ODBC connection string
    """
    driver = "ODBC Driver 17 for SQL Server" if driver_hint != "18" else "ODBC Driver 18 for SQL Server"
    return f"DRIVER={{{driver}}};SERVER={server};UID={user};PWD={password};DATABASE={db_name};"


def try_sqlserver_connect(conn_str: str, timeout: Optional[int] = None):
    """
    Attempt to connect to SQL Server with configurable timeout.

    Args:
        conn_str: ODBC connection string
        timeout: Connection timeout in seconds (uses config value if not specified)

    Returns:
        pyodbc.Connection: Database connection object
    """
    timeout = timeout or config.get_connection_timeout()
    return pyodbc.connect(conn_str, timeout=timeout)


def get_all_databases(server: str, user: str, password: str) -> Tuple[List[Dict], Optional[str]]:
    """
    Get all databases from SQL Server master database.

    Args:
        server: SQL Server hostname or IP
        user: SQL Server username
        password: SQL Server password

    Returns:
        tuple: (list of database info dictionaries, driver version string)
               Returns ([], None) if connection fails
    """
    for drv in (None, "18"):
        try:
            conn_str = build_sql_conn_str(server, user, password, "master", driver_hint=drv)
            with try_sqlserver_connect(conn_str) as conn:
                cur = conn.cursor()
                cur.execute(SQL_GET_DATABASES)

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

        except pyodbc.Error as e:
            logging.warning(f"[{server}] Database connection failed with driver {drv or '17'}: {e}")
        except Exception as e:
            logging.error(f"[{server}] Unexpected error with driver {drv or '17'}: {e}", exc_info=True)

    logging.error(f"[{server}] Could not connect to SQL Server with ODBC Driver 17/18")
    return [], None


def sanitize_filename(name: str) -> str:
    """
    Sanitize server name for use in filename.

    Args:
        name: Server name to sanitize

    Returns:
        str: Sanitized filename-safe string
    """
    # Replace invalid filename characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner filenames
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ',']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized


def is_database_active(db_name: str, databases_include: List[str],
                       system_databases: List[str]) -> bool:
    """
    Determine if a database should be marked as active.

    Args:
        db_name: Name of the database
        databases_include: List of databases to include (whitelist)
        system_databases: List of system databases to exclude

    Returns:
        bool: True if database should be active, False otherwise
    """
    if databases_include:
        return db_name in databases_include
    return db_name not in system_databases


def create_server_config(server_info: Dict, databases: List[Dict], output_dir: Path) -> bool:
    """
    Create a configuration file for a server with all its databases.

    Args:
        server_info: Dictionary containing server connection information
        databases: List of database information dictionaries
        output_dir: Path to output directory for config files

    Returns:
        bool: True if config file created successfully, False otherwise
    """
    # Create config filename: database_config_{servername}.json
    server_name_clean = sanitize_filename(server_info["servername"])
    config_filename = f"database_config_{server_name_clean}.json"
    config_path = output_dir / config_filename

    # Get databases_include list
    databases_include = server_info.get("databases_include", [])

    # Calculate active database count once
    active_db_count = sum(
        1 for db_info in databases
        if is_database_active(db_info["name"], databases_include, SYSTEM_DATABASES)
    )

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
                "is_active": is_database_active(db_info["name"], databases_include, SYSTEM_DATABASES)
            }
            for db_info in databases
        ],
        "metadata": {
            "config_generated_date": datetime.now().isoformat(),
            "config_generator_script": "01_generate_database_configs.py",
            "total_databases": len(databases),
            "active_databases": active_db_count
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
        server_config = load_json_config("database-config.json")
        
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
            # Validate required fields
            try:
                server_name = server_info['servername']
                username = server_info['username']
                password = server_info['password']
            except KeyError as e:
                logging.error(f"Missing required field in server config: {e}")
                continue

            parent_name = server_info.get('parent_name', server_name)

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

