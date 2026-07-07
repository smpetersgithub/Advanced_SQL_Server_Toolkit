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

logger = logging.getLogger(__name__)

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
def load_json_config(filename: str, config_dir: Path) -> Dict:
    """Load JSON configuration file"""
    config_path = config_dir / filename

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def try_sqlserver_connect(conn_str: str, timeout: int = 10):
    """
    Attempt to connect to SQL Server with configurable timeout.

    Args:
        conn_str: ODBC connection string
        timeout: Connection timeout in seconds

    Returns:
        pyodbc.Connection: Database connection object
    """
    return pyodbc.connect(conn_str, timeout=timeout)


def get_all_databases(server: str, user: str, password: str, config: ConfigLoader,
                      windows_auth: bool = False) -> Tuple[List[Dict], Optional[str]]:
    """
    Get all databases from SQL Server master database.

    Args:
        server: SQL Server hostname or IP
        user: SQL Server username (ignored when windows_auth is True)
        password: SQL Server password (ignored when windows_auth is True)
        config: ConfigLoader instance for building connection strings
        windows_auth: If True, uses Windows Authentication instead of SQL auth

    Returns:
        tuple: (list of database info dictionaries, driver name string)
               Returns ([], None) if connection fails
    """
    try:
        conn_str = config.get_connection_string(server, user, password, "master",
                                                 windows_auth=windows_auth)
        with try_sqlserver_connect(conn_str, config.get_connection_timeout()) as conn:
            with conn.cursor() as cur:
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

            driver_used = config.get_odbc_driver()
            logger.info(f"[{server}] Found {len(databases)} databases (driver={driver_used})")
            return databases, driver_used

    except RuntimeError as e:
        logger.error(f"[{server}] {e}", exc_info=True)
    except pyodbc.Error as e:
        logger.warning(f"[{server}] Database connection failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[{server}] Unexpected error: {e}", exc_info=True)

    logger.error(f"[{server}] Could not connect to SQL Server")
    return [], None


def sanitize_filename(name: str) -> str:
    """
    Sanitize server name for use in filename.

    Args:
        name: Server name to sanitize

    Returns:
        str: Sanitized filename-safe string
    """
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
    server_name_clean = sanitize_filename(server_info["servername"])
    config_filename = f"database_config_{server_name_clean}.json"
    config_path = output_dir / config_filename

    databases_include = server_info.get("databases_include", [])

    active_db_count = sum(
        1 for db_info in databases
        if is_database_active(db_info["name"], databases_include, SYSTEM_DATABASES)
    )

    server_config = {
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

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(server_config, f, indent=2)
        active_count = server_config["metadata"]["active_databases"]
        logger.info(f"  Created config: {config_filename} ({len(databases)} databases, {active_count} active)")
        return True
    except Exception as e:
        logger.error(f"  Failed to create config {config_filename}: {e}", exc_info=True)
        return False


# ===================== Main Processing =====================
def main():
    """Main processing function"""
    # Load configuration
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)

    # Read configuration values
    workspace_dir = config.get_workspace_dir()
    config_dir = config.get_config_dir()
    database_config_dir = config.get_database_config_dir()
    log_dir = config.get_log_dir()

    # Ensure directories exist
    config_dir.mkdir(parents=True, exist_ok=True)
    database_config_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = config.setup_logging('01_generate_database_configs')

    logger.info("=" * 70)
    logger.info("Database Configuration Generator")
    logger.info("=" * 70)
    logger.info(f"Workspace: {workspace_dir}")
    logger.info(f"Config Directory: {config_dir}")
    logger.info(f"Database Config Directory: {database_config_dir}")
    logger.info(f"Log File: {log_file}")

    try:
        # Load SQL Server connections configuration
        logger.info("Loading SQL Server connections configuration...")
        server_config = load_json_config("database-config.json", config_dir)

        # Get active servers
        active_servers = [
            s for s in server_config.get('servers', [])
            if s.get('active', False)
        ]

        if not active_servers:
            logger.warning("No active servers found in configuration")
            return

        logger.info(f"Found {len(active_servers)} active server(s)")
        logger.info("")

        # Process each active server
        total_configs_created = 0

        for server_info in active_servers:
            try:
                server_name = server_info['servername']
                username = server_info['username']
                password = server_info['password']
            except KeyError as e:
                logger.error(f"Missing required field in server config: {e}", exc_info=True)
                continue

            windows_auth = server_info.get('windows_auth', False)
            parent_name = server_info.get('parent_name', server_name)

            logger.info(f"Processing server: {parent_name} ({server_name})")
            if windows_auth:
                logger.info(f"  Auth: Windows Authentication")
            else:
                logger.info(f"  Username: {username}")

            databases, driver_version = get_all_databases(server_name, username, password, config,
                                                          windows_auth=windows_auth)

            if not databases:
                logger.warning(f"  No databases found or connection failed. Skipping server.")
                logger.info("")
                continue

            if create_server_config(server_info, databases, database_config_dir):
                total_configs_created += 1

            logger.info("")

        # Summary
        logger.info("=" * 70)
        logger.info(f"Configuration generation complete!")
        logger.info(f"Total config files created: {total_configs_created}")
        logger.info(f"Config files location: {database_config_dir}")
        logger.info("=" * 70)

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
