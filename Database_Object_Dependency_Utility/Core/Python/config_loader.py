"""
Configuration loader for Database Object Dependency Utility.
Loads configuration from config.json file.
"""

import json
import sys
import logging
from pathlib import Path


class ConfigLoader:
    """Centralized configuration loader for the Database Object Dependency utility."""

    def __init__(self, config_path=None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config.json. If not provided, will auto-detect.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)

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

    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            self.logger.error("Please ensure config.json exists in the Config directory.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            self.logger.error("Please check your config.json file for syntax errors.")
            sys.exit(1)

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

    def get_log_dir(self):
        """Get the log directory as an absolute path."""
        log_dir = self.config.get('paths', {}).get('log_dir', 'Logs')
        # Convert to absolute path if relative
        if not Path(log_dir).is_absolute():
            return str(self.project_root / log_dir)
        return log_dir

    # ========================================================================
    # File Getters
    # ========================================================================

    def get_database_config_file(self):
        """Get the database config file path."""
        return self.config.get('files', {}).get('database_config', 'Config/database-config.json')

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

    def get_odbc_driver(self):
        """Get the ODBC driver name."""
        return self.config.get('database', {}).get('odbc_driver', 'ODBC Driver 17 for SQL Server')

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


