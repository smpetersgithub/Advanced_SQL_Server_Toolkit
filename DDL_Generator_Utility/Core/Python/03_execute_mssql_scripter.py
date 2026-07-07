# run_mssql_scripter.py
"""
Script to run mssql-scripter commands for all active databases.
Reads database_config files and database-config.json to execute
mssql-scripter commands with proper parameter substitution.
"""
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ===================== Constants =====================
DATABASE_CONFIG_PATTERN = "database_config_*.json"
DEFAULT_COMMAND_TIMEOUT = 600  # 10 minutes in seconds

# ===================== Helper Functions =====================
def sanitize_dirname(name: str) -> str:
    """
    Sanitize name for use in directory name.

    Args:
        name: Directory name to sanitize

    Returns:
        str: Sanitized directory-safe string
    """
    # Replace invalid directory characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner directory names
    invalid_chars = '<>:"/\\|?*,'
    translation_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))
    return name.translate(translation_table)


def load_json_config(filename: str, config_dir: Path) -> Optional[Dict]:
    """
    Load a JSON configuration file.

    Args:
        filename: Name of the config file to load
        config_dir: Directory containing the config file

    Returns:
        Dict containing the configuration, or None if loading fails
    """
    config_path = config_dir / filename
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {config_path}: {e}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"Failed to read config file {config_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading config file {config_path}: {e}", exc_info=True)
        return None


def load_database_config(config_file_path: Path) -> Optional[Dict]:
    """
    Load a database configuration file.

    Args:
        config_file_path: Path to the JSON configuration file

    Returns:
        Dict containing the configuration, or None if loading fails
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {config_file_path}: {e}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"Failed to read config file {config_file_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading config file {config_file_path}: {e}", exc_info=True)
        return None


def get_all_database_config_files(database_config_dir: Path) -> List[Path]:
    """
    Get all database_config_*.json files from the database_config directory.

    Returns:
        List of Path objects for each config file found
    """
    if not database_config_dir.exists():
        logger.error(f"Database config directory not found: {database_config_dir}")
        return []

    config_files = list(database_config_dir.glob(DATABASE_CONFIG_PATTERN))
    logger.info(f"Found {len(config_files)} database config file(s)")
    return config_files


def get_server_credentials(servername: str, sql_server_connections: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get username and password for a server from database-config.json

    Args:
        servername: The server name to look up
        sql_server_connections: The loaded database-config.json data

    Returns:
        Tuple of (username, password, full_domain_name) or (None, None, None) if not found
    """
    servers = sql_server_connections.get("servers", [])

    for server in servers:
        if server.get("servername") == servername:
            username = server.get("username", "")
            password = server.get("password", "")
            # Use servername as full_domain_name (can be customized if needed)
            full_domain_name = servername
            return username, password, full_domain_name

    logger.warning(f"  No credentials found for server: {servername}")
    return None, None, None


def substitute_command_parameters(command_template: str, replacements: Dict[str, str]) -> str:
    """
    Substitute parameters in command template.

    Args:
        command_template: The command string with placeholders
        replacements: Dictionary of placeholder -> value mappings

    Returns:
        str: The command string with all placeholders replaced
    """
    command = command_template
    for placeholder, value in replacements.items():
        command = command.replace(placeholder, value)
    return command


