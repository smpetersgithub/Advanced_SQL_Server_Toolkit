"""
Configuration Loader for Execution Plan Analysis Utility

This module provides a centralized configuration loader class that reads
from config.json and provides type-safe getter methods for all configuration values.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Union, List


class ConfigLoader:
    """Centralized configuration loader for Execution Plan Analysis Utility."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config.json. If not provided, uses default location.

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        # Calculate project root once (Python -> Core -> Project Root)
        self.project_root = Path(__file__).parent.parent.parent

        if config_path is None:
            config_path = self.project_root / "Config" / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> dict:
        """
        Load configuration from JSON file.

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file {self.config_path}: {e.msg}",
                e.doc, e.pos
            )

    def _validate_config(self):
        """
        Validate that config has required structure.

        Raises:
            ValueError: If required sections are missing
        """
        required_sections = ['paths', 'files', 'logging', 'excel']
        missing_sections = [s for s in required_sections if s not in self.config]

        if missing_sections:
            raise ValueError(
                f"Missing required sections in config: {', '.join(missing_sections)}"
            )

    def _get_config_value(self, *keys: str, default: Any = None) -> Any:
        """
        Safely get nested config value with default.

        Args:
            *keys: Nested keys to traverse (e.g., 'excel', 'header_color')
            default: Default value if key not found

        Returns:
            Config value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def reload_config(self):
        """
        Reload configuration from file.

        Useful if config.json has been modified during runtime.
        """
        self.config = self._load_config()
        self._validate_config()

    def validate_paths(self):
        """
        Validate that all configured paths exist or can be created.

        Creates directories if they don't exist.
        """
        for path_getter in [self.get_logs_dir, self.get_output_dir, self.get_config_dir]:
            path = path_getter()
            path.mkdir(parents=True, exist_ok=True)
            logging.debug(f"Validated path: {path}")
    
    # ==================== Path Getters ====================

    def get_base_dir(self) -> Path:
        """Get the base directory (project root)."""
        return self.project_root

    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        logs_dir = self._get_config_value('paths', 'logs_dir', default='Logs')
        return self.project_root / logs_dir

    def get_output_dir(self) -> Path:
        """Get the output directory path."""
        output_dir = self._get_config_value('paths', 'output_dir', default='Output')
        return self.project_root / output_dir

    def get_config_dir(self) -> Path:
        """Get the config directory path."""
        config_dir = self._get_config_value('paths', 'config_dir', default='Config')
        return self.project_root / config_dir
    
    # ==================== File Getters ====================

    def get_plan_config_file(self) -> str:
        """Get the execution plan configuration file name."""
        return self._get_config_value('files', 'plan_config_file',
                                       default='execution_plan_config.json')

    def get_json_output_file(self) -> str:
        """Get the JSON output file name for comparison analysis."""
        return self._get_config_value('files', 'json_output_file',
                                       default='execution_plan_analysis.json')

    def get_json_single_plan_output_file(self) -> str:
        """Get the JSON output file name for single plan analysis."""
        return self._get_config_value('files', 'json_single_plan_output_file',
                                       default='single_plan_analysis.json')
    
    # ==================== Logging Getters ====================

    def get_analysis_log_file(self) -> str:
        """Get the analysis log file base name."""
        return self._get_config_value('logging', 'analysis_log_file',
                                       default='log_01_analyze_execution_plans')

    def get_export_log_file(self) -> str:
        """Get the export log file base name."""
        return self._get_config_value('logging', 'export_log_file',
                                       default='log_02_export_to_excel')

    def get_single_plan_analysis_log_file(self) -> str:
        """Get the single plan analysis log file base name."""
        return self._get_config_value('logging', 'single_plan_analysis_log_file',
                                       default='log_03_analyze_single_plan')

    def get_single_plan_export_log_file(self) -> str:
        """Get the single plan export log file base name."""
        return self._get_config_value('logging', 'single_plan_export_log_file',
                                       default='log_04_export_single_plan_to_excel')

    def get_log_format(self) -> str:
        """Get the logging format string."""
        return self._get_config_value('logging', 'log_format',
                                       default='%(asctime)s - %(levelname)s - %(message)s')

    def get_log_level(self) -> str:
        """Get the logging level."""
        return self._get_config_value('logging', 'log_level', default='INFO')

    def get_timestamp_format(self) -> str:
        """Get the timestamp format for log files."""
        return self._get_config_value('logging', 'timestamp_format',
                                       default='%Y%m%d_%H%M%S')

    def get_analysis_timestamp_format(self) -> str:
        """Get the timestamp format for analysis timestamps in JSON."""
        return self._get_config_value('logging', 'analysis_timestamp_format',
                                       default='%Y-%m-%d %H:%M:%S')

    def get_log_filemode(self) -> str:
        """Get the log file mode (w=overwrite, a=append)."""
        return self._get_config_value('logging', 'log_filemode', default='w')
    
    # ==================== Excel Getters ====================

    def get_header_color(self) -> str:
        """Get the Excel header color (hex code without #)."""
        return self._get_config_value('excel', 'header_color', default='4472C4')

    def get_header_font_color(self) -> str:
        """Get the Excel header font color (hex code without #)."""
        return self._get_config_value('excel', 'header_font_color', default='FFFFFF')

    def get_header_font_size(self) -> int:
        """Get the Excel header font size."""
        return self._get_config_value('excel', 'header_font_size', default=11)

    def get_excel_engine(self) -> str:
        """Get the Excel engine to use."""
        return self._get_config_value('excel', 'excel_engine', default='openpyxl')

    def get_max_sheet_name_length(self) -> int:
        """Get the maximum sheet name length."""
        return self._get_config_value('excel', 'max_sheet_name_length', default=31)

    def get_summary_tab_color(self) -> str:
        """Get the summary tab color (hex code without #)."""
        return self._get_config_value('excel', 'summary_tab_color', default='4472C4')

    def get_plan1_tab_color(self) -> str:
        """Get the plan 1 tab color (hex code without #)."""
        return self._get_config_value('excel', 'plan1_tab_color', default='70AD47')

    def get_plan2_tab_color(self) -> str:
        """Get the plan 2 tab color (hex code without #)."""
        return self._get_config_value('excel', 'plan2_tab_color', default='FFC000')
    
    # ==================== Logging Setup ====================

    def setup_logging(self, log_file_base_name: str) -> Path:
        """
        Set up logging for a script.

        Args:
            log_file_base_name: Base name of the log file (e.g., 'log_01_analyze_execution_plans')

        Returns:
            Path to the log file

        Raises:
            ValueError: If log level is invalid
        """
        log_dir = self.get_logs_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(self.get_timestamp_format())
        log_file = log_dir / f"{log_file_base_name}_{timestamp}.log"

        # Get log level using getattr for cleaner code
        log_level_name = self.get_log_level().upper()
        log_level_value = getattr(logging, log_level_name, None)

        if log_level_value is None:
            # Fallback to INFO if invalid level specified
            logging.warning(f"Invalid log level '{log_level_name}', using INFO")
            log_level_value = logging.INFO

        logging.basicConfig(
            filename=str(log_file),
            level=log_level_value,
            format=self.get_log_format(),
            filemode=self.get_log_filemode()
        )

        return log_file

