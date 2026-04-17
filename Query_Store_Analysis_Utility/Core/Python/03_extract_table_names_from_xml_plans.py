"""
Extract Table Names from XML Execution Plans

This script parses all XML execution plan files and extracts unique table names
referenced in the plans, saving the results to a JSON file.
"""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def extract_table_names_from_xml_plan(xml_file_path, logger):
    """Extract table names from a single XML execution plan file.

    Args:
        xml_file_path: Path to the XML execution plan file
        logger: Logger instance

    Returns:
        List of dictionaries containing table information (schema, table, full_name)
        Returns empty list if parsing fails
    """
    # Validate input
    xml_file_path = Path(xml_file_path)
    if not xml_file_path.exists():
        logger.error(f"  XML file not found: {xml_file_path.name}")
        return []

    tables = []

    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse XML with defusedxml would be better for production, but ET is acceptable
        # for trusted internal SQL Server execution plans
        # Note: Consider using defusedxml.ElementTree for untrusted XML sources
        root = ET.fromstring(content)

        # SQL Server execution plans use this namespace
        namespaces = {'ns': 'http://schemas.microsoft.com/sqlserver/2004/07/showplan'}

        # Find all Object elements (tables, views, etc.)
        for obj in root.findall('.//ns:Object', namespaces):
            table = obj.get('Table')
            schema = obj.get('Schema')
            database = obj.get('Database')

            if table and schema:
                table_info = {
                    'schema': schema,
                    'table': table,
                    'full_name': f"{schema}.{table}"
                }

                if database:
                    table_info['database'] = database
                    table_info['full_name_with_db'] = f"{database}.{schema}.{table}"

                tables.append(table_info)

        return tables

    except ET.ParseError as e:
        logger.error(f"  XML parsing error in {xml_file_path.name}: {str(e)}")
        return []
    except FileNotFoundError as e:
        logger.error(f"  File not found: {xml_file_path.name}")
        return []
    except Exception as e:
        logger.error(f"  Unexpected error parsing {xml_file_path.name}: {str(e)}")
        return []


def process_all_xml_plans(xml_plans_dir, logger, xml_extension='.sqlplan'):
    """Process all XML execution plan files in the directory.

    Args:
        xml_plans_dir: Directory containing XML execution plan files
        logger: Logger instance
        xml_extension: File extension for XML plans (default: '.sqlplan')

    Returns:
        Dictionary with 'unique_tables' and 'plan_details' keys
        Returns empty dict if directory doesn't exist or no files found

    Raises:
        ValueError: If xml_extension is invalid
    """
    # Validate inputs
    if not xml_extension or not xml_extension.startswith('.'):
        raise ValueError(f"Invalid xml_extension: {xml_extension}. Must start with '.'")

    xml_plans_dir = Path(xml_plans_dir)

    # Check if directory exists
    if not xml_plans_dir.exists():
        logger.error(f"XML plans directory not found: {xml_plans_dir}")
        return {}

    if not xml_plans_dir.is_dir():
        logger.error(f"Path is not a directory: {xml_plans_dir}")
        return {}

    xml_files = list(xml_plans_dir.glob(f'*{xml_extension}'))

    if not xml_files:
        logger.warning(f"No {xml_extension} files found in {xml_plans_dir}")
        return {}

    logger.info(f"Found {len(xml_files)} XML execution plan files")

    all_tables = {}
    plan_details = []

    for xml_file in xml_files:
        logger.info(f"Processing: {xml_file.name}...")

        tables = extract_table_names_from_xml_plan(xml_file, logger)

        if tables:
            logger.info(f"  ✓ ({len(tables)} table references)")

            # Track which plan file references which tables
            plan_info = {
                'plan_file': xml_file.name,
                'tables': tables
            }
            plan_details.append(plan_info)

            # Add to unique tables set
            for table in tables:
                full_name = table['full_name']
                if full_name not in all_tables:
                    all_tables[full_name] = {
                        'schema': table['schema'],
                        'table': table['table'],
                        'referenced_in_plans': []
                    }

                if xml_file.name not in all_tables[full_name]['referenced_in_plans']:
                    all_tables[full_name]['referenced_in_plans'].append(xml_file.name)
        else:
            logger.info("  ✓ (no tables found)")

    return {
        'unique_tables': all_tables,
        'plan_details': plan_details
    }


def save_results_to_json(results, output_path, logger):
    """Save table extraction results to JSON file.

    Args:
        results: Dictionary containing 'unique_tables' and 'plan_details'
        output_path: Path where JSON file should be saved
        logger: Logger instance

    Raises:
        KeyError: If results dictionary is missing required keys
    """
    # Validate results structure
    if 'unique_tables' not in results or 'plan_details' not in results:
        raise KeyError("Results dictionary must contain 'unique_tables' and 'plan_details' keys")

    # Ensure output_path is a Path object
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare output data
    unique_table_list = sorted(results['unique_tables'].keys())

    output_data = {
        "extraction_timestamp": datetime.now().isoformat(),
        "total_unique_tables": len(unique_table_list),
        "unique_table_names": unique_table_list,
        "table_details": results['unique_tables'],
        "plan_count": len(results['plan_details']),
        "plan_details": results['plan_details']
    }

    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Results saved to: {output_path}")


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_03')

    # Get logger instance
    logger = logging.getLogger(__name__)

    # Get active report settings
    active_report_key, report_settings = config.get_active_report_settings()

    # Build report-specific paths
    project_root = config.get_project_root()
    report_base_dir = project_root / report_settings['output']['base_dir']
    xml_plans_dir = report_base_dir / report_settings['output']['xml_plans_dir']
    output_file = report_base_dir / report_settings['output']['table_names_json']
    xml_extension = config.get_xml_file_extension()

    logger.info("=" * 70)
    logger.info(f"{report_settings['name']} - Extract Table Names from XML Plans")
    logger.info("=" * 70)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"XML Plans Directory: {xml_plans_dir}")
    logger.info(f"XML File Extension: {xml_extension}")
    logger.info(f"Output File: {output_file}")

    try:
        # Process all XML plans
        results = process_all_xml_plans(xml_plans_dir, logger, xml_extension)

        if not results or not results['unique_tables']:
            logger.warning("No tables found in XML execution plans.")
            return

        logger.info("-" * 70)
        logger.info(f"Summary:")
        logger.info(f"  Total unique tables: {len(results['unique_tables'])}")
        logger.info(f"  Total plans processed: {len(results['plan_details'])}")
        logger.info("Unique tables found:")
        for table_name in sorted(results['unique_tables'].keys()):
            plan_count = len(results['unique_tables'][table_name]['referenced_in_plans'])
            logger.info(f"  - {table_name} (referenced in {plan_count} plan(s))")
        logger.info("-" * 70)

        # Save results
        save_results_to_json(results, output_file, logger)

        logger.info("Extraction completed successfully!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

