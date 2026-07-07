"""
Script to read database configuration, connect to SQL Server,
and populate primary key and unique key information from the database schema.
"""

import logging
import pyodbc
import sys
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





def get_primary_key(conn, table_name, schema='dbo'):
    """Query the database to get the primary key column(s) for the specified table."""
    query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = ?
        AND TABLE_SCHEMA = ?
        ORDER BY ORDINAL_POSITION
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (table_name, schema))
        pk_columns = [row.COLUMN_NAME for row in cursor.fetchall()]

    if len(pk_columns) == 1:
        return pk_columns[0]
    elif len(pk_columns) > 1:
        return pk_columns
    else:
        return ""


def get_unique_keys(conn, table_name, schema='dbo'):
    """Query the database to get unique key constraints and unique indexes."""
    # Query to get both UNIQUE CONSTRAINTS and UNIQUE INDEXES
    query = """
        SELECT
            i.name AS constraint_name,
            c.name AS column_name,
            ic.key_ordinal
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic
            ON i.object_id = ic.object_id
            AND i.index_id = ic.index_id
        INNER JOIN sys.columns c
            ON ic.object_id = c.object_id
            AND ic.column_id = c.column_id
        INNER JOIN sys.tables t
            ON i.object_id = t.object_id
        INNER JOIN sys.schemas s
            ON t.schema_id = s.schema_id
        WHERE i.is_unique = 1
        AND i.is_primary_key = 0
        AND t.name = ?
        AND s.name = ?
        ORDER BY i.name, ic.key_ordinal
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (table_name, schema))

        unique_constraints = {}
        for row in cursor.fetchall():
            constraint_name = row.constraint_name
            column_name = row.column_name
            if constraint_name not in unique_constraints:
                unique_constraints[constraint_name] = []
            unique_constraints[constraint_name].append(column_name)

    # Flatten to a list of columns (or list of lists for composite keys)
    unique_keys = []
    for columns in unique_constraints.values():
        if len(columns) == 1:
            unique_keys.append(columns[0])
        else:
            unique_keys.append(columns)

    return unique_keys if unique_keys else []


def main():
    """Main function to orchestrate the key population process."""
    print("=" * 80)
    print("Database Key Population Script")
    print("=" * 80)

    # Load configuration using ConfigLoader
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)
    log_file = config.setup_logging('01_populate_keys_from_database')
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
            full_table_name = db_config['table']
            default_schema = config.get_default_schema()
            schema, table_name = parse_table_name(full_table_name, default_schema)

            logger.info(f"Querying keys for table: {full_table_name}")
            logger.info(f"  Schema: {schema}")
            logger.info(f"  Table: {table_name}")

            # Get primary key
            logger.info("Querying primary key...")
            primary_key = get_primary_key(conn, table_name, schema)
            db_config['primarykey'] = primary_key
            logger.info(f"Primary Key: {primary_key}")

            # Get unique keys
            logger.info("Querying unique keys...")
            unique_keys = get_unique_keys(conn, table_name, schema)
            db_config['uniquekey'] = unique_keys
            logger.info(f"Unique Keys: {unique_keys}")

            # Save updated configuration
            logger.info("=" * 80)
            config.save_database_config(db_config)

        logger.info("Database connection closed.")
        logger.info("=" * 80)
        logger.info("Process completed successfully!")

    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        logger.error(f"Error querying database: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error updating configuration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
