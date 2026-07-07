"""
Shared configuration loader for all Python scripts.
Loads both database configuration and Python settings.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Centralized configuration loader for the normalization analysis utility."""

    def __init__(self, config_path=None):
        """
        Initialize the config loader and determine project root.

        Args:
            config_path: Optional path to config.json. If not provided, uses default location.

        Raises:
            FileNotFoundError: If configuration files are not found
            json.JSONDecodeError: If configuration files contain invalid JSON
            ValueError: If configuration structure is invalid
        """
        # Determine project root (go up from Core/Python to project root)
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent

        # Load Python configuration
        if config_path is None:
            config_path = self.project_root / "Config" / "config.json"
        self.config_path = Path(config_path)
        self.config = self._load_json(self.config_path, "Python configuration")

        # Validate Python configuration structure
        self._validate_python_config()

        # Load database configuration
        try:
            db_config_relative = self.config['paths']['database_config']
        except KeyError as e:
            raise KeyError(f"Python configuration missing required key: {e}. Please check {self.config_path}")

        self.db_config_path = self.project_root / db_config_relative
        self.db_config = self._load_json(self.db_config_path, "Database configuration")
        self._validate_database_config()

        # Load table configuration
        try:
            table_config_relative = self.config['paths']['table_config']
        except KeyError as e:
            raise KeyError(f"Python configuration missing required key: {e}. Please check {self.config_path}")

        self.table_config_path = self.project_root / table_config_relative
        self.table_config = self._load_json(self.table_config_path, "Table configuration")

        # Merge database and table configs for backward compatibility
        self.merged_config = {**self.db_config, **self.table_config}

    def _load_json(self, file_path: Path, description: str) -> Dict[str, Any]:
        """
        Load a JSON file with error handling.

        Args:
            file_path: Path to the JSON file
            description: Description of the file for error messages

        Returns:
            Dictionary containing the loaded JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"{description} file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {description} file: {e.msg}", e.doc, e.pos
            )

    def _validate_python_config(self) -> None:
        """
        Validate that the Python configuration has all required fields.

        Raises:
            ValueError: If required fields are missing
        """
        required_sections = {
            'paths': ['database_config', 'table_config', 'output_directory', 'functional_dependencies_output'],
            'analysis': ['max_determinant_size', 'progress_update_interval'],
            'database': ['odbc_driver', 'default_schema'],
            'excel': ['header_font_color', 'header_font_size', 'header_color', 'min_column_width', 'max_column_width'],
            'logging': ['show_progress', 'show_sql_queries']
        }

        for section, keys in required_sections.items():
            if section not in self.config:
                raise ValueError(f"Python configuration missing required section: '{section}'")

            for key in keys:
                if key not in self.config[section]:
                    raise ValueError(f"Python configuration section '{section}' missing required key: '{key}'")

    def _validate_database_config(self) -> None:
        """
        Validate that the database configuration has all required fields.

        Raises:
            ValueError: If required fields are missing
        """
        required_always = ['servername', 'database']
        for key in required_always:
            if key not in self.db_config:
                raise ValueError(
                    f"Database configuration missing required field: '{key}'. "
                    f"Please check {self.db_config_path}"
                )

        use_windows_auth = self.db_config.get('windows_auth', False)
        if not use_windows_auth:
            required_auth = ['username', 'password']
            for key in required_auth:
                if key not in self.db_config:
                    raise ValueError(
                        f"Database configuration missing required field: '{key}' "
                        f"(required when 'windows_auth' is not set). "
                        f"Please check {self.db_config_path}"
                    )

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get the merged database and table configuration.

        Returns:
            Dictionary containing merged database and table configuration
        """
        return self.merged_config

    def get_database_connection_config(self) -> Dict[str, Any]:
        """
        Get only the database connection configuration.

        Returns:
            Dictionary containing database connection configuration
        """
        return self.db_config

    def get_connection_string(self) -> str:
        """
        Build and return the database connection string.

        Supports both Windows Authentication and SQL Server Authentication.
        If windows_auth is True, uses Windows Authentication (Trusted_Connection).
        Otherwise, uses SQL Server Authentication.

        Returns:
            str: ODBC connection string
        """
        odbc_driver = self.get_odbc_driver()
        server = self.db_config['servername']
        database = self.db_config['database']
        use_windows_auth = self.db_config.get('windows_auth', False)

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
                f"UID={self.db_config['username']};"
                f"PWD={self.db_config['password']};"
                f"TrustServerCertificate=yes;"
            )

    def get_table_config(self) -> Dict[str, Any]:
        """
        Get only the table configuration.

        Returns:
            Dictionary containing table configuration
        """
        return self.table_config

    def get_python_config(self) -> Dict[str, Any]:
        """
        Get the settings configuration.

        Returns:
            Dictionary containing settings
        """
        return self.config

    def get_output_path(self, filename: Optional[str] = None) -> Path:
        """
        Get the full path to the output directory or a specific output file.

        Args:
            filename: Optional filename to append to output directory

        Returns:
            Path to output directory or specific file
        """
        try:
            output_dir = self.project_root / self.config['paths']['output_directory']
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename:
            return output_dir / filename
        return output_dir

    def get_functional_dependencies_path(self) -> Path:
        """
        Get the path to the functional dependencies JSON output file.

        Returns:
            Path to functional dependencies output file
        """
        try:
            fd_path = self.config['paths']['functional_dependencies_output']
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)
        return self.project_root / fd_path

    def get_database_config_path(self) -> Path:
        """
        Get the path to the database connection configuration file.

        Returns:
            Path to database configuration file
        """
        return self.db_config_path

    def get_table_config_path(self) -> Path:
        """
        Get the path to the table configuration file.

        Returns:
            Path to table configuration file
        """
        return self.table_config_path

    def save_database_config(self, config: Dict[str, Any]) -> None:
        """
        Save updated configuration back to appropriate files.

        Splits the merged config into table-specific fields (table, columns, primarykey, uniquekey)
        and database connection fields (servername, database, username, password), then saves each
        to their respective configuration files.

        Args:
            config: Dictionary containing configuration to save

        Raises:
            PermissionError: If no permission to write files
            IOError: If files cannot be written
        """
        # Extract table-specific fields
        table_fields = ['table', 'columns', 'primarykey', 'uniquekey']
        table_config = {k: v for k, v in config.items() if k in table_fields}

        # Extract database connection fields
        db_fields = ['servername', 'database', 'username', 'password', 'windows_auth']
        db_config = {k: v for k, v in config.items() if k in db_fields}

        # Save table config
        try:
            with open(self.table_config_path, 'w') as f:
                json.dump(table_config, f, indent=2)
            print(f"Table configuration updated and saved to: {self.table_config_path}")
        except PermissionError:
            print(f"Error: Permission denied writing to {self.table_config_path}")
            print("Please check file permissions and try again.")
            sys.exit(1)
        except IOError as e:
            print(f"Error: Cannot write to table config file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error saving table config file: {e}")
            sys.exit(1)

        # Save database config if it has changes
        if db_config:
            try:
                with open(self.db_config_path, 'w') as f:
                    json.dump(db_config, f, indent=2)
                print(f"Database configuration updated and saved to: {self.db_config_path}")
            except PermissionError:
                print(f"Error: Permission denied writing to {self.db_config_path}")
                print("Please check file permissions and try again.")
                sys.exit(1)
            except IOError as e:
                print(f"Error: Cannot write to database config file: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"Error saving database config file: {e}")
                sys.exit(1)

    def get_max_determinant_size(self) -> int:
        """
        Get the maximum determinant size for analysis.

        Returns:
            Maximum determinant size (validated to be positive integer)
        """
        try:
            max_size = self.config['analysis']['max_determinant_size']
            if not isinstance(max_size, int) or max_size < 1:
                raise ValueError(f"max_determinant_size must be a positive integer, got: {max_size}")
            return max_size
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

    def get_progress_update_interval(self) -> int:
        """
        Get the progress update interval.

        Returns:
            Progress update interval (validated to be positive integer)
        """
        try:
            interval = self.config['analysis']['progress_update_interval']
            if not isinstance(interval, int) or interval < 1:
                raise ValueError(f"progress_update_interval must be a positive integer, got: {interval}")
            return interval
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

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

        Returns:
            str: ODBC driver name string
        """
        try:
            configured = self.config['database']['odbc_driver']
            if configured and configured.strip().lower() != 'auto':
                return configured
        except KeyError:
            pass
        return self._get_available_odbc_driver()

    def get_default_schema(self) -> str:
        """
        Get the default database schema.

        Returns:
            Default schema name string
        """
        try:
            schema = self.config['database']['default_schema']
            if not isinstance(schema, str) or not schema.strip():
                raise ValueError(f"default_schema must be a non-empty string, got: {schema}")
            return schema
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

    def get_excel_config(self) -> Dict[str, Any]:
        """
        Get the Excel formatting configuration.

        Returns:
            Dictionary containing Excel formatting settings
        """
        try:
            return self.config['excel']
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

    def should_show_progress(self) -> bool:
        """
        Check if progress should be shown.

        Returns:
            Boolean indicating whether to show progress
        """
        try:
            return bool(self.config['logging']['show_progress'])
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

    def should_show_sql_queries(self) -> bool:
        """
        Check if SQL queries should be shown.

        Returns:
            Boolean indicating whether to show SQL queries
        """
        try:
            return bool(self.config['logging']['show_sql_queries'])
        except KeyError as e:
            print(f"Error: Python configuration missing required key: {e}")
            sys.exit(1)

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

    def get_log_dir(self) -> Path:
        """
        Get the log directory as an absolute path.

        Returns:
            Path: Absolute path to the log directory
        """
        log_dir = self.config.get('paths', {}).get('log_dir', 'Logs')
        if not Path(log_dir).is_absolute():
            return self.project_root / log_dir
        return Path(log_dir)

    def setup_logging(self, script_name: str) -> Path:
        """
        Set up logging for a script, writing to both file and console.

        Args:
            script_name: Name of the script (e.g., '00_populate_columns_from_database')

        Returns:
            Path: Path to the created log file
        """
        log_dir = self.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(
            self.config.get('logging', {}).get('timestamp_format', '%Y%m%d_%H%M%S')
        )
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