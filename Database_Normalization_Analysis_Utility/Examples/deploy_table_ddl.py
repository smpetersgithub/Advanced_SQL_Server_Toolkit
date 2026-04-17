"""
================================================================================
Deploy Table DDL Script
================================================================================

PURPOSE:
This script deploys all SQL example tables to the database specified in the
configuration file. It automatically discovers and executes all .sql files
in the Examples directory.

USAGE:
    python deploy_table_ddl.py

REQUIREMENTS:
    - pyodbc package
    - Valid database configuration in Config/database-config.json
    - SQL Server with ODBC Driver 17

================================================================================
"""

import sys
import pyodbc
from pathlib import Path


def load_database_config():
    """Load database configuration from the config file."""
    import json

    # Get project root (go up from Examples to project root)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "Config" / "database-config.json"

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from: {config_path}")
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def get_connection_string(config):
    """Build SQL Server connection string from configuration."""
    server = config['servername']
    database = config['database']
    username = config['username']
    password = config['password']

    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    return connection_string


def find_sql_files():
    """Find all .sql files in the Examples directory."""
    script_dir = Path(__file__).parent
    sql_files = sorted(script_dir.glob("*.sql"))
    return sql_files


def execute_sql_file(connection, sql_file):
    """Execute a SQL file against the database."""
    print(f"\n{'=' * 80}")
    print(f"Executing: {sql_file.name}")
    print(f"{'=' * 80}")
    
    try:
        # Read the SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by GO statements (SQL Server batch separator)
        batches = sql_content.split('\nGO\n')
        
        cursor = connection.cursor()
        batch_count = 0
        
        for batch in batches:
            batch = batch.strip()
            if not batch or batch.startswith('/*') and batch.endswith('*/'):
                continue
            
            try:
                cursor.execute(batch)
                connection.commit()
                batch_count += 1
            except pyodbc.Error as e:
                print(f"  ⚠️  Warning executing batch: {e}")
                # Continue with next batch even if one fails
                continue
        
        cursor.close()
        print(f"✅ Successfully executed {batch_count} batch(es) from {sql_file.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error executing {sql_file.name}: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 80)
    print("Deploy Table DDL Script")
    print("=" * 80)
    print()
    
    # Load configuration
    config = load_database_config()
    print(f"Target Server: {config['servername']}")
    print(f"Target Database: {config['database']}")
    print()
    
    # Find SQL files
    sql_files = find_sql_files()
    
    if not sql_files:
        print("No SQL files found in the Examples directory.")
        sys.exit(0)
    
    print(f"Found {len(sql_files)} SQL file(s) to execute:")
    for sql_file in sql_files:
        print(f"  - {sql_file.name}")
    print()
    
    # Connect to database
    connection_string = get_connection_string(config)
    
    try:
        print("Connecting to database...")
        connection = pyodbc.connect(connection_string)
        print("✅ Connected successfully!")
        
        # Execute each SQL file
        success_count = 0
        fail_count = 0
        
        for sql_file in sql_files:
            if execute_sql_file(connection, sql_file):
                success_count += 1
            else:
                fail_count += 1
        
        # Close connection
        connection.close()
        
        # Summary
        print()
        print("=" * 80)
        print("Deployment Summary")
        print("=" * 80)
        print(f"Total files: {len(sql_files)}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print("=" * 80)
        
    except pyodbc.Error as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

