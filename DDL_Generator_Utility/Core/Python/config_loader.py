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

    # Log level mapping constant
    LOG_LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

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
        self.project_root = Path(self.config['paths']['workspace_dir'])

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
        required_paths = ['workspace_dir', 'config_dir', 'database_config_dir', 'log_dir', 'generated_scripts_dir']
        for path_key in required_paths:
            if path_key not in self.config['paths']:
                raise KeyError(f"Required path '{path_key}' not found in config.json paths section")
    
    # ==================== Path Getters ====================

    def get_workspace_dir(self) -> Path:
        """
        Get the workspace directory path.

        Returns:
            Path: Workspace directory path
        """
        return Path(self.config['paths']['workspace_dir'])

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
        return self.config['logging'].get('log_filemode', 'w')
    
    # ==================== Database Getters ====================

    def get_connection_timeout(self) -> int:
        """
        Get the database connection timeout in seconds.

        Returns:
            int: Connection timeout in seconds
        """
        return self.config.get('database', {}).get('connection_timeout', 10)
    
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

        log_level_value = self.LOG_LEVEL_MAP.get(self.get_log_level().upper(), logging.INFO)

        logging.basicConfig(
            filename=str(log_file),
            level=log_level_value,
            format=self.get_log_format(),
            filemode=self.get_log_filemode()
        )

        return log_file

