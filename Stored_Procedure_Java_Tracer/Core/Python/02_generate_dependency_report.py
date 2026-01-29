import json
import pyodbc
import os
import sys
import configparser
import logging
from datetime import datetime

def load_database_config(config_path):
    """Load database configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def load_stored_procedures(input_file):
    """Load stored procedure names from input file."""
    with open(input_file, 'r') as f:
        # Read lines and strip whitespace, filter out empty lines
        procedures = [line.strip() for line in f if line.strip()]
    return procedures

def load_sql_script(sql_file):
    """Load SQL script from file."""
    with open(sql_file, 'r', encoding='utf-8-sig') as f:
        return f.read()

def execute_sql_for_procedure(connection, sql_script, procedure_name):
    """Execute SQL script with the procedure name as a variable."""
    try:
        # Replace the $(object_name) variable with the actual procedure name
        sql_to_execute = sql_script.replace("'$(object_name)'", f"'{procedure_name}'")

        cursor = connection.cursor()

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

        cursor.close()
        return {
            'procedure': procedure_name,
            'status': 'success',
            'results': results
        }
    except Exception as e:
        return {
            'procedure': procedure_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    # Load configuration
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)

    # Get configuration values
    base_dir = config.get('Paths', 'project_base_dir')
    output_dir = config.get('Paths', 'output_dir')

    # Define file paths
    config_file = os.path.join(base_dir, config.get('Files', 'database_config'))
    input_file = os.path.join(base_dir, config.get('Files', 'stored_procedures_input'))
    sql_file = os.path.join(base_dir, config.get('Files', 'dependency_sql_script'))
    output_file = os.path.join(output_dir, config.get('Files', 'object_dependency_list_json'))
    odbc_driver = config.get('Database', 'odbc_driver')
    log_dir = config.get('Paths', 'log_dir')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Setup logging
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'log_02_generate_dependency_report_{timestamp}.log'
    log_filepath = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Load configuration
    logging.info("Loading database configuration...")
    db_config = load_database_config(config_file)

    # Load stored procedures
    logging.info("Loading stored procedures...")
    procedures = load_stored_procedures(input_file)
    logging.info(f"Found {len(procedures)} stored procedures to process")

    # Load SQL script
    logging.info("Loading SQL script...")
    sql_script = load_sql_script(sql_file)

    # Connect to database
    logging.info("Connecting to database...")
    connection_string = (
        f"DRIVER={{{odbc_driver}}};"
        f"SERVER={db_config['server']};"
        f"UID={db_config['username']};"
        f"PWD={db_config['password']}"
    )
    
    try:
        connection = pyodbc.connect(connection_string)
        logging.info("Connected successfully!")

        # Process each stored procedure
        all_results = []
        for i, procedure in enumerate(procedures, 1):
            logging.info(f"Processing {i}/{len(procedures)}: {procedure}")
            result = execute_sql_for_procedure(connection, sql_script, procedure)
            all_results.append(result)

        # Close connection
        connection.close()

        # Write results to JSON file
        logging.info(f"Writing results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, default=str)

        logging.info("Processing complete!")
        logging.info(f"Results saved to: {output_file}")
        logging.info(f"Log file: {log_filepath}")

    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

