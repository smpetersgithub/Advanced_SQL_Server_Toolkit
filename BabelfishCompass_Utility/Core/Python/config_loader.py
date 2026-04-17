"""
Shared configuration loader for all Python scripts in BabelfishCompass_Utility.
Loads configuration from config.json and provides centralized access to settings.
"""

import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class ConfigLoader:
    """Centralized configuration loader for the BabelfishCompass utility."""

    def __init__(self):
        """Initialize the config loader and determine project root."""
        # Determine project root (go up from Core/Python to project root)
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent

        # Load configuration from config.json
        self.config_path = self.project_root / "Config" / "config.json"
        self.config = self._load_json(self.config_path, "Configuration")

        # Validate configuration has all required sections and values
        self._validate_config()
        self._validate_config_values()

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return f"ConfigLoader(config_path='{self.config_path}')"

    def __str__(self) -> str:
        """Return a user-friendly string representation."""
        return f"ConfigLoader loaded from {self.config_path}"

    def _load_json(self, file_path: Path, description: str) -> Dict[str, Any]:
        """Load a JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"[ERROR] {description} file not found: {file_path}")
            print(f"Please ensure config.json exists in the Config directory.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {description} file: {e}")
            print("Please check your config.json file for syntax errors.")
            sys.exit(1)

    def _validate_config(self) -> None:
        """Validate that all required configuration sections and keys exist."""
        required_sections = {
            'paths': ['babelfish_dir', 'sql_examples_dir', 'sqlite_dir', 'core_dir', 'logs_dir'],
            'defaults': ['default_report_name'],
            'database': ['table_name'],
            'postgresql': ['pg_connection'],
            'babelfishcompass': ['dat_file_pattern', 'report_location_pattern', 'step1_options'],
            'display': ['ascii_art_file'],
            'logging': ['log_format', 'log_level', 'timestamp_format', 'log_filemode']
        }

        missing_sections = []
        missing_keys = []

        # Check for missing sections
        for section in required_sections.keys():
            if section not in self.config:
                missing_sections.append(section)
            else:
                # Check for missing keys within each section
                for key in required_sections[section]:
                    if key not in self.config[section]:
                        missing_keys.append(f"{section}.{key}")

        # Report errors if any
        if missing_sections or missing_keys:
            print(f"[ERROR] Configuration validation failed in {self.config_path}")
            if missing_sections:
                print(f"  Missing sections: {', '.join(missing_sections)}")
            if missing_keys:
                print(f"  Missing keys: {', '.join(missing_keys)}")
            print("Please check your config.json file.")
            sys.exit(1)

    def _validate_config_values(self) -> None:
        """Validate that configuration values are reasonable."""
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = self.config['logging']['log_level'].upper()
        if log_level not in valid_log_levels:
            print(f"[WARNING] Invalid log level '{log_level}', using INFO")
            self.config['logging']['log_level'] = 'INFO'

        # Validate table name is not empty
        table_name = self.config['database']['table_name']
        if not table_name or not table_name.strip():
            print(f"[ERROR] database.table_name cannot be empty")
            sys.exit(1)

        # Validate default report name is not empty
        report_name = self.config['defaults']['default_report_name']
        if not report_name or not report_name.strip():
            print(f"[ERROR] defaults.default_report_name cannot be empty")
            sys.exit(1)

    def reload(self) -> None:
        """
        Reload configuration from disk.

        This allows updating configuration without restarting the application.
        Useful for long-running processes or when config.json is modified.
        """
        self.config = self._load_json(self.config_path, "Configuration")
        self._validate_config()
        self._validate_config_values()

    # ========================================================================
    # Project Root Getter
    # ========================================================================

    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self.project_root

    # ========================================================================
    # Path Getters
    # ========================================================================

    def get_babelfish_dir(self) -> Path:
        """Get the BabelfishCompass directory path."""
        return self.project_root / self.config['paths']['babelfish_dir']

    def get_sql_examples_dir(self) -> Path:
        """Get the SQL examples directory path."""
        return self.project_root / self.config['paths']['sql_examples_dir']

    def get_sqlite_dir(self) -> Path:
        """Get the SQLite directory path."""
        return self.project_root / self.config['paths']['sqlite_dir']

    def get_core_dir(self) -> Path:
        """Get the Core directory path."""
        return self.project_root / self.config['paths']['core_dir']

    def get_logs_dir(self) -> Path:
        """Get the Logs directory path."""
        return self.project_root / self.config['paths']['logs_dir']

    # ========================================================================
    # Default Settings Getters
    # ========================================================================

    def get_default_report_name(self) -> str:
        """Get the default report name."""
        return self.config['defaults']['default_report_name']

    # ========================================================================
    # Database Settings Getters
    # ========================================================================

    def get_table_name(self) -> str:
        """Get the database table name."""
        return self.config['database']['table_name']

    # ========================================================================
    # PostgreSQL Settings Getters
    # ========================================================================

    def get_pg_connection(self) -> str:
        """
        Get the PostgreSQL connection string.

        Can be overridden by PG_CONNECTION environment variable.
        This is useful for CI/CD, Docker, or different environments.
        """
        return os.getenv('PG_CONNECTION') or self.config['postgresql']['pg_connection']

    # ========================================================================
    # BabelfishCompass Settings Getters
    # ========================================================================

    def get_dat_file_pattern(self) -> str:
        """Get the DAT file path pattern."""
        return self.config['babelfishcompass']['dat_file_pattern']

    def get_step1_options(self) -> str:
        """Get the BabelfishCompass step 1 command-line options."""
        return self.config['babelfishcompass']['step1_options']

    def get_report_location_pattern(self) -> str:
        """Get the report location path pattern."""
        return self.config['babelfishcompass']['report_location_pattern']

    # ========================================================================
    # Display Settings Getters
    # ========================================================================

    def get_ascii_art_file(self) -> str:
        """Get the ASCII art filename."""
        return self.config['display']['ascii_art_file']

    # ========================================================================
    # Logging Configuration
    # ========================================================================

    def get_logging_config(self) -> Dict[str, str]:
        """
        Get all logging configuration settings.

        Note: Defaults are not needed here since _validate_config() ensures
        all required keys exist. Direct access is safe.
        """
        return {
            'log_format': self.config['logging']['log_format'],
            'log_level': self.config['logging']['log_level'],
            'timestamp_format': self.config['logging']['timestamp_format'],
            'log_filemode': self.config['logging']['log_filemode']
        }

    def setup_logging(self, script_name: str) -> Path:
        """
        Setup logging for a script with standardized configuration.

        Args:
            script_name: Name of the script (e.g., '01_Generate_BabelfishCompass_Report')

        Returns:
            Path to the log file

        Note:
            This method clears existing handlers before reconfiguring to allow
            multiple calls to setup_logging() in the same process. This is necessary
            because logging.basicConfig() only works on the first call by default.
        """
        # Create logs directory using config
        logs_dir = self.get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Get logging configuration
        log_config = self.get_logging_config()

        # Create log filename with timestamp
        timestamp = datetime.now().strftime(log_config['timestamp_format'])
        log_filename = f"log_{script_name}_{timestamp}.log"
        log_file = logs_dir / log_filename

        # Map log level string to logging constant
        log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level_value = log_level_map.get(log_config['log_level'].upper(), logging.INFO)

        # Clear existing handlers to allow reconfiguration
        # This is necessary because basicConfig() only works on first call
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Configure logging - file only, no console output
        logging.basicConfig(
            filename=str(log_file),
            level=log_level_value,
            format=log_config['log_format'],
            filemode=log_config['log_filemode']
        )

        return log_file

