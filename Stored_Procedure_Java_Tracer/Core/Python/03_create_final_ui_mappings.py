"""
Script to create final UI mappings by searching for referencing objects from Dependency_List.json
in the Complete_StoredProc_to_UI_Mapping.csv file.

This script:
1. Reads Dependency_List.json and extracts all referencing_object values
2. Searches for these stored procedures in Complete_StoredProc_to_UI_Mapping.csv
3. Copies matching rows to UI_Mappings_Final.csv
"""

import json
import csv
import os
import configparser
import logging
from datetime import datetime

def extract_referencing_objects(json_file):
    """Extract all referencing_object values from Dependency_List.json."""
    referencing_objects = set()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        if item.get('status') == 'success' and 'results' in item:
            for result in item['results']:
                ref_obj = result.get('referencing_object', '').strip()
                if ref_obj:
                    referencing_objects.add(ref_obj)
    
    return sorted(list(referencing_objects))

def search_and_copy_mappings(csv_input, referencing_objects, csv_output):
    """Search for referencing objects in CSV and copy matching rows to output file."""
    matching_rows = []
    found_procedures = set()

    # Read the input CSV file
    logging.info(f"Reading {csv_input}...")
    with open(csv_input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
        fieldnames = reader.fieldnames

    logging.info(f"Searching for {len(referencing_objects)} stored procedures...")

    # Search for each referencing object
    for ref_obj in referencing_objects:
        for row in csv_data:
            stored_proc = row.get('Stored_Procedure', '').strip()
            # Case-insensitive comparison
            if ref_obj.lower() == stored_proc.lower():
                matching_rows.append(row.copy())
                found_procedures.add(ref_obj)

    # Write matching rows to output CSV
    logging.info(f"Writing {len(matching_rows)} matching rows to {csv_output}...")
    with open(csv_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in matching_rows:
            writer.writerow(row)

    # Calculate not found
    not_found = set(referencing_objects) - found_procedures

    return len(matching_rows), len(found_procedures), sorted(list(not_found))

def main():
    # Load configuration
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)

    # Get configuration values
    output_dir = config.get('Paths', 'output_dir')

    # Define file paths
    json_file = os.path.join(output_dir, config.get('Files', 'object_dependency_list_json'))
    csv_input = os.path.join(output_dir, config.get('Files', 'complete_mapping_csv'))
    csv_output = os.path.join(output_dir, config.get('Files', 'final_ui_mappings_csv'))
    log_dir = config.get('Paths', 'log_dir')

    # Setup logging
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'log_03_create_final_ui_mappings_{timestamp}.log'
    log_filepath = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info("="*60)
    logging.info("Creating Final UI Mappings")
    logging.info("="*60)
    
    # Extract referencing objects from JSON
    logging.info(f"\nReading {json_file}...")
    referencing_objects = extract_referencing_objects(json_file)
    logging.info(f"Found {len(referencing_objects)} unique referencing objects")
    
    # Search and copy matching rows
    total_rows, found_count, not_found = search_and_copy_mappings(
        csv_input, referencing_objects, csv_output
    )
    
    # Print summary
    logging.info("\n" + "="*60)
    logging.info("Summary:")
    logging.info("="*60)
    logging.info(f"Total referencing objects searched: {len(referencing_objects)}")
    logging.info(f"Stored procedures found in mapping: {found_count}")
    logging.info(f"Total matching rows copied: {total_rows}")
    logging.info(f"Not found in mapping: {len(not_found)}")

    if not_found:
        logging.info(f"\nStored procedures not found ({len(not_found)}):")
        for proc in not_found[:10]:  # Show first 10
            logging.info(f"  - {proc}")
        if len(not_found) > 10:
            logging.info(f"  ... and {len(not_found) - 10} more")

    logging.info(f"\nOutput file created: {csv_output}")
    logging.info(f"Log file: {log_filepath}")
    logging.info("="*60)

if __name__ == "__main__":
    main()

