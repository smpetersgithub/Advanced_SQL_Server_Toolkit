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
import sys
import logging
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

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
        logger.info(f"Reading {csv_input}...")
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
    logger.info("Building lookup index...")
    csv_lookup = {}
    for row in csv_data:
        stored_proc = row.get('Stored_Procedure', '').strip().lower()
        if stored_proc:
            if stored_proc not in csv_lookup:
                csv_lookup[stored_proc] = []
            csv_lookup[stored_proc].append(row)

    # Search for each referencing object
    logger.info(f"Searching for {len(referencing_objects)} stored procedures...")
    matching_rows = []
    found_procedures = set()

    for i, ref_obj in enumerate(referencing_objects, 1):
        if i % 100 == 0:  # Progress every 100 items
            logger.info(f"  Processed {i}/{len(referencing_objects)} procedures...")

        ref_obj_lower = ref_obj.lower()
        if ref_obj_lower in csv_lookup:
            matching_rows.extend(csv_lookup[ref_obj_lower])
            found_procedures.add(ref_obj)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_output), exist_ok=True)

    # Write matching rows to output CSV
    logger.info(f"Writing {len(matching_rows)} matching rows to {csv_output}...")
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
    try:
        config = ConfigLoader()
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"[ERROR] Configuration error: {e}")
        sys.exit(1)

    # Get configuration values
    output_dir = config.get_output_dir()

    # Define file paths
    json_file = os.path.join(output_dir, config.get_object_dependency_list_json())
    csv_input = os.path.join(output_dir, config.get_complete_mapping_csv())
    csv_output = os.path.join(output_dir, config.get_final_ui_mappings_csv())

    # Setup logging
    log_file = config.setup_logging('03_create_final_ui_mappings')

    try:
        logger.info("="*60)
        logger.info("Creating Final UI Mappings")
        logger.info("="*60)

        # Validate input files exist
        if not os.path.exists(json_file):
            logger.error(f"Input JSON file not found: {json_file}")
            logger.error("Please run script 02 first to generate the dependency list")
            return
        if not os.path.exists(csv_input):
            logger.error(f"Input CSV file not found: {csv_input}")
            logger.error("Please run script 01 first to generate the UI mapping")
            return

        # Extract referencing objects from JSON
        logger.info(f"\nReading {json_file}...")
        referencing_objects = extract_referencing_objects(json_file)
        logger.info(f"Found {len(referencing_objects)} unique referencing objects")

        # Validate we have objects to process
        if not referencing_objects:
            logger.warning("No referencing objects found in JSON file")
            logger.info("Exiting - nothing to process")
            return

        # Search and copy matching rows
        total_rows, found_count, not_found = search_and_copy_mappings(
            csv_input, referencing_objects, csv_output
        )

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("Summary:")
        logger.info("="*60)
        logger.info(f"Total referencing objects searched: {len(referencing_objects)}")
        logger.info(f"Stored procedures found in mapping: {found_count}")
        logger.info(f"Total matching rows copied: {total_rows}")
        logger.info(f"Not found in mapping: {len(not_found)}")

        if not_found:
            logger.info(f"\nStored procedures not found ({len(not_found)}):")
            for proc in not_found[:10]:  # Show first 10
                logger.info(f"  - {proc}")
            if len(not_found) > 10:
                logger.info(f"  ... and {len(not_found) - 10} more")

        logger.info(f"\nOutput file created: {csv_output}")
        logger.info(f"Log file: {log_file}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
