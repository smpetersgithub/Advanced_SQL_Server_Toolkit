"""
Configuration Loader for DDL Generator Utility

This module provides a centralized configuration loader class that reads
from config.json and provides type-safe getter methods for all configuration values.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class ConfigLoader:
    """Centralized configuration loader for DDL Generator Utility."""


    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config.json. If not provided, uses default location.

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file contains invalid JSON
            KeyError: If required config sections are missing
        """
        # Calculate project root (Python -> Core -> Project Root)
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "Config" / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
        self.project_root = Path(__file__).parent.parent.parent

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Returns:
            Dict containing the configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file contains invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file {self.config_path}: {e.msg}",
                e.doc,
                e.pos
            )

    def _validate_config(self) -> None:
        """
        Validate that required configuration sections exist.

        Raises:
            KeyError: If required sections are missing
        """
        required_sections = ['paths', 'logging']
        for section in required_sections:
            if section not in self.config:
                raise KeyError(f"Required configuration section '{section}' not found in {self.config_path}")

        # Validate required path keys
        required_paths = ['config_dir', 'database_config_dir', 'log_dir', 'generated_scripts_dir']
        for path_key in required_paths:
            if path_key not in self.config['paths']:
                raise KeyError(f"Required path '{path_key}' not found in config.json paths section")
    
    # ==================== Path Getters ====================

    def get_workspace_dir(self) -> Path:
        """
        Get the workspace directory path.

        Derived from the location of this config_loader.py file
        (Core/Python -> Core -> project root), making it location-independent.
        Previously this was read from a hardcoded absolute path in config.json;
        that entry has been removed.

        Returns:
            Path: Workspace (project root) directory path
        """
        return self.project_root

    def get_config_dir(self) -> Path:
        """
        Get the config directory path.

        Returns:
            Path: Config directory path
        """
        return self.project_root / self.config['paths']['config_dir']

    def get_database_config_dir(self) -> Path:
        """
        Get the database config directory path.

        Returns:
            Path: Database config directory path
        """
        return self.project_root / self.config['paths']['database_config_dir']

    def get_log_dir(self) -> Path:
        """
        Get the log directory path.

        Returns:
            Path: Log directory path
        """
        return self.project_root / self.config['paths']['log_dir']

    def get_generated_scripts_dir(self) -> Path:
        """
        Get the generated scripts directory path.

        Returns:
            Path: Generated scripts directory path
        """
        return self.project_root / self.config['paths']['generated_scripts_dir']
    
    # ==================== Logging Getters ====================

    def get_log_format(self) -> str:
        """
        Get the logging format string.

        Returns:
            str: Logging format string
        """
        return self.config['logging']['log_format']

    def get_log_level(self) -> str:
        """
        Get the logging level.

        Returns:
            str: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        return self.config['logging']['log_level']

    def get_timestamp_format(self) -> str:
        """
        Get the timestamp format for log files.

        Returns:
            str: Timestamp format string
        """
        return self.config['logging']['timestamp_format']

    def get_log_filemode(self) -> str:
        """
        Get the log file mode (w=overwrite, a=append).

        Returns:
            str: File mode ('w' or 'a')
        """
        return self.config['logging'].get('log_filemode', 'a')

    # ==================== Database Getters ====================

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
        configured = self.config.get('database', {}).get('odbc_driver', 'auto')
        if configured and str(configured).strip().lower() != 'auto':
            return configured
        return self._get_available_odbc_driver()

    def get_connection_string(self, server: str, user: str = "", password: str = "",
                              db_name: str = "master",
                              driver_hint: Optional[str] = None,
                              windows_auth: bool = False) -> str:
        """
        Build and return an ODBC connection string for SQL Server.

        This method is intentionally parameterized because the DDL Generator
        operates against multiple servers. Credentials are supplied by the
        caller (read from the servers array in database-config.json) rather
        than from a single pre-loaded config, which is why the signature
        differs from the zero-argument get_connection_string() found in the
        single-server utilities (Normalization, Dependency, Query Store).

        Supports both Windows Authentication and SQL Server Authentication.
        When windows_auth is True, user and password are ignored.

        Args:
            server: SQL Server hostname or IP
            user: SQL Server username (required when windows_auth is False)
            password: SQL Server password (required when windows_auth is False)
            db_name: Database name (default: "master")
            driver_hint: Optional explicit driver override. If omitted, the
                         best available driver is auto-detected.
            windows_auth: If True, uses Windows Authentication (Trusted_Connection).
                          If False (default), uses SQL Server Authentication.

        Returns:
            str: ODBC connection string
        """
        driver = driver_hint if driver_hint else self.get_odbc_driver()

        if windows_auth:
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={db_name};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={db_name};"
                f"UID={user};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
            )
    
    # ==================== Logging Setup ====================

    def setup_logging(self, script_name: str) -> Path:
        """
        Set up logging for a script.

        Args:
            script_name: Name of the script (e.g., '01_generate_database_configs')

        Returns:
            Path: Path to the log file

        Raises:
            OSError: If log directory cannot be created
        """
        log_dir = self.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(self.get_timestamp_format())
        log_file = log_dir / f"log_{script_name}_{timestamp}.log"

        log_level_value = getattr(logging, self.get_log_level().upper(), logging.INFO)

        logging.basicConfig(
            level=log_level_value,
            format=self.get_log_format(),
            handlers=[
                logging.FileHandler(str(log_file), mode=self.get_log_filemode(), encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )

        return log_file
