import json
from pathlib import Path
from typing import Dict, List, Any
import sys
import logging
from datetime import datetime
from config_loader import ConfigLoader
from execution_plan_parser import parse_execution_plan


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


# ============================================================================
# CONFIGURATION AND LOGGING SETUP
# ============================================================================

# Load configuration using ConfigLoader
config_loader = ConfigLoader()
base_dir = config_loader.get_base_dir()

# Set up logging
LOG_FILE = config_loader.setup_logging(config_loader.get_single_plan_analysis_log_file())


def load_plan_config(config_loader: ConfigLoader) -> Dict[str, Any]:
    """Load configuration file with plan file paths."""
    config_file = config_loader.get_config_dir() / config_loader.get_plan_config_file()
    try:
        # Use utf-8-sig to handle BOM if present
        with open(config_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        # Check if it's the new format (array of objects with ID, Name, FullPath)
        if isinstance(data, list):
            # Convert new format to old format
            plan_files = []
            for item in data:
                plan_files.append({
                    'name': item.get('Name', item.get('name', 'Unknown')),
                    'path': item.get('FullPath', item.get('path', '')),
                    'description': item.get('Description', item.get('description', '')),
                    'active': item.get('Active', item.get('active', False))
                })
            return {'planFiles': plan_files}

        # Check if it's a single plan object (has Name, FullPath, etc.)
        if isinstance(data, dict) and 'Name' in data and 'FullPath' in data:
            # Convert single plan object to array format
            plan_files = [{
                'name': data.get('Name', data.get('name', 'Unknown')),
                'path': data.get('FullPath', data.get('path', '')),
                'description': data.get('Description', data.get('description', '')),
                'active': data.get('Active', data.get('active', False))
            }]
            return {'planFiles': plan_files}

        # Old format - return as is
        return data

    except FileNotFoundError:
        logging.error(f"Config file '{config_file}' not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)


def main():
    """Main function to analyze individual execution plans."""

    logging.info("="*80)
    logging.info("INDIVIDUAL EXECUTION PLAN ANALYSIS - STARTED")
    logging.info("="*80)
    logging.info(f"Log file: {LOG_FILE}")

    # Load configuration
    plan_config_file = config_loader.get_config_dir() / config_loader.get_plan_config_file()
    logging.info(f"Loading configuration from {plan_config_file}...")
    plan_config = load_plan_config(config_loader)

    # Get active plan files
    all_plan_files = plan_config['planFiles']
    plan_files = [plan for plan in all_plan_files if plan.get('active', False)]

    logging.info(f"Total plan files in config: {len(all_plan_files)}")
    logging.info(f"Active plan files: {len(plan_files)}")

    if len(plan_files) == 0:
        logging.error("No active plan files found in configuration!")
        logging.info("Please mark at least one plan as active in the configuration.")
        sys.exit(1)

    # Analyze each plan individually
    results = []
    failed_plans = []

    for idx, plan_info in enumerate(plan_files, 1):
        plan_name = plan_info['name']
        plan_path = plan_info['path']
        plan_description = plan_info.get('description', '')

        logging.info(f"\nPlan {idx}/{len(plan_files)}: {plan_name}")
        logging.info(f"  Path: {plan_path}")
        if plan_description:
            logging.info(f"  Description: {plan_description}")

        # Validate plan path exists
        if not Path(plan_path).exists():
            logging.error(f"  ❌ Plan file not found: {plan_path}")
            failed_plans.append({
                'name': plan_name,
                'path': plan_path,
                'error': 'File not found'
            })
            continue

        try:
            logging.info(f"  Parsing {plan_name}...")
            plan_data = parse_execution_plan(plan_path)
            plan_data['config_name'] = plan_name  # Add the config name
            plan_data['description'] = plan_description

            results.append(plan_data)
            logging.info(f"  ✅ Successfully parsed {plan_name}")

        except FileNotFoundError as e:
            logging.error(f"  ❌ File not found: {e}")
            failed_plans.append({
                'name': plan_name,
                'path': plan_path,
                'error': str(e)
            })
        except ValueError as e:
            logging.error(f"  ❌ Parse error: {e}")
            failed_plans.append({
                'name': plan_name,
                'path': plan_path,
                'error': str(e)
            })
        except Exception as e:
            logging.error(f"  ❌ Unexpected error: {e}")
            logging.exception("Full traceback:")
            failed_plans.append({
                'name': plan_name,
                'path': plan_path,
                'error': f"Unexpected error: {str(e)}"
            })

    # Create output directory if it doesn't exist
    output_dir = config_loader.get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results to JSON
    json_filename = config_loader.get_json_single_plan_output_file()
    output_file = output_dir / json_filename

    # Create output structure
    output_data = {
        'analysis_timestamp': datetime.now().strftime(config_loader.get_analysis_timestamp_format()),
        'total_plans': len(results),
        'plans': results
    }

    logging.info(f"\nWriting results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logging.info(f"\n✅ Analysis complete! Results saved to {output_file}")

    logging.info("\n" + "="*80)
    logging.info("SUMMARY")
    logging.info("="*80)
    logging.info(f"\nTotal plans in config: {len(plan_files)}")
    logging.info(f"Successfully analyzed: {len(results)}")
    logging.info(f"Failed: {len(failed_plans)}")

    # Show failed plans if any
    if failed_plans:
        logging.info("\n❌ Failed Plans:")
        for failed in failed_plans:
            logging.info(f"  - {failed['name']}: {failed['error']}")

    # Show successful plans
    if results:
        logging.info("\n✅ Successfully Analyzed Plans:")
        for plan_data in results:
            logging.info(f"\n{plan_data['plan_name']}:")
            logging.info(f"  Total Statements: {plan_data['summary']['total_statements']}")
            logging.info(f"  Total Estimated Cost: {plan_data['summary']['total_estimated_cost']:.3f}")
            logging.info(f"  Total Elapsed Time: {plan_data['summary']['total_elapsed_time_ms']}ms")
            logging.info(f"  Total Logical Reads: {plan_data['summary']['total_logical_reads']:,}")
            logging.info(f"  Optimizer Timeouts: {plan_data['summary']['optimizer_timeouts']}")
            logging.info(f"  Missing Indexes: {len(plan_data['summary']['missing_indexes'])}")
            logging.info(f"  Warnings: {plan_data['summary']['total_warnings']}")

    logging.info("\n" + "="*80)

    # Exit with error code if all plans failed
    if len(results) == 0 and len(failed_plans) > 0:
        logging.error("\n❌ All plans failed to parse!")
        sys.exit(1)


if __name__ == '__main__':
    main()


