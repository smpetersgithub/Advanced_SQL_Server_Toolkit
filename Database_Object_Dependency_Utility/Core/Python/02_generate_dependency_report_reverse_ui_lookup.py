"""
Script to generate a reverse dependency report by looking up stored procedures
against the complete UI mapping to identify which UI components call each procedure.
"""

import json
import pyodbc
import os
import sys
import logging
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

def normalize_object_name(name, default_database, default_schema='dbo'):
    """Ensure object name is fully qualified as database.schema.object."""
    parts = [p.strip() for p in name.split('.')]
    if len(parts) == 1:
        return f"{default_database}.{default_schema}.{parts[0]}"
    elif len(parts) == 2:
        return f"{default_database}.{parts[0]}.{parts[1]}"
    return name  # Already 3-part


def load_stored_procedures(input_file):
    """Load stored procedure names from input file."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read lines and strip whitespace, filter out empty lines
            procedures = [line.strip() for line in f if line.strip()]
        return procedures
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file}")

def load_sql_script(sql_file):
    """Load SQL script from file."""
    try:
        with open(sql_file, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"SQL script file not found: {sql_file}")

def execute_sql_for_procedure(connection, sql_script, procedure_name):
    """Execute SQL script with the procedure name as a variable."""
    try:
        # Replace the $(object_name) variable with the actual procedure name
        sql_to_execute = sql_script.replace("'$(object_name)'", f"'{procedure_name}'")

        with connection.cursor() as cursor:
            # Execute the SQL script
            cursor.execute(sql_to_execute)

            # Move through any result sets until we get to the final one
            results = []
            while True:
                if cursor.description:  # Check if there are results to fetch
                    columns = [column[0] for column in cursor.description]
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, value in enumerate(row):
                            # Convert non-serializable types to strings
                            if isinstance(value, (bytes, bytearray)):
                                row_dict[columns[i]] = str(value)
                            else:
                                row_dict[columns[i]] = value
                        results.append(row_dict)

                # Try to move to the next result set
                if not cursor.nextset():
                    break

        return {
            'procedure': procedure_name,
            'status': 'success',
            'results': results
        }
    except pyodbc.Error as e:
        logger.error(f"Database error processing {procedure_name}: {e}", exc_info=True)
        return {
            'procedure': procedure_name,
            'status': 'error',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error processing {procedure_name}: {e}", exc_info=True)
        return {
            'procedure': procedure_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    # Load configuration
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)

    # Get configuration values
    base_dir = config.get_project_base_dir()
    output_dir = config.get_output_dir()

    # Define file paths
    input_file = os.path.join(base_dir, config.get_database_object_input_file())
    sql_file = os.path.join(base_dir, config.get_dependency_sql_script())
    output_file = os.path.join(output_dir, config.get_object_dependency_list_json())

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Setup logging
    log_file = config.setup_logging('02_generate_dependency_report_reverse_ui_lookup')

    # Load stored procedures
    logger.info("Loading stored procedures...")
    procedures = load_stored_procedures(input_file)
    procedures = [normalize_object_name(p, config.get_database_name()) for p in procedures]
    logger.info(f"Found {len(procedures)} stored procedures to process")
    for p in procedures:
        logger.info(f"  Object: {p}")

    # Validate we have procedures to process
    if not procedures:
        logger.warning("No stored procedures found in input file")
        logger.info("Exiting - nothing to process")
        return

    # Load SQL script
    logger.info("Loading SQL script...")
    sql_script = load_sql_script(sql_file)

    # Connect to database
    logger.info("Connecting to database...")
    connection_string = config.get_connection_string()

    try:
        with pyodbc.connect(connection_string, timeout=config.get_connection_timeout()) as connection:
            logger.info("Connected successfully!")

            # Process each stored procedure
            all_results = []
            total = len(procedures)
            for i, procedure in enumerate(procedures, 1):
                percentage = (i / total) * 100
                logger.info(f"Processing {i}/{total} ({percentage:.1f}%): {procedure}")
                result = execute_sql_for_procedure(connection, sql_script, procedure)
                all_results.append(result)

        logger.info("Database connection closed")

        # Write results to JSON file
        logger.info(f"Writing results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, default=str)

        logger.info("Processing complete!")
        logger.info(f"Results saved to: {output_file}")
        logger.info(f"Log file: {log_file}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
