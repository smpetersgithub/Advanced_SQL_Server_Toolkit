# run_mssql_scripter.py
"""
Script to run mssql-scripter commands for all active databases.
Reads database_config files and sql_server_connections.json to execute
mssql-scripter commands with proper parameter substitution.
"""
import os
import sys
import json
import logging
import subprocess
import configparser
from pathlib import Path
from datetime import datetime

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
    GENERATED_SCRIPTS_DIR = WORKSPACE_DIR / config.get('Paths', 'generated_scripts_dir')
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
DATABASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===================== Logging Setup =====================
LOG_FILE = LOG_DIR / f"log_003_execute_mssql_scripter_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"

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
logging.info("MSSQL-Scripter Command Runner")
logging.info("=" * 70)
logging.info(f"Workspace: {WORKSPACE_DIR}")
logging.info(f"Database Config Directory: {DATABASE_CONFIG_DIR}")
logging.info(f"Generated Scripts Directory: {GENERATED_SCRIPTS_DIR}")
logging.info(f"Log File: {LOG_FILE}")
logging.info("")

# ===================== Helper Functions =====================
def sanitize_dirname(name):
    """Sanitize name for use in directory name"""
    # Replace invalid directory characters
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace comma for cleaner directory names
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ',']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized


def load_json_config(filename):
    """Load a JSON configuration file"""
    config_path = CONFIG_DIR / filename
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        return None


def load_database_config(config_file_path):
    """Load a database configuration file"""
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_file_path}: {e}")
        return None


def get_all_database_config_files():
    """Get all database_config_*.json files from the database_config directory"""
    if not DATABASE_CONFIG_DIR.exists():
        logging.error(f"Database config directory not found: {DATABASE_CONFIG_DIR}")
        return []
    
    config_files = list(DATABASE_CONFIG_DIR.glob("database_config_*.json"))
    logging.info(f"Found {len(config_files)} database config file(s)")
    return config_files


def get_server_credentials(servername, sql_server_connections):
    """
    Get username and password for a server from sql_server_connections.json
    
    Args:
        servername: The server name to look up
        sql_server_connections: The loaded sql_server_connections.json data
    
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


def substitute_command_parameters(command_template, replacements):
    """
    Substitute parameters in command template
    
    Args:
        command_template: The command string with placeholders
        replacements: Dictionary of placeholder -> value mappings
    
    Returns:
        The command string with all placeholders replaced
    """
    command = command_template
    for placeholder, value in replacements.items():
        command = command.replace(placeholder, value)
    return command


def run_command(command, description):
    """
    Execute a shell command and log the results
    
    Args:
        command: The command to execute
        description: Description of the command for logging
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"    Executing: {description}")
        logging.debug(f"    Command: {command}")
        
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
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
        logging.error(f"    ✗ Timeout: {description} (exceeded 10 minutes)")
        return False
    except Exception as e:
        logging.error(f"    ✗ Error executing {description}: {e}")
        return False


def process_database(db_info, server_info, username, password, full_domain_name, commands_config):
    """
    Process a single database - run all active commands for it
    
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
        logging.warning(f"    No active commands found in commands_config.json")
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
        replacements = {
            "FULLDOMAINNAME": full_domain_name,
            "USERNAME": username,
            "PASSWORD": password,
            "SERVERNAME": servername,  # Use actual servername for connection
            "DATABASENAME": db_name,
            "PARENTNAME": parent_name_clean,  # Use sanitized names for paths
        }
        
        # Also replace sanitized servername in file paths
        # The command template uses SERVERNAME in paths, so we need to replace it with sanitized version
        command = substitute_command_parameters(command_template, replacements)
        
        # Now replace the sanitized servername in the file path
        # Replace the path pattern with sanitized servername
        path_pattern = f"\\{parent_name_clean}\\{servername}\\"
        path_replacement = f"\\{parent_name_clean}\\{servername_clean}\\"
        command = command.replace(path_pattern, path_replacement)
        
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
        sql_server_connections = load_json_config("sql_server_connections.json")
        commands_config = load_json_config("commands_config.json")
        
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

