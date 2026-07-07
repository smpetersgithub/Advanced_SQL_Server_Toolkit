"""
Script to retrieve all column names from the specified table in SQL Server
and update the configuration file with the discovered columns.
"""

import logging
import sys
import pyodbc
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)


def parse_table_name(full_table_name, default_schema='dbo'):
    """
    Parse a table name that may include schema.

    Args:
        full_table_name: Table name, optionally schema-qualified (e.g., 'norm.MyTable' or 'MyTable')
        default_schema: Default schema to use if not specified

    Returns:
        Tuple of (schema, table_name)

    Raises:
        ValueError: If table name is empty or invalid format
    """
    if not full_table_name or not full_table_name.strip():
        raise ValueError("Table name cannot be empty")

    if '.' in full_table_name:
        parts = full_table_name.split('.', 1)
        schema = parts[0].strip()
        table = parts[1].strip()
        if not schema or not table:
            raise ValueError(f"Invalid table name format: {full_table_name}")
        return schema, table
    else:
        return default_schema, full_table_name.strip()


def get_table_columns(connection, table_name, schema='dbo'):
    """
    Retrieve all column names for a table from sys.columns.

    Args:
        connection: Active pyodbc connection
        table_name: Name of the table (without schema)
        schema: Schema name (default: 'dbo')

    Returns:
        List of column names in ordinal position order
    """
    query = """
        SELECT c.name AS column_name
        FROM sys.columns c
        INNER JOIN sys.tables t ON c.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name = ?
          AND s.name = ?
        ORDER BY c.column_id
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (table_name, schema))
        columns = [row.column_name for row in cursor.fetchall()]

    return columns


def main():
    """Main execution function."""
    print("=" * 80)
    print("Database Column Population Script")
    print("=" * 80)

    # Load configuration using ConfigLoader
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)
    log_file = config.setup_logging('00_populate_columns_from_database')
    db_config = config.get_database_config()

    # Validate table name
    table_name = db_config.get('table', '')
    if not table_name:
        logger.error("Table name is not specified in the configuration.")
        logger.error("Please enter a table name in the Configuration tab first.")
        sys.exit(1)

    try:
        # Connect to database
        connection_string = config.get_connection_string()
        with pyodbc.connect(connection_string, timeout=config.get_connection_timeout()) as conn:
            logger.info(f"Successfully connected to database: {db_config['database']}")

            # Parse table name to extract schema and table
            default_schema = config.get_default_schema()
            schema, table_only = parse_table_name(table_name, default_schema)

            logger.info(f"Retrieving columns for table: {table_name}")
            logger.info(f"  Schema: {schema}")
            logger.info(f"  Table: {table_only}")

            columns = get_table_columns(conn, table_only, schema)

            if not columns:
                logger.warning(f"No columns found for table '{table_only}' in schema '{schema}'")
                logger.warning("Please verify:")
                logger.warning("  1. The table name is correct")
                logger.warning("  2. The table exists in the database")
                logger.warning("  3. The schema is correct")
                logger.warning("  (You can specify schema as: schema.tablename, e.g., 'norm.MyTable')")
                sys.exit(1)

            logger.info(f"Found {len(columns)} column(s):")
            for i, column in enumerate(columns, 1):
                logger.info(f"  {i}. {column}")

            # Update configuration
            db_config['columns'] = columns
            config.save_database_config(db_config)

        logger.info("Database connection closed.")
        logger.info("=" * 80)
        logger.info("Process completed successfully!")
        logger.info("=" * 80)

    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        logger.error(f"Error retrieving columns: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error updating configuration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