def run_command(command: str, description: str, timeout: Optional[int] = None) -> bool:
    """
    Execute a shell command and log the results.

    Args:
        command: The command to execute
        description: Description of the command for logging
        timeout: Command timeout in seconds (uses DEFAULT_COMMAND_TIMEOUT if not specified)

    Returns:
        bool: True if successful, False otherwise
    """
    timeout = timeout or DEFAULT_COMMAND_TIMEOUT

    try:
        logger.info(f"    Executing: {description}")
        logger.debug(f"    Command: {command}")

        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Log output
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.debug(f"      STDOUT: {line}")

        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():  # Only log non-empty lines
                    logger.warning(f"      STDERR: {line}")

        # Check return code
        if result.returncode == 0:
            logger.info(f"    ✓ Success: {description}")
            return True
        else:
            logger.error(f"    ✗ Failed: {description} (return code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"    ✗ Timeout: {description} (exceeded {timeout} seconds)")
        return False
    except subprocess.SubprocessError as e:
        logger.error(f"    ✗ Subprocess error executing {description}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"    ✗ Unexpected error executing {description}: {e}", exc_info=True)
        return False


def process_database(db_info: Dict, server_info: Dict, username: str, password: str,
                     full_domain_name: str, commands_config: Dict) -> Tuple[int, int, int]:
    """
    Process a single database - run all active commands for it.

    Args:
        db_info: Database information dictionary
        server_info: Server information dictionary
        username: SQL Server username
        password: SQL Server password
        full_domain_name: Full domain name for the server
        commands_config: Commands configuration data

    Returns:
        Tuple of (commands_executed, commands_succeeded, commands_failed)
    """
    db_name = db_info.get("name", "")
    parent_name = server_info.get("parent_name", "")
    servername = server_info.get("servername", "")
    
    # Sanitize names for directory paths
    parent_name_clean = sanitize_dirname(parent_name)
    servername_clean = sanitize_dirname(servername)
    db_name_clean = sanitize_dirname(db_name)
    
    logger.info(f"  Processing database: {db_name}")
    
    # Get active commands
    commands = commands_config.get("commands", [])
    active_commands = [cmd for cmd in commands if cmd.get("active", False)]
    
    if not active_commands:
        logger.warning(f"    No active commands found in commands-config.json")
        return 0, 0, 0
    
    commands_executed = 0
    commands_succeeded = 0
    commands_failed = 0
    
    # Execute each active command
    for cmd in active_commands:
        command_template = cmd.get("command", "")
        command_name = cmd.get("name", f"Command {cmd.get('command_id', '?')}")
        
        if not command_template:
            logger.warning(f"    Skipping command '{command_name}' - no command template found")
            continue
        
        # Prepare replacements
        # Note: SERVERNAME is used both for connection and in paths
        # For paths, we need the sanitized version, so we do a two-step replacement
        replacements = {
            "FULLDOMAINNAME": full_domain_name,
            "USERNAME": username,
            "PASSWORD": password,
            "SERVERNAME": servername,  # Use actual servername for connection
            "DATABASENAME": db_name,
            "PARENTNAME": parent_name_clean,  # Use sanitized names for paths
        }

        # First pass: replace all placeholders
        command = substitute_command_parameters(command_template, replacements)

        # Second pass: fix file paths by replacing unsanitized servername with sanitized version
        # This handles cases where SERVERNAME appears in file paths
        if servername != servername_clean:
            # Replace servername in Windows-style paths
            command = command.replace(f"\\{servername}\\", f"\\{servername_clean}\\")
            # Replace servername in Unix-style paths (just in case)
            command = command.replace(f"/{servername}/", f"/{servername_clean}/")
        
        # Execute the command
        commands_executed += 1
        if run_command(command, command_name):
            commands_succeeded += 1
        else:
            commands_failed += 1
    
    return commands_executed, commands_succeeded, commands_failed


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
    generated_scripts_dir = config.get_generated_scripts_dir()
    log_dir = config.get_log_dir()

    # Ensure directories exist
    database_config_dir.mkdir(parents=True, exist_ok=True)
    generated_scripts_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = config.setup_logging('03_execute_mssql_scripter')

    logger.info("=" * 70)
    logger.info("MSSQL-Scripter Command Runner")
    logger.info("=" * 70)
    logger.info(f"Workspace: {workspace_dir}")
    logger.info(f"Database Config Directory: {database_config_dir}")
    logger.info(f"Generated Scripts Directory: {generated_scripts_dir}")
    logger.info(f"Log File: {log_file}")
    logger.info("")

    try:
        # Load configurations
        logger.info("Loading configurations...")
        sql_server_connections = load_json_config("database-config.json", config_dir)
        commands_config = load_json_config("commands-config.json", config_dir)

        if not sql_server_connections or not commands_config:
            logger.error("Failed to load required configuration files")
            return

        # Get all database config files
        config_files = get_all_database_config_files(database_config_dir)

        if not config_files:
            logger.warning("No database config files found")
            return

        logger.info("")

        # Process each config file
        total_databases_processed = 0
        total_commands_executed = 0
        total_commands_succeeded = 0
        total_commands_failed = 0

        for config_file in config_files:
            logger.info(f"Processing config: {config_file.name}")

            config_data = load_database_config(config_file)

            if not config_data:
                logger.warning(f"  Skipping {config_file.name} due to load error")
                continue

            server_info = config_data.get("server", {})
            servername = server_info.get("servername", "")
            parent_name = server_info.get("parent_name", "")

            if not servername:
                logger.warning(f"  No servername found in {config_file.name}")
                continue

            username, password, full_domain_name = get_server_credentials(servername, sql_server_connections)

            if not username or not password:
                logger.warning(f"  Skipping server {servername} - no credentials found")
                continue

            logger.info(f"  Server: {servername} (Parent: {parent_name})")
            logger.info(f"  Username: {username}")

            databases = config_data.get("databases", [])
            active_databases = [db for db in databases if db.get("is_active", False)]

            logger.info(f"  Active databases: {len(active_databases)} of {len(databases)}")

            for db in active_databases:
                cmds_exec, cmds_succ, cmds_fail = process_database(
                    db, server_info, username, password, full_domain_name, commands_config
                )

                total_databases_processed += 1
                total_commands_executed += cmds_exec
                total_commands_succeeded += cmds_succ
                total_commands_failed += cmds_fail

            logger.info("")

        # Summary
        logger.info("=" * 70)
        logger.info(f"MSSQL-Scripter execution complete!")
        logger.info(f"Databases processed: {total_databases_processed}")
        logger.info(f"Commands executed: {total_commands_executed}")
        logger.info(f"Commands succeeded: {total_commands_succeeded}")
        logger.info(f"Commands failed: {total_commands_failed}")
        logger.info(f"Generated Scripts location: {generated_scripts_dir}")
        logger.info("=" * 70)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
