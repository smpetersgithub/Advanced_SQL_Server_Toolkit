"""
Script to analyze functional dependencies including composite column combinations.
Tests all combinations: single columns, pairs, triples, etc. as determinants.
"""

import json
import pyodbc
import sys
from itertools import combinations
from datetime import datetime
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





def check_composite_functional_dependency(conn, schema, table_name, determinant_cols, dependent_col):
    """
    Check if there is a functional dependency violation for composite columns.
    determinant_cols: list of column names (can be single or multiple)
    dependent_col: single column name

    Returns True if there is NO functional dependency (violation found).
    Returns False if there IS a functional dependency (no violation).
    """
    # Build GROUP BY clause with all determinant columns
    group_by_cols = ', '.join([f'[{col}]' for col in determinant_cols])

    # Build WHERE clause to exclude NULLs in determinant columns
    where_conditions = ' AND '.join([f'[{col}] IS NOT NULL' for col in determinant_cols])

    # Modified SQL query for composite keys
    query = f"""
        SELECT TOP 1 {group_by_cols}
        FROM [{schema}].[{table_name}]
        WHERE {where_conditions}
        GROUP BY {group_by_cols}
        HAVING COUNT(DISTINCT [{dependent_col}]) > 1;
    """

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchone()

        # If result exists, there's a violation (no functional dependency)
        return result is not None
    except pyodbc.Error as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        cursor.close()


def generate_all_combinations(columns, max_combination_size=None):
    """
    Generate all combinations of columns from size 1 to max_combination_size.
    If max_combination_size is None, use len(columns) - 1 as max.
    """
    if max_combination_size is None:
        max_combination_size = len(columns) - 1
    
    all_combos = []
    for size in range(1, min(max_combination_size, len(columns)) + 1):
        for combo in combinations(columns, size):
            all_combos.append(list(combo))
    
    return all_combos


def analyze_all_composite_combinations(conn, config, max_determinant_size, progress_interval, default_schema):
    """
    Analyze all combinations including composite functional dependencies.
    max_determinant_size: maximum number of columns in determinant
    progress_interval: how often to show progress updates
    default_schema: default database schema

    Raises:
        ValueError: If table name or columns are invalid
    """
    full_table_name = config['table']
    columns = config['columns']

    # Validate columns list
    if not columns or not isinstance(columns, list):
        raise ValueError("Columns list is empty or invalid")

    if len(columns) < 2:
        raise ValueError(f"Need at least 2 columns for functional dependency analysis, found {len(columns)}")

    # Parse table name to extract schema and table
    schema, table_name = parse_table_name(full_table_name, default_schema)

    print(f"\nAnalyzing table: [{schema}].[{table_name}]")
    print(f"Columns to analyze: {columns}")
    print(f"Max determinant size: {max_determinant_size}")
    
    # Generate all determinant combinations
    determinant_combos = generate_all_combinations(columns, max_determinant_size)
    
    total_checks = 0
    for det_combo in determinant_combos:
        for dep_col in columns:
            # Include trivial dependencies (where dependent is in determinant)
            # They will be classified as TRIVIAL by the classifier
            total_checks += 1
    
    print(f"Total combinations to check: {total_checks}")
    print("=" * 80)
    
    results = []
    checks_done = 0
    violations_found = 0
    dependencies_found = 0
    
    # Check all combinations
    for det_combo in determinant_combos:
        for dep_col in columns:
            checks_done += 1
            determinant_str = ', '.join(det_combo)

            # Progress indicator
            if checks_done % progress_interval == 0 or checks_done == total_checks:
                print(f"Progress: {checks_done}/{total_checks} ({100*checks_done//total_checks}%)")

            print(f"  Checking: [{determinant_str}] -> [{dep_col}]... ", end="")

            # Check if this is a trivial dependency (dependent is in determinant)
            if dep_col in det_combo:
                print("TRIVIAL (always true)")
                status = "functional_dependency_exists"
                dependencies_found += 1
            else:
                has_violation = check_composite_functional_dependency(
                    conn, schema, table_name, det_combo, dep_col
                )

                if has_violation is None:
                    print("ERROR")
                    status = "error"
                elif has_violation:
                    print("VIOLATION (No FD)")
                    status = "no_functional_dependency"
                    violations_found += 1
                else:
                    print("OK (FD exists)")
                    status = "functional_dependency_exists"
                    dependencies_found += 1

            result = {
                "determinant": det_combo if len(det_combo) > 1 else det_combo[0],
                "determinant_size": len(det_combo),
                "dependent": dep_col,
                "status": status,
                "description": f"[{determinant_str}] -> [{dep_col}]"
            }

            results.append(result)

    print("=" * 80)
    print(f"\nAnalysis Summary:")
    print(f"  Total checks: {checks_done}")
    print(f"  Functional dependencies found: {dependencies_found}")
    print(f"  Violations found (no FD): {violations_found}")

    return results


def save_results(results, config, output_path):
    """Save the analysis results to a JSON file."""
    from pathlib import Path

    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Separate results by determinant size
    single_column_fds = [r for r in results if r['determinant_size'] == 1]
    composite_fds = [r for r in results if r['determinant_size'] > 1]

    output_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "database": config['database'],
        "table": config['table'],
        "primarykey": config.get('primarykey', ''),
        "uniquekey": config.get('uniquekey', []),
        "columns_analyzed": config['columns'],
        "total_combinations_checked": len(results),
        "single_column_dependencies": [r for r in single_column_fds if r['status'] == 'functional_dependency_exists'],
        "composite_dependencies": [r for r in composite_fds if r['status'] == 'functional_dependency_exists'],
        "functional_dependencies": [r for r in results if r['status'] == 'functional_dependency_exists'],
        "violations": [r for r in results if r['status'] == 'no_functional_dependency'],
        "errors": [r for r in results if r['status'] == 'error'],
        "all_results": results
    }

    try:
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to: {output_path}")
    except Exception as e:
        print(f"Error saving results file: {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate the functional dependency analysis."""
    print("=" * 80)
    print("Composite Functional Dependency Analysis")
    print("=" * 80)

    # Load configuration using ConfigLoader
    config_loader = ConfigLoader()
    config = config_loader.get_database_config()
    odbc_driver = config_loader.get_odbc_driver()
    max_determinant_size = config_loader.get_max_determinant_size()
    progress_interval = config_loader.get_progress_update_interval()
    default_schema = config_loader.get_default_schema()
    output_path = config_loader.get_functional_dependencies_path()

    # Validate table name
    table_name = config.get('table', '')
    if not table_name:
        print("Error: Table name is not specified in the configuration.")
        print("Please enter a table name in the Configuration tab first.")
        sys.exit(1)

    # Validate columns
    columns = config.get('columns', [])
    if not columns:
        print("Error: Columns are not specified in the configuration.")
        print("Please run the 'Populate Columns' script first.")
        sys.exit(1)

    # Initialize connection variable
    conn = None

    try:
        # Connect to database
        conn = connect_to_database(config, odbc_driver)

        # Analyze all column combinations
        results = analyze_all_composite_combinations(
            conn, config, max_determinant_size, progress_interval, default_schema
        )

        # Save results
        save_results(results, config, output_path)

        print("=" * 80)
        print("Analysis completed successfully!")
        print("=" * 80)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        print("=" * 80)
        print(f"ERROR: Database error during analysis: {e}")
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print("=" * 80)
        print(f"ERROR: Analysis failed: {e}")
        print("=" * 80)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()
