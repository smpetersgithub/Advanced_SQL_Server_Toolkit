"""
Lookup Query Text by Query ID from SQL Server Query Store

This script retrieves and formats the SQL query text for a specific query_id
from the Query Store and saves it to a text file.
"""

import pyodbc
import logging
import sys
import sqlparse
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def format_sql_query(query_text):
    """Format SQL query for better readability using sqlparse.

    Args:
        query_text: Raw SQL query text to format

    Returns:
        Formatted SQL query string
    """
    if not query_text:
        return ""

    try:
        # Use sqlparse to format the SQL
        formatted = sqlparse.format(
            query_text,
            reindent=True,
            keyword_case='upper',
            indent_width=4,
            wrap_after=80
        )
        return formatted
    except Exception as e:
        # If formatting fails, return original
        logging.warning(f"Failed to format SQL: {e}")
        return query_text


def lookup_query_by_id(query_id, connection_string, logger):
    """Lookup query text by query_id from Query Store.

    Args:
        query_id: Integer query ID to lookup
        connection_string: Database connection string
        logger: Logger instance

    Returns:
        Dictionary with query details, or None if not found

    Raises:
        ValueError: If query_id is not a positive integer
        pyodbc.Error: If database operation fails
    """
    # Validate query_id
    if not isinstance(query_id, int) or query_id <= 0:
        raise ValueError(f"query_id must be a positive integer, got: {query_id}")

    # Use parameterized query to prevent SQL injection
    sql_query = """
    SELECT
        q.query_id,
        qt.query_sql_text,
        q.object_id,
        OBJECT_NAME(q.object_id) AS object_name
    FROM sys.query_store_query AS q
    INNER JOIN sys.query_store_query_text AS qt ON q.query_text_id = qt.query_text_id
    WHERE q.query_id = ?
    """

    # Use context managers for proper resource cleanup
    try:
        logger.info(f"Connecting to database to lookup query_id: {query_id}")
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                logger.info(f"Executing query lookup for query_id: {query_id}")
                cursor.execute(sql_query, query_id)
                row = cursor.fetchone()

                if row:
                    result = {
                        'query_id': row.query_id,
                        'query_sql_text': row.query_sql_text,
                        'object_id': row.object_id,
                        'object_name': row.object_name if row.object_name else 'Ad-hoc query'
                    }
                    logger.info(f"Found query_id {query_id}: {result['object_name']}")
                    return result
                else:
                    logger.warning(f"Query ID {query_id} not found in Query Store")
                    return None

    except pyodbc.Error as e:
        logger.error(f"Database error looking up query: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error looking up query: {e}")
        raise


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_06')

    # Get logger instance
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("QUERY ID LOOKUP SCRIPT")
    logger.info("=" * 80)

    # Setup paths
    project_root = config.get_project_root()
    output_dir = project_root / 'Output' / 'QueryID_Lookup'

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get query_id from command line argument
    if len(sys.argv) < 2:
        logger.error("Usage: python 06_lookup_query_by_id.py <query_id>")
        sys.exit(1)

    try:
        query_id = int(sys.argv[1])
    except ValueError:
        logger.error(f"Invalid query_id: {sys.argv[1]}. Must be an integer.")
        sys.exit(1)

    logger.info(f"Looking up query_id: {query_id}")

    # Get connection string from config
    connection_string = config.get_connection_string()
    logger.info(f"Connecting to: {config.get_server()} / {config.get_database()}")

    # Lookup query
    result = lookup_query_by_id(query_id, connection_string, logger)

    if result is None:
        logger.error(f"Query ID {query_id} not found")
        sys.exit(1)

    # Format the SQL query
    logger.info("Formatting SQL query...")
    formatted_query = format_sql_query(result['query_sql_text'])

    # Save to file (no timestamp - always overwrite)
    output_filename = f"query_{query_id}.sql"
    output_path = output_dir / output_filename

    logger.info(f"Saving formatted query to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"-- Query ID: {result['query_id']}\n")
        f.write(f"-- Object: {result['object_name']}\n")
        f.write(f"-- Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- " + "=" * 76 + "\n\n")
        f.write(formatted_query)
        f.write("\n")

    logger.info("=" * 80)
    logger.info("QUERY LOOKUP COMPLETE")
    logger.info(f"Query ID: {query_id}")
    logger.info(f"Object: {result['object_name']}")
    logger.info(f"Output file: {output_filename}")
    logger.info(f"Location: {output_dir}")
    logger.info("=" * 80)

    # Return the output path for the UI to use (use absolute path string)
    print(f"OUTPUT_FILE:{str(output_path)}")


if __name__ == "__main__":
    main()
