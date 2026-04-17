"""
Extract Top Resource Consuming Queries from SQL Server Query Store

This script connects to SQL Server, executes a query to retrieve the top N
resource-consuming queries from the Query Store, and saves the results as JSON.
"""

import json
import re
import pyodbc
import logging
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def execute_sql_query(sql_file_path, connection_string, logger, top_n_queries=10):
    """Execute SQL query from file and return results.

    Args:
        sql_file_path: Path to the SQL file to execute
        connection_string: Database connection string
        logger: Logger instance
        top_n_queries: Number of top queries to return (default: 10)

    Raises:
        FileNotFoundError: If SQL file doesn't exist
        ValueError: If top_n_queries is not a positive integer
        pyodbc.Error: If database connection or query execution fails
    """
    # Validate inputs
    sql_file_path = Path(sql_file_path)
    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    if not isinstance(top_n_queries, int) or top_n_queries <= 0:
        raise ValueError(f"top_n_queries must be a positive integer, got: {top_n_queries}")

    # Read SQL query from file (utf-8-sig automatically strips BOM if present)
    with open(sql_file_path, 'r', encoding='utf-8-sig') as f:
        sql_query = f.read()

    # Replace the default @top_n_queries value with the value from config
    # Use regex for more flexible matching (handles variations in whitespace)
    original_query = sql_query
    sql_query = re.sub(
        r'DECLARE\s+@top_n_queries\s+INT\s*=\s*\d+\s*;',
        f'DECLARE @top_n_queries INT = {top_n_queries};',
        sql_query,
        flags=re.IGNORECASE
    )

    # Verify replacement occurred
    if sql_query == original_query:
        logger.warning("Failed to replace @top_n_queries parameter - SQL file may use different format")

    # Modify query to convert DATETIMEOFFSET columns to VARCHAR to avoid pyodbc issues
    # Style 127 = ISO 8601 format with timezone (YYYY-MM-DDTHH:MM:SS.mmmZ)
    # VARCHAR(33) = max length for ISO 8601 datetime with timezone
    sql_query = sql_query.replace(
        'r.first_execution_time,',
        'CONVERT(VARCHAR(33), r.first_execution_time, 127) AS first_execution_time,'
    )
    sql_query = sql_query.replace(
        'r.last_execution_time',
        'CONVERT(VARCHAR(33), r.last_execution_time, 127) AS last_execution_time'
    )

    # Connect and execute using context managers for proper resource cleanup
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            # Show connection info
            cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName")
            conn_info = cursor.fetchone()
            logger.info(f"Connected to: {conn_info[0]}, Database: {conn_info[1]}")

            # Log the parameter value
            logger.info(f"Using @top_n_queries parameter: {top_n_queries}")

            # Execute the main query (with the modified DECLARE statement)
            cursor.execute(sql_query)

            # Get column names
            columns = [column[0] for column in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            # Note: datetime conversion is kept for safety, though SQL conversion should handle most cases
            results = []
            for row in rows:
                row_dict = {
                    columns[i]: value.isoformat() if isinstance(value, datetime) else value
                    for i, value in enumerate(row)
                }
                results.append(row_dict)

            return results


def save_results_to_json(results, output_path, logger):
    """Save query results to JSON file.

    Args:
        results: List of dictionaries containing query results
        output_path: Path where JSON file should be saved
        logger: Logger instance
    """
    # Ensure output_path is a Path object
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare output data with metadata
    output_data = {
        "extraction_timestamp": datetime.now().isoformat(),
        "record_count": len(results),
        "data": results
    }

    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Total records: {len(results)}")


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_01')

    # Get logger instance
    logger = logging.getLogger(__name__)

    # Get active report settings
    active_report_key, report_settings = config.get_active_report_settings()

    # Get paths from config
    project_root = config.get_project_root()
    sql_file_path = project_root / report_settings['sql_files']['main_query']

    # Build output paths
    report_base_dir = project_root / report_settings['output']['base_dir']
    output_path = report_base_dir / report_settings['output']['main_results_json']

    # Get top_n_queries parameter from report settings (default to 10 if not specified)
    top_n_queries = report_settings.get('processing', {}).get('top_n_queries', 10)

    logger.info("=" * 70)
    logger.info(f"SQL Server Query Store - {report_settings['name']}")
    logger.info("=" * 70)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"SQL file: {sql_file_path}")
    logger.info(f"Output file: {output_path}")
    logger.info(f"Top N Queries: {top_n_queries}")

    try:
        # Get database connection info
        logger.info("Loading database configuration...")
        logger.info(f"Server: {config.get_server()}")
        logger.info(f"Database: {config.get_database()}")

        # Build connection string
        connection_string = config.get_connection_string()

        # Execute SQL query
        logger.info("Connecting to database and executing SQL query...")
        results = execute_sql_query(sql_file_path, connection_string, logger, top_n_queries)

        # Save results to JSON
        logger.info("Saving results to JSON...")
        save_results_to_json(results, output_path, logger)

        logger.info("Extraction completed successfully!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

