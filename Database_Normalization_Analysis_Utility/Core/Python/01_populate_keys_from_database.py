"""
Script to read database configuration, connect to SQL Server,
and populate primary key and unique key information from the database schema.
"""

import pyodbc
import sys
from config_loader import ConfigLoader


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
    cursor = conn.cursor()
    try:
        cursor.execute(query, (table_name, schema))
        pk_columns = [row.COLUMN_NAME for row in cursor.fetchall()]
    finally:
        cursor.close()

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
    cursor = conn.cursor()
    try:
        cursor.execute(query, (table_name, schema))

        unique_constraints = {}
        for row in cursor.fetchall():
            constraint_name = row.constraint_name
            column_name = row.column_name
            if constraint_name not in unique_constraints:
                unique_constraints[constraint_name] = []
            unique_constraints[constraint_name].append(column_name)
    finally:
        cursor.close()

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
        full_table_name = config['table']
        default_schema = config_loader.get_default_schema()
        schema, table_name = parse_table_name(full_table_name, default_schema)

        print(f"\nQuerying keys for table: {full_table_name}")
        print(f"  Schema: {schema}")
        print(f"  Table: {table_name}")

        # Get primary key
        print(f"\nQuerying primary key...")
        primary_key = get_primary_key(conn, table_name, schema)
        config['primarykey'] = primary_key
        print(f"Primary Key: {primary_key}")

        # Get unique keys
        print(f"\nQuerying unique keys...")
        unique_keys = get_unique_keys(conn, table_name, schema)
        config['uniquekey'] = unique_keys
        print(f"Unique Keys: {unique_keys}")

        # Save updated configuration
        print("\n" + "=" * 80)
        config_loader.save_database_config(config)
        print("=" * 80)
        print("Process completed successfully!")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        print(f"Error querying database: {e}")
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
