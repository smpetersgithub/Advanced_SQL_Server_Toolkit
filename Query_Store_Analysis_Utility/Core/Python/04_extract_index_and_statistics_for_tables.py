"""
Extract Index and Statistics Details for Specific Tables

This script reads the table names from the XML plan analysis JSON file,
then executes SQL queries to retrieve index and statistics details
only for those specific tables.
"""

import json
import re
import pyodbc
import logging
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def load_table_names(json_path):
    """Load table names from the XML plan analysis JSON file.

    Args:
        json_path: Path to the JSON file containing table names

    Returns:
        List of dictionaries with schema, table, and full_name keys

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
        KeyError: If JSON structure is unexpected
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Table names JSON file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate JSON structure
    if 'unique_table_names' not in data:
        raise KeyError("JSON file missing 'unique_table_names' key")

    # Extract unique table names and parse schema.table
    tables = []
    for full_name in data.get('unique_table_names', []):
        # Remove brackets and split schema.table
        clean_name = full_name.replace('[', '').replace(']', '')
        parts = clean_name.split('.')

        if len(parts) == 2:
            schema, table = parts
            # Skip temp tables (starting with #)
            if not table.startswith('#'):
                # Validate schema and table names contain only safe characters
                # Allow alphanumeric, underscore, and common SQL Server name characters
                if re.match(r'^[\w\-\.]+$', schema) and re.match(r'^[\w\-\.]+$', table):
                    tables.append({'schema': schema, 'table': table, 'full_name': clean_name})
                else:
                    raise ValueError(f"Invalid characters in table name: {clean_name}")

    return tables


def build_table_filter_clause(tables):
    """Build SQL WHERE clause to filter specific tables.

    Escapes single quotes in table and schema names to prevent SQL syntax errors.
    Uses parameterized approach where possible for better security.

    Args:
        tables: List of dictionaries with 'schema' and 'table' keys

    Returns:
        SQL WHERE clause string with properly escaped table/schema names

    Note:
        While this function escapes single quotes, the table names should already
        be validated by load_table_names() to contain only safe characters.
    """
    if not tables:
        return "1=1"

    conditions = []
    for table in tables:
        # Validate that schema and table are strings
        if not isinstance(table.get('schema'), str) or not isinstance(table.get('table'), str):
            raise ValueError(f"Invalid table structure: {table}")

        # Escape single quotes by doubling them (SQL standard)
        # Additional validation: ensure no suspicious patterns
        schema = table['schema'].replace("'", "''")
        table_name = table['table'].replace("'", "''")

        # Double-check for SQL injection patterns after escaping
        if '--' in schema or '--' in table_name or ';' in schema or ';' in table_name:
            raise ValueError(f"Suspicious SQL pattern detected in table name: {table['full_name']}")

        conditions.append(f"(s.name = '{schema}' AND o.name = '{table_name}')")

    return " OR ".join(conditions)


def execute_sql_query_with_filter(sql_file_path, connection_string, table_filter_clause, logger, batch_size=1000):
    """Execute SQL query from file with table filtering.

    This function also converts DATETIMEOFFSET columns to VARCHAR to avoid pyodbc compatibility issues.
    Applies table filtering to WHERE clause based on schema and table names.

    Args:
        sql_file_path: Path to the SQL file to execute
        connection_string: Database connection string
        table_filter_clause: SQL WHERE clause for filtering tables
        logger: Logger instance
        batch_size: Number of rows to fetch per batch (default: 1000)

    Returns:
        List of dictionaries containing query results

    Raises:
        FileNotFoundError: If SQL file doesn't exist
        ValueError: If batch_size is invalid
        pyodbc.Error: If database operation fails
    """
    # Validate inputs
    sql_file_path = Path(sql_file_path)
    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got: {batch_size}")

    # Read SQL query from file
    with open(sql_file_path, 'r', encoding='utf-8-sig') as f:
        sql_query = f.read()

    # Modify query to convert DATETIMEOFFSET columns to VARCHAR
    # Style 127 = ISO 8601 format with timezone
    # VARCHAR(33) = max length for ISO 8601 datetime with timezone
    datetime_conversions = [
        ('us.last_user_seek,', 'CONVERT(VARCHAR(33), us.last_user_seek, 127) AS last_user_seek,'),
        ('us.last_user_scan,', 'CONVERT(VARCHAR(33), us.last_user_scan, 127) AS last_user_scan,'),
        ('us.last_user_lookup,', 'CONVERT(VARCHAR(33), us.last_user_lookup, 127) AS last_user_lookup,'),
        ('us.last_user_update', 'CONVERT(VARCHAR(33), us.last_user_update, 127) AS last_user_update'),
        ('sp.last_updated,', 'CONVERT(VARCHAR(33), sp.last_updated, 127) AS last_updated,'),
    ]

    for old_str, new_str in datetime_conversions:
        sql_query = sql_query.replace(old_str, new_str)

    # Add table filter to WHERE clause
    # For Index Detail query (uses 's' and 'o' aliases)
    if "FROM sys.indexes i" in sql_query:
        if "WHERE o.type = 'U'" in sql_query:
            sql_query = sql_query.replace(
                "WHERE o.type = 'U'",
                f"WHERE o.type = 'U' AND ({table_filter_clause})"
            )
        else:
            logger.warning("Expected WHERE clause not found in Index Detail query")
    # For Statistics Detail query (uses 'sch' and 'obj' aliases)
    elif "FROM sys.stats st" in sql_query:
        # Replace s. with sch. and o. with obj. in the filter
        stats_filter = table_filter_clause.replace('s.name', 'sch.name').replace('o.name', 'obj.name')
        if "WHERE obj.type = 'U'" in sql_query:
            sql_query = sql_query.replace(
                "WHERE obj.type = 'U'",
                f"WHERE obj.type = 'U' AND ({stats_filter})"
            )
        else:
            logger.warning("Expected WHERE clause not found in Statistics Detail query")

    # Connect and execute using context managers
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            logger.info("  Executing SQL query...")
            cursor.execute(sql_query)

            # Get column names
            columns = [column[0] for column in cursor.description]

            # Fetch rows in batches
            results = []
            row_count = 0

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break

                for row in rows:
                    row_dict = {
                        columns[i]: value.isoformat() if isinstance(value, datetime) else value
                        for i, value in enumerate(row)
                    }
                    results.append(row_dict)

                row_count += len(rows)

            logger.info(f"  ✓ ({row_count} rows)")
            return results


def save_results_to_json(results, output_path, query_name, tables, logger):
    """Save query results to JSON file.

    Args:
        results: List of dictionaries containing query results
        output_path: Path where JSON file should be saved
        query_name: Name of the query being saved
        tables: List of table dictionaries with 'full_name' key
        logger: Logger instance
    """
    # Ensure output_path is a Path object
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "query_name": query_name,
        "extraction_timestamp": datetime.now().isoformat(),
        "filtered_tables": [t['full_name'] for t in tables],
        "record_count": len(results),
        "data": results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Total records: {len(results)}")


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_04')

    # Get logger instance
    logger = logging.getLogger(__name__)

    # Get active report settings
    active_report_key, report_settings = config.get_active_report_settings()

    # Get paths from config
    project_root = config.get_project_root()
    batch_size = config.get_sql_fetch_batch_size()

    # Build report-specific paths
    report_base_dir = project_root / report_settings['output']['base_dir']
    table_names_json = report_base_dir / report_settings['output']['table_names_json']

    # Define SQL scripts and their output files
    sql_scripts = [
        {
            "name": "Index Detail",
            "sql_file": project_root / report_settings['sql_files']['index_detail'],
            "output_file": report_base_dir / report_settings['output']['index_details_json']
        },
        {
            "name": "Statistics Detail",
            "sql_file": project_root / report_settings['sql_files']['statistics_detail'],
            "output_file": report_base_dir / report_settings['output']['statistics_details_json']
        }
    ]

    logger.info("=" * 70)
    logger.info(f"{report_settings['name']} - Index and Statistics Details")
    logger.info("=" * 70)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"Table names file: {table_names_json}")
    logger.info(f"Batch size: {batch_size}")

    try:
        # Load table names from JSON
        logger.info("Loading table names from XML plan analysis...")
        tables = load_table_names(table_names_json)
        logger.info(f"Found {len(tables)} tables to analyze (excluding temp tables):")
        for table in tables:
            logger.info(f"  - {table['full_name']}")

        if not tables:
            logger.warning("No tables found to analyze. Exiting.")
            return

        # Build table filter clause
        table_filter_clause = build_table_filter_clause(tables)

        # Get database connection
        logger.info("Loading database configuration...")
        logger.info(f"Server: {config.get_server()}")
        logger.info(f"Database: {config.get_database()}")

        # Build connection string
        connection_string = config.get_connection_string()

        # Execute each SQL script
        for script in sql_scripts:
            logger.info("-" * 70)
            logger.info(f"Processing: {script['name']}")
            logger.info(f"SQL file: {script['sql_file']}")

            try:
                results = execute_sql_query_with_filter(
                    script['sql_file'],
                    connection_string,
                    table_filter_clause,
                    logger,
                    batch_size
                )

                logger.info("  Saving results to JSON...")
                save_results_to_json(results, script['output_file'], script['name'], tables, logger)
                logger.info("  ✓ Success")

            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}", exc_info=True)

        logger.info("=" * 70)
        logger.info("Extraction completed!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

