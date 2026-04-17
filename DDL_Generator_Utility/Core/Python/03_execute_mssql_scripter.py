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
GENERATED_SCRIPTS_DIR = config.get_generated_scripts_dir()
LOG_DIR = config.get_log_dir()

# Ensure directories exist
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = config.setup_logging('03_execute_mssql_scripter')

logging.info("=" * 70)
logging.info("MSSQL-Scripter Command Runner")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Generated Scripts Directory: {GENERATED_SCRIPTS_DIR}")
logging.info(f"Log File: {LOG_FILE}")
logging.info("")

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


def load_json_config(filename: str) -> Optional[Dict]:
    """
    Load a JSON configuration file.

    Args:
        filename: Name of the config file to load

    Returns:
        Dict containing the configuration, or None if loading fails
    """
    config_path = CONFIG_DIR / filename
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file {config_path}: {e}")
        return None
    except IOError as e:
        logging.error(f"Failed to read config file {config_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading config file {config_path}: {e}", exc_info=True)
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
        logging.error(f"Invalid JSON in config file {config_file_path}: {e}")
        return None
    except IOError as e:
        logging.error(f"Failed to read config file {config_file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading config file {config_file_path}: {e}", exc_info=True)
        return None


def get_all_database_config_files() -> List[Path]:
    """
    Get all database_config_*.json files from the database_config directory.

    Returns:
        List of Path objects for each config file found
    """
    if not DATABASE_CONFIG_DIR.exists():
        logging.error(f"Database config directory not found: {DATABASE_CONFIG_DIR}")
        return []

    config_files = list(DATABASE_CONFIG_DIR.glob(DATABASE_CONFIG_PATTERN))
    logging.info(f"Found {len(config_files)} database config file(s)")
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

    logging.warning(f"  No credentials found for server: {servername}")
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
        logging.info(f"    Executing: {description}")
        logging.debug(f"    Command: {command}")

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
                logging.debug(f"      STDOUT: {line}")

        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():  # Only log non-empty lines
                    logging.warning(f"      STDERR: {line}")

        # Check return code
        if result.returncode == 0:
            logging.info(f"    ✓ Success: {description}")
            return True
        else:
            logging.error(f"    ✗ Failed: {description} (return code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"    ✗ Timeout: {description} (exceeded {timeout} seconds)")
        return False
    except subprocess.SubprocessError as e:
        logging.error(f"    ✗ Subprocess error executing {description}: {e}")
        return False
    except Exception as e:
        logging.error(f"    ✗ Unexpected error executing {description}: {e}", exc_info=True)
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
    
    logging.info(f"  Processing database: {db_name}")
    
    # Get active commands
    commands = commands_config.get("commands", [])
    active_commands = [cmd for cmd in commands if cmd.get("active", False)]
    
    if not active_commands:
        logging.warning(f"    No active commands found in commands-config.json")
        return 0, 0, 0
    
    commands_executed = 0
    commands_succeeded = 0
    commands_failed = 0
    
    # Execute each active command
    for cmd in active_commands:
        command_template = cmd.get("command", "")
        command_name = cmd.get("name", f"Command {cmd.get('command_id', '?')}")
        
        if not command_template:
            logging.warning(f"    Skipping command '{command_name}' - no command template found")
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
    try:
        # Load configurations
        logging.info("Loading configurations...")
        sql_server_connections = load_json_config("database-config.json")
        commands_config = load_json_config("commands-config.json")
        
        if not sql_server_connections or not commands_config:
            logging.error("Failed to load required configuration files")
            return
        
        # Get all database config files
        config_files = get_all_database_config_files()
        
        if not config_files:
            logging.warning("No database config files found")
            return
        
        logging.info("")
        
        # Process each config file
        total_databases_processed = 0
        total_commands_executed = 0
        total_commands_succeeded = 0
        total_commands_failed = 0
        
        for config_file in config_files:
            logging.info(f"Processing config: {config_file.name}")
            
            # Load config file
            config_data = load_database_config(config_file)
            
            if not config_data:
                logging.warning(f"  Skipping {config_file.name} due to load error")
                continue
            
            # Extract server information
            server_info = config_data.get("server", {})
            servername = server_info.get("servername", "")
            parent_name = server_info.get("parent_name", "")
            
            if not servername:
                logging.warning(f"  No servername found in {config_file.name}")
                continue
            
            # Get credentials for this server
            username, password, full_domain_name = get_server_credentials(servername, sql_server_connections)
            
            if not username or not password:
                logging.warning(f"  Skipping server {servername} - no credentials found")
                continue
            
            logging.info(f"  Server: {servername} (Parent: {parent_name})")
            logging.info(f"  Username: {username}")
            
            # Get active databases
            databases = config_data.get("databases", [])
            active_databases = [db for db in databases if db.get("is_active", False)]
            
            logging.info(f"  Active databases: {len(active_databases)} of {len(databases)}")
            
            # Process each active database
            for db in active_databases:
                cmds_exec, cmds_succ, cmds_fail = process_database(
                    db, server_info, username, password, full_domain_name, commands_config
                )
                
                total_databases_processed += 1
                total_commands_executed += cmds_exec
                total_commands_succeeded += cmds_succ
                total_commands_failed += cmds_fail
            
            logging.info("")
        
        # Summary
        logging.info("=" * 70)
        logging.info(f"MSSQL-Scripter execution complete!")
        logging.info(f"Databases processed: {total_databases_processed}")
        logging.info(f"Commands executed: {total_commands_executed}")
        logging.info(f"Commands succeeded: {total_commands_succeeded}")
        logging.info(f"Commands failed: {total_commands_failed}")
        logging.info(f"Generated Scripts location: {GENERATED_SCRIPTS_DIR}")
        logging.info("=" * 70)
        
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

