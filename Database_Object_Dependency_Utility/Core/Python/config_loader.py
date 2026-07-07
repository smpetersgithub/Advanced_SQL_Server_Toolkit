"""
Configuration loader for Database Object Dependency Utility.
Loads configuration from config.json file.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Centralized configuration loader for the Database Object Dependency utility."""

    def __init__(self, config_path=None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config.json. If not provided, will auto-detect.
        """
        # Set paths (always needed)
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent

        # Determine config path
        if config_path is None:
            # Auto-detect config path relative to this file
            # Python script -> Core/Python -> Core -> ProjectRoot -> Config
            config_path = self.project_root / 'Config' / 'config.json'

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._db_config: Optional[Dict[str, Any]] = None  # Cached database config

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in configuration file: {e.msg}", e.doc, e.pos
            )

    def get(self, section, key, default=None):
        """
        Get a configuration value.

        Args:
            section: Configuration section (e.g., 'paths', 'files')
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        section_lower = section.lower()
        if section_lower in self.config:
            return self.config[section_lower].get(key, default)
        return default

    def get_path(self, section, key):
        """Get a path configuration value."""
        return self.get(section, key, '')

    def get_int(self, section, key, default=0):
        """Get an integer configuration value."""
        value = self.get(section, key, default)
        return int(value) if value is not None else default

    def get_bool(self, section, key, default=False):
        """Get a boolean configuration value."""
        value = self.get(section, key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1')
        return bool(value)

    # ========================================================================
    # Path Getters
    # ========================================================================

    def get_java_source_dirs(self):
        """Get list of Java source directories."""
        return self.config.get('paths', {}).get('java_source_dirs', [])

    def get_project_base_dir(self):
        """Get the project base directory."""
        return self.config.get('paths', {}).get('project_base_dir', '')

    def get_output_dir(self):
        """Get the output directory as an absolute path."""
        output_dir = self.config.get('paths', {}).get('output_dir', 'Output')
        # Convert to absolute path if relative
        if not Path(output_dir).is_absolute():
            return str(self.project_root / output_dir)
        return output_dir

    def get_log_dir(self) -> Path:
        """Get the log directory as an absolute path."""
        log_dir = self.config.get('paths', {}).get('log_dir', 'Logs')
        if not Path(log_dir).is_absolute():
            return self.project_root / log_dir
        return Path(log_dir)

    # ========================================================================
    # File Getters
    # ========================================================================

    def get_database_config_file(self):
        """Get the database config file path."""
        return self.config.get('paths', {}).get('database_config', 'Config/database-config.json')

    def get_database_object_input_file(self):
        """Get the database object input file path."""
        return self.config.get('files', {}).get('database_object_input', 'Config/database-objects-input.txt')

    def get_dependency_sql_script(self):
        """Get the dependency SQL script path."""
        return self.config.get('files', {}).get('dependency_sql_script', 'Core/SQL/Determine Object Dependencies.sql')

    def get_dependency_sql_script_reverse(self):
        """Get the reverse dependency SQL script path."""
        return self.config.get('files', {}).get('dependency_sql_script_reverse', 'Core/SQL/Determine Object Dependencies Reverse.sql')

    def get_dependency_sql_script_forward(self):
        """Get the forward dependency SQL script path."""
        return self.config.get('files', {}).get('dependency_sql_script_forward', 'Core/SQL/Determine Object Dependencies Forward.sql')

    def get_complete_mapping_csv(self):
        """Get the complete mapping CSV filename."""
        return self.config.get('files', {}).get('complete_mapping_csv', 'Complete_StoredProc_to_UI_Mapping.csv')

    def get_complete_mapping_excel(self):
        """Get the complete mapping Excel filename."""
        return self.config.get('files', {}).get('complete_mapping_excel', 'Complete_StoredProc_to_UI_Mapping.xlsx')

    def get_object_dependency_list_json(self):
        """Get the object dependency list JSON filename."""
        return self.config.get('files', {}).get('object_dependency_list_json', 'Object_Dependency_List.json')

    def get_object_dependency_list_reverse_json(self):
        """Get the reverse object dependency list JSON filename."""
        return self.config.get('files', {}).get('object_dependency_list_reverse_json', 'Object_Dependency_List_Reverse.json')

    def get_object_dependency_list_forward_json(self):
        """Get the forward object dependency list JSON filename."""
        return self.config.get('files', {}).get('object_dependency_list_forward_json', 'Object_Dependency_List_Forward.json')

    def get_final_ui_mappings_csv(self):
        """Get the final UI mappings CSV filename."""
        return self.config.get('files', {}).get('final_ui_mappings_csv', 'UI_Mappings_Final.csv')

    def get_final_excel_report(self):
        """Get the final Excel report filename."""
        return self.config.get('files', {}).get('final_excel_report', 'Final_Dependency_Report.xlsx')

    def get_final_excel_report_formatted(self):
        """Get the formatted final Excel report filename."""
        return self.config.get('files', {}).get('final_excel_report_formatted', 'Final_Dependency_Report_Formatted.xlsx')

    # ========================================================================
    # Database Getters
    # ========================================================================

    def _get_available_odbc_driver(self) -> str:
        """
        Detect and return the first available ODBC driver for SQL Server.

        Tries drivers in order: 18, 17, 13, 11, Native Client, SQL Server.

        Returns:
            str: Name of the first available ODBC driver

        Raises:
            RuntimeError: If no compatible ODBC driver is found
        """
        import pyodbc

        drivers_to_try = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "ODBC Driver 11 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]

        available_drivers = pyodbc.drivers()
        for driver in drivers_to_try:
            if driver in available_drivers:
                return driver

        raise RuntimeError(
            f"No compatible ODBC driver found for SQL Server.\n"
            f"Available drivers: {', '.join(available_drivers)}\n"
            f"Please install 'ODBC Driver 17 for SQL Server' or newer.\n"
            f"Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
        )

    def get_odbc_driver(self) -> str:
        """
        Get the ODBC driver name.

        Returns the explicitly configured driver if set in config.json
        (and not set to 'auto'), otherwise auto-detects the best available
        driver installed on the system.
        """
        configured = self.config.get('database', {}).get('odbc_driver', 'auto')
        if configured and configured.strip().lower() != 'auto':
            return configured
        return self._get_available_odbc_driver()

    def _load_database_config(self) -> Dict[str, Any]:
        """Load and validate database configuration from JSON file (cached after first load)."""
        if self._db_config is not None:
            return self._db_config

        db_config_path = self.project_root / self.get_database_config_file()
        try:
            with open(db_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            required_keys = ['servername', 'database']
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise ValueError(f"Missing required keys in database config: {', '.join(missing_keys)}")

            use_windows_auth = config.get('windows_auth', False)
            if not use_windows_auth:
                auth_keys = ['username', 'password']
                missing_auth = [key for key in auth_keys if key not in config]
                if missing_auth:
                    raise ValueError(
                        f"Missing required authentication keys in database config: {', '.join(missing_auth)} "
                        f"(required when 'windows_auth' is not set)"
                    )

            self._db_config = config
            return self._db_config
        except FileNotFoundError:
            raise FileNotFoundError(f"Database configuration file not found: {db_config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in database config file: {e.msg}", e.doc, e.pos
            )

    def get_connection_string(self) -> str:
        """
        Build and return the database connection string.

        Supports both Windows Authentication and SQL Server Authentication.
        If windows_auth is True, uses Windows Authentication (Trusted_Connection).
        Otherwise, uses SQL Server Authentication.

        Returns:
            str: ODBC connection string
        """
        db_config = self._load_database_config()
        odbc_driver = self.get_odbc_driver()
        server = db_config['servername']
        database = db_config['database']
        use_windows_auth = db_config.get('windows_auth', False)

        if use_windows_auth:
            return (
                f"DRIVER={{{odbc_driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"DRIVER={{{odbc_driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={db_config['username']};"
                f"PWD={db_config['password']};"
                f"TrustServerCertificate=yes;"
            )

    def get_database_name(self) -> str:
        """Get the database name from the database configuration."""
        return self._load_database_config().get('database', '')

    def get_connection_timeout(self) -> int:
        """
        Get the database connection timeout in seconds.

        Returns:
            int: Connection timeout in seconds
        """
        try:
            return int(self.config.get('database', {}).get('connection_timeout', 10))
        except (TypeError, ValueError):
            return 10

    def setup_logging(self, script_name: str) -> Path:
        """
        Set up logging for a script, writing to both file and console.

        Args:
            script_name: Name of the script (e.g., '02_generate_dependency_report_reverse_ui_lookup')

        Returns:
            Path: Path to the created log file
        """
        log_dir = Path(self.get_log_dir())
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp_format = self.config.get('logging', {}).get('timestamp_format', '%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime(timestamp_format)
        log_file = log_dir / f"log_{script_name}_{timestamp}.log"

        log_level_str = self.config.get('logging', {}).get('log_level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        log_format = self.config.get('logging', {}).get(
            'log_format', '%(asctime)s - %(levelname)s - %(message)s'
        )

        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )

        return log_file

    # ========================================================================
    # Formatting Getters
    # ========================================================================

    def get_naming_convention(self):
        """Get the naming convention setting."""
        return self.config.get('formatting', {}).get('naming_convention', 'three_part')

    def get_part_naming_convention(self):
        """Get the part naming convention setting."""
        return self.config.get('formatting', {}).get('part_naming_convention', 'object_name')

    def get_remove_object_description(self):
        """Get the remove object description setting."""
        return self.config.get('formatting', {}).get('remove_object_description', False)


