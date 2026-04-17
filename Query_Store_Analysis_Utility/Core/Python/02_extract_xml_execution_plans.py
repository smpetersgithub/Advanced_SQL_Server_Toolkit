"""
Download XML Execution Plans from SQL Server Query Store

This script reads the top resource consuming queries JSON file, extracts all plan IDs,
and downloads the corresponding XML execution plans from SQL Server Query Store.
"""

import json
import pyodbc
import logging
from datetime import datetime
from pathlib import Path
from config_loader import ConfigLoader


def load_query_results(json_file_path):
    """Load the query results JSON file.

    Args:
        json_file_path: Path to the JSON file containing query results

    Returns:
        Dictionary containing query results data

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
    """
    json_file_path = Path(json_file_path)
    if not json_file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_plan_ids(query_data):
    """Extract all unique plan IDs from the query results with object names.

    Args:
        query_data: Dictionary containing query results with 'data' key

    Returns:
        List of dictionaries with plan_id, query_id, and object_name

    Raises:
        KeyError: If required keys are missing from query_data
        ValueError: If plan_ids cannot be parsed as integers
    """
    if 'data' not in query_data:
        raise KeyError("Query data missing required 'data' key")

    plan_info = []

    for record in query_data['data']:
        query_id = record.get('query_id')
        object_name = record.get('object_name', 'Unknown')
        # plan_ids field contains comma-separated plan IDs
        plan_ids_str = record.get('plan_ids', '')
        if plan_ids_str:
            try:
                # Split by comma and create plan info
                ids = [int(pid.strip()) for pid in plan_ids_str.split(',')]
                for plan_id in ids:
                    plan_info.append({
                        'plan_id': plan_id,
                        'query_id': query_id,
                        'object_name': object_name
                    })
            except ValueError as e:
                raise ValueError(f"Invalid plan_id format in record: {plan_ids_str}") from e

    # Sort by plan_id
    plan_info.sort(key=lambda x: x['plan_id'])
    return plan_info


def download_execution_plans_batch(connection_string, plan_info_list, logger, batch_size=5):
    """Download XML execution plans in batches.

    Args:
        connection_string: Database connection string
        plan_info_list: List of dictionaries with plan_id, query_id, object_name
        logger: Logger instance
        batch_size: Number of plans to fetch per batch (default: 5)

    Returns:
        List of dictionaries containing plan data with XML

    Raises:
        ValueError: If batch_size is not a positive integer
    """
    # Validate batch_size
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got: {batch_size}")

    if not plan_info_list:
        logger.warning("No plan IDs to download")
        return []

    all_plans = []
    failed_batches = []

    # Process in batches
    for i in range(0, len(plan_info_list), batch_size):
        batch = plan_info_list[i:i + batch_size]

        # Validate all plan_ids are integers to prevent SQL injection
        plan_ids = []
        for p in batch:
            plan_id = p['plan_id']
            if not isinstance(plan_id, int):
                raise ValueError(f"Invalid plan_id type: {type(plan_id)}, expected int")
            plan_ids.append(plan_id)

        plan_ids_str = ','.join(str(pid) for pid in plan_ids)

        query = f"""
        SELECT
            p.plan_id,
            p.query_id,
            CAST(p.query_plan AS NVARCHAR(MAX)) AS query_plan_xml
        FROM sys.query_store_plan p
        WHERE p.plan_id IN ({plan_ids_str})
        ORDER BY p.plan_id
        """

        try:
            # Use context managers for proper resource cleanup
            with pyodbc.connect(connection_string) as conn:
                with conn.cursor() as cursor:
                    logger.info(f"  Fetching batch {i//batch_size + 1} (plan IDs {batch[0]['plan_id']} to {batch[-1]['plan_id']})...")
                    cursor.execute(query)

                    batch_count = 0
                    for row in cursor.fetchall():
                        # Find the matching plan_info to get object_name
                        plan_info = next((p for p in batch if p['plan_id'] == row[0]), None)
                        object_name = plan_info['object_name'] if plan_info else 'Unknown'

                        all_plans.append({
                            'plan_id': row[0],
                            'query_id': row[1],
                            'object_name': object_name,
                            'xml_plan': row[2]
                        })
                        batch_count += 1

                    logger.info(f"  ✓ ({batch_count} plans)")

        except pyodbc.Error as e:
            logger.error(f"  ✗ Database Error: {str(e)[:80]}")
            failed_batches.append(batch)
        except Exception as e:
            logger.error(f"  ✗ Unexpected Error: {str(e)[:80]}")
            failed_batches.append(batch)

    if failed_batches:
        logger.warning(f"  Warning: {len(failed_batches)} batch(es) failed")

    return all_plans


