"""
Script to retrieve all column names from the specified table in SQL Server
and update the configuration file with the discovered columns.
"""

import sys
import pyodbc
from config_loader import ConfigLoader


def connect_to_database(config, odbc_driver):
    """Establish connection to SQL Server database."""
    try:
        connection_string = (
            f"DRIVER={{{odbc_driver}}};"
            f"SERVER={config['servername']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']}"
        )
        conn = pyodbc.connect(connection_string)
        print(f"Successfully connected to database: {config['database']}")
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


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

    cursor = connection.cursor()
    try:
        cursor.execute(query, (table_name, schema))
        columns = [row.column_name for row in cursor.fetchall()]
    finally:
        cursor.close()

    return columns


def main():
    """Main execution function."""
    print("=" * 80)
    print("Database Column Population Script")
    print("=" * 80)

    # Load configuration using ConfigLoader
    config_loader = ConfigLoader()
    config = config_loader.get_database_config()
    odbc_driver = config_loader.get_odbc_driver()

    # Validate table name
    table_name = config.get('table', '')
    if not table_name:
        print("Error: Table name is not specified in the configuration.")
        print("Please enter a table name in the Configuration tab first.")
        sys.exit(1)

    # Initialize connection variable
    conn = None

    try:
        # Connect to database
        conn = connect_to_database(config, odbc_driver)

        # Parse table name to extract schema and table
        default_schema = config_loader.get_default_schema()
        schema, table_only = parse_table_name(table_name, default_schema)

        print(f"\nRetrieving columns for table: {table_name}")
        print(f"  Schema: {schema}")
        print(f"  Table: {table_only}")

        columns = get_table_columns(conn, table_only, schema)

        if not columns:
            print(f"\nWarning: No columns found for table '{table_only}' in schema '{schema}'")
            print("Please verify:")
            print("  1. The table name is correct")
            print("  2. The table exists in the database")
            print("  3. The schema is correct")
            print(f"     (You can specify schema as: schema.tablename, e.g., 'norm.MyTable')")
            sys.exit(1)

        print(f"\nFound {len(columns)} column(s):")
        for i, column in enumerate(columns, 1):
            print(f"  {i}. {column}")

        # Update configuration
        config['columns'] = columns
        config_loader.save_database_config(config)

        print("\n" + "=" * 80)
        print("Process completed successfully!")
        print("=" * 80)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        print(f"Error retrieving columns: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error updating configuration: {e}")
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()

