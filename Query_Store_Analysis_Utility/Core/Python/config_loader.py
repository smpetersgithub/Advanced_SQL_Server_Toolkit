"""
Configuration Loader for Query Store Analysis Utility

This module provides a centralized configuration loader class that reads
from multiple config files and provides type-safe getter methods for all configuration values.
"""

import json
import logging
from pathlib import Path
from datetime import datetime


class ConfigLoader:
    """Centralized configuration loader for Query Store Analysis Utility."""

    def __init__(self, config_path=None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config.json. If not provided, uses default location.
        """
        # Calculate project root (Python -> Core -> Project Root)
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "Config" / "config.json"

        self.config_path = Path(config_path)
        self.project_root = Path(__file__).parent.parent.parent

        # Load main configuration
        self.config = self._load_config()

        # Load additional config files
        self.reports_config = self._load_reports_config()
        self.active_report_config = self._load_active_report_config()
        self.database_config = None  # Loaded on demand

    def _load_config(self):
        """Load main configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_reports_config(self):
        """Load reports configuration."""
        reports_config_path = self.project_root / self.config['paths']['config']['reports_config']
        if not reports_config_path.exists():
            raise FileNotFoundError(f"Reports config not found: {reports_config_path}")

        with open(reports_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_active_report_config(self):
        """Load active report configuration."""
        active_report_path = self.project_root / self.config['paths']['config']['active_report_config']
        if not active_report_path.exists():
            raise FileNotFoundError(f"Active report config not found: {active_report_path}")

        with open(active_report_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_database_config(self):
        """Load database configuration (lazy loading)."""
        if self.database_config is None:
            db_config_path = self.project_root / self.config['paths']['config']['database_config']
            if not db_config_path.exists():
                raise FileNotFoundError(f"Database config not found: {db_config_path}")

            with open(db_config_path, 'r', encoding='utf-8') as f:
                self.database_config = json.load(f)

        return self.database_config

    # ==================== Path Getters ====================

    def get_project_root(self):
        """Get the project root directory."""
        return self.project_root

    def get_logs_base_dir(self):
        """Get the logs base directory path."""
        return self.project_root / self.config['paths']['logs']['base_dir']

    def get_database_config_path(self):
        """Get the database config file path."""
        return self.config['paths']['config']['database_config']

    def get_reports_config_path(self):
        """Get the reports config file path."""
        return self.config['paths']['config']['reports_config']

    def get_active_report_config_path(self):
        """Get the active report config file path."""
        return self.config['paths']['config']['active_report_config']

    def get_github_procs_path(self):
        """Get the GitHub repository procs path."""
        return self.config['paths']['github_repo']['procs']

    def get_github_functions_path(self):
        """Get the GitHub repository functions path."""
        return self.config['paths']['github_repo']['functions']

    # ==================== Processing Getters ====================

    def get_xml_plan_download_batch_size(self):
        """Get the XML plan download batch size."""
        return self.config['processing']['xml_plan_download_batch_size']

    def get_sql_fetch_batch_size(self):
        """Get the SQL fetch batch size."""
        return self.config['processing']['sql_fetch_batch_size']

    def get_xml_file_extension(self):
        """Get the XML file extension."""
        return self.config['processing']['xml_file_extension']

    def get_json_file_extension(self):
        """Get the JSON file extension."""
        return self.config['processing']['json_file_extension']

    # ==================== Logging Getters ====================

    def get_log_level(self):
        """Get the logging level."""
        return self.config['logging']['level']

    def get_log_format(self):
        """Get the logging format string."""
        return self.config['logging']['format']

    def get_timestamp_format(self):
        """Get the timestamp format for log files."""
        return self.config['logging']['timestamp_format']

    def get_log_file_name(self, script_key):
        """
        Get the log file name template for a specific script.

        Args:
            script_key: Script identifier (e.g., 'script_01', 'script_02')

        Returns:
            Log file name template with {timestamp} placeholder
        """
        return self.config['logging']['log_file_names'].get(script_key, f"{script_key}_{{timestamp}}.log")


    # ==================== Report Configuration Getters ====================

    def get_active_report_key(self):
        """Get the currently active report key."""
        return self.active_report_config['active_report']

    def get_active_report_settings(self):
        """
        Get the settings for the currently active report.

        Returns:
            Tuple of (report_key, report_settings)

        Raises:
            ValueError: If active report is not found or not enabled
        """
        active_report_key = self.get_active_report_key()

        if active_report_key not in self.reports_config['reports']:
            raise ValueError(f"Active report '{active_report_key}' not found in reports-config.json")

        report_settings = self.reports_config['reports'][active_report_key]

        if not report_settings.get('enabled', False):
            raise ValueError(f"Report '{active_report_key}' is not enabled in reports-config.json")

        return active_report_key, report_settings

    def get_report_settings(self, report_key):
        """
        Get settings for a specific report.

        Args:
            report_key: The report identifier

        Returns:
            Report settings dictionary
        """
        if report_key not in self.reports_config['reports']:
            raise ValueError(f"Report '{report_key}' not found in reports-config.json")

        return self.reports_config['reports'][report_key]

    def get_all_reports(self):
        """Get all available reports."""
        return self.reports_config['reports']

    def get_enabled_reports(self):
        """Get all enabled reports."""
        return {key: value for key, value in self.reports_config['reports'].items()
                if value.get('enabled', False)}

    # ==================== Database Configuration Getters ====================

    def get_database_config(self):
        """Get the complete database configuration."""
        return self._load_database_config()

    def get_connection_string(self):
        """Build and return the database connection string.

        Supports both Windows Authentication and SQL Server Authentication.
        If username/password are provided, uses SQL Server Authentication.
        Otherwise, uses Windows Authentication (Trusted_Connection).

        Automatically detects available ODBC driver (tries 18, 17, 13, 11 in order).

        Raises:
            ValueError: If required database configuration fields are missing
            RuntimeError: If no compatible ODBC driver is found
        """
        db_config = self._load_database_config()

        # Validate required fields
        if 'servername' not in db_config:
            raise ValueError(
                "Database configuration is missing required field 'servername'. "
                "Please check Config/database-config.json"
            )

        server = db_config['servername']
        database = db_config.get('database', 'master')
        username = db_config.get('username', '')
        password = db_config.get('password', '')

        # Detect available ODBC driver
        driver = self._get_available_odbc_driver()

        # Determine authentication method
        use_sql_auth = bool(username and password)

        if use_sql_auth:
            # SQL Server Authentication
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
            )
        else:
            # Windows Authentication
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )

        return conn_str

    def _get_available_odbc_driver(self):
        """Detect and return the first available ODBC driver for SQL Server.

        Tries drivers in order: 18, 17, 13, 11

        Returns:
            str: Name of the available ODBC driver

        Raises:
            RuntimeError: If no compatible ODBC driver is found
        """
        import pyodbc

        # List of drivers to try (newest to oldest)
        drivers_to_try = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "ODBC Driver 11 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]

        # Get list of available drivers
        available_drivers = [driver for driver in pyodbc.drivers()]

        # Find first matching driver
        for driver in drivers_to_try:
            if driver in available_drivers:
                return driver

        # No driver found - raise error with helpful message
        raise RuntimeError(
            f"No compatible ODBC driver found for SQL Server.\n"
            f"Available drivers: {', '.join(available_drivers)}\n"
            f"Please install 'ODBC Driver 17 for SQL Server' or newer.\n"
            f"Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
        )

    def get_server(self):
        """Get the database server name.

        Raises:
            ValueError: If 'servername' field is missing from database config
        """
        db_config = self._load_database_config()
        if 'servername' not in db_config:
            raise ValueError(
                "Database configuration is missing required field 'servername'. "
                "Please check Config/database-config.json"
            )
        return db_config['servername']

    def get_database(self):
        """Get the database name."""
        return self._load_database_config().get('database', 'master')

    # ==================== Utility Methods ====================

    def setup_logging(self, log_filename):
        """
        Setup logging configuration to write to both file and console.

        Args:
            log_filename: Script identifier (e.g., 'script_01', 'script_02', 'run_all_scripts')

        Returns:
            Path: Path to the created log file

        Note:
            After calling this method, use logging.getLogger(__name__) to get a logger instance.
            Log files are named: log_<script_name>_<timestamp>.log
        """
        # Create logs directory
        log_dir = self.get_logs_base_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Map script identifiers to descriptive log names
        log_name_map = {
            'script_01': 'log_01_extract_query_store_data',
            'script_02': 'log_02_extract_xml_execution_plans',
            'script_03': 'log_03_extract_table_names_from_xml_plans',
            'script_04': 'log_04_extract_index_and_statistics_for_tables',
            'script_05': 'log_05_create_json_execution_plans',
            'script_06': 'log_06_lookup_query_by_id',
            'run_all_scripts': 'log_run_all_scripts'
        }

        # Get mapped name or use provided name with 'log_' prefix
        if log_filename in log_name_map:
            log_base_name = log_name_map[log_filename]
        else:
            # If not in map, add 'log_' prefix if not already present
            log_base_name = log_filename if log_filename.startswith('log_') else f'log_{log_filename}'

        # Create log filename with timestamp: log_<script_name>_<timestamp>.log
        log_file_name = f"{log_base_name}_{timestamp}.log"
        log_file = log_dir / log_file_name

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ],
            force=True  # Force reconfiguration if already configured
        )

        return log_file

    def get_sql_file_path(self, report_key, sql_file_key):
        """
        Get the full path to a SQL file for a specific report.

        Args:
            report_key: The report identifier
            sql_file_key: The SQL file key (e.g., 'main_query', 'index_detail')

        Returns:
            Path to the SQL file
        """
        report_settings = self.get_report_settings(report_key)
        sql_file_relative = report_settings['sql_files'][sql_file_key]
        return self.project_root / sql_file_relative

    def get_output_dir(self, report_key):
        """
        Get the output directory for a specific report.

        Args:
            report_key: The report identifier

        Returns:
            Path to the output directory
        """
        report_settings = self.get_report_settings(report_key)
        output_base = report_settings['output']['base_dir']
        return self.project_root / output_base

    def reload_configs(self):
        """Reload all configuration files."""
        self.config = self._load_config()
        self.reports_config = self._load_reports_config()
        self.active_report_config = self._load_active_report_config()
        self.database_config = None  # Reset to force reload on next access