def save_xml_plan(plan_data, output_dir):
    """Save XML execution plan to file.

    Args:
        plan_data: Dictionary containing plan_id, query_id, object_name, xml_plan
        output_dir: Directory path where XML file should be saved

    Returns:
        bool: True if save was successful, False otherwise
    """
    if not plan_data or not plan_data.get('xml_plan'):
        return False

    # Ensure output_dir is a Path object
    output_dir = Path(output_dir)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize object name for filename (remove special characters)
    object_name = plan_data.get('object_name') or 'Unknown'
    safe_object_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in object_name)

    # Create filename: <ObjectName>_QueryID_<query_id>_PlanID_<plan_id>.sqlplan
    filename = f"{safe_object_name}_QueryID_{plan_data['query_id']}_PlanID_{plan_data['plan_id']}.sqlplan"
    file_path = output_dir / filename

    # Write XML to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(plan_data['xml_plan'])

    return True


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_02')

    # Get logger instance
    logger = logging.getLogger(__name__)

    # Get active report settings
    active_report_key, report_settings = config.get_active_report_settings()

    # Get paths from config
    project_root = config.get_project_root()

    # Build report-specific paths
    report_base_dir = project_root / report_settings['output']['base_dir']
    json_input_path = report_base_dir / report_settings['output']['main_results_json']
    xml_output_dir = report_base_dir / report_settings['output']['xml_plans_dir']
    batch_size = config.get_xml_plan_download_batch_size()

    logger.info("=" * 70)
    logger.info(f"SQL Server Query Store - {report_settings['name']} - XML Plans")
    logger.info("=" * 70)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"Input JSON: {json_input_path}")
    logger.info(f"Output directory: {xml_output_dir}")
    logger.info(f"Batch size: {batch_size}")

    try:
        # Load query results
        logger.info("Loading query results from JSON...")
        query_data = load_query_results(json_input_path)
        logger.info(f"Loaded {query_data['record_count']} query records")

        # Extract plan IDs with object names
        logger.info("Extracting plan IDs...")
        plan_info_list = extract_plan_ids(query_data)
        logger.info(f"Found {len(plan_info_list)} unique execution plans")
        logger.info(f"Plan IDs: {[p['plan_id'] for p in plan_info_list]}")

        # Get database connection
        logger.info("Loading database configuration...")
        connection_string = config.get_connection_string()
        logger.info(f"Server: {config.get_server()}")
        logger.info(f"Database: {config.get_database()}")

        # Download execution plans in batches
        logger.info("Downloading XML execution plans in batches...")
        logger.info("-" * 70)

        plans = download_execution_plans_batch(connection_string, plan_info_list, logger, batch_size=batch_size)
        logger.info(f"Retrieved {len(plans)} execution plans from database")

        # Save each plan to file
        logger.info("Saving XML files...")
        success_count = 0
        failed_count = 0

        for i, plan_data in enumerate(plans, 1):
            try:
                logger.info(f"  [{i}/{len(plans)}] Saving {plan_data.get('object_name', 'Unknown')} (Plan ID {plan_data['plan_id']})...")

                if save_xml_plan(plan_data, xml_output_dir):
                    logger.info("  ✓")
                    success_count += 1
                else:
                    logger.error("  ✗ Failed")
                    failed_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}")
                failed_count += 1

        logger.info("-" * 70)
        logger.info(f"Download Summary:")
        logger.info(f"  Total plans: {len(plan_info_list)}")
        logger.info(f"  Successfully downloaded: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info("Download completed!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

