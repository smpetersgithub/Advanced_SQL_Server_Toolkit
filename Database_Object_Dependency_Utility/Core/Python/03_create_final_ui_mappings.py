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
import logging
from datetime import datetime
from config_loader import ConfigLoader

def extract_referencing_objects(json_file):
    """Extract all referencing_object values from Dependency_List.json."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {e}")

    referencing_objects = set()
    for item in data:
        if item.get('status') == 'success' and 'results' in item:
            for result in item['results']:
                ref_obj = result.get('referencing_object', '').strip()
                if ref_obj:
                    referencing_objects.add(ref_obj)

    return sorted(list(referencing_objects))

def search_and_copy_mappings(csv_input, referencing_objects, csv_output):
    """Search for referencing objects in CSV and copy matching rows to output file."""
    try:
        # Read the input CSV file
        logging.info(f"Reading {csv_input}...")
        with open(csv_input, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
            fieldnames = reader.fieldnames

        if not fieldnames or 'Stored_Procedure' not in fieldnames:
            raise ValueError("CSV file missing 'Stored_Procedure' column")
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_input}")
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Build lookup dictionary for O(1) search (case-insensitive)
    logging.info("Building lookup index...")
    csv_lookup = {}
    for row in csv_data:
        stored_proc = row.get('Stored_Procedure', '').strip().lower()
        if stored_proc:
            if stored_proc not in csv_lookup:
                csv_lookup[stored_proc] = []
            csv_lookup[stored_proc].append(row)

    # Search for each referencing object
    logging.info(f"Searching for {len(referencing_objects)} stored procedures...")
    matching_rows = []
    found_procedures = set()

    for i, ref_obj in enumerate(referencing_objects, 1):
        if i % 100 == 0:  # Progress every 100 items
            logging.info(f"  Processed {i}/{len(referencing_objects)} procedures...")

        ref_obj_lower = ref_obj.lower()
        if ref_obj_lower in csv_lookup:
            matching_rows.extend(csv_lookup[ref_obj_lower])
            found_procedures.add(ref_obj)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_output), exist_ok=True)

    # Write matching rows to output CSV
    logging.info(f"Writing {len(matching_rows)} matching rows to {csv_output}...")
    try:
        with open(csv_output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matching_rows)
    except Exception as e:
        raise IOError(f"Error writing output CSV: {e}")

    # Calculate not found
    not_found = set(referencing_objects) - found_procedures
    return len(matching_rows), len(found_procedures), sorted(list(not_found))

def main():
    # Load configuration
    config = ConfigLoader()

    # Get configuration values
    output_dir = config.get_output_dir()
    log_dir = config.get_log_dir()

    # Define file paths
    json_file = os.path.join(output_dir, config.get_object_dependency_list_json())
    csv_input = os.path.join(output_dir, config.get_complete_mapping_csv())
    csv_output = os.path.join(output_dir, config.get_final_ui_mappings_csv())

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

    try:
        logging.info("="*60)
        logging.info("Creating Final UI Mappings")
        logging.info("="*60)

        # Validate input files exist
        if not os.path.exists(json_file):
            logging.error(f"Input JSON file not found: {json_file}")
            logging.error("Please run script 02 first to generate the dependency list")
            return
        if not os.path.exists(csv_input):
            logging.error(f"Input CSV file not found: {csv_input}")
            logging.error("Please run script 01 first to generate the UI mapping")
            return

        # Extract referencing objects from JSON
        logging.info(f"\nReading {json_file}...")
        referencing_objects = extract_referencing_objects(json_file)
        logging.info(f"Found {len(referencing_objects)} unique referencing objects")

        # Validate we have objects to process
        if not referencing_objects:
            logging.warning("No referencing objects found in JSON file")
            logging.info("Exiting - nothing to process")
            return

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

    except Exception as e:
        logging.error(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()

