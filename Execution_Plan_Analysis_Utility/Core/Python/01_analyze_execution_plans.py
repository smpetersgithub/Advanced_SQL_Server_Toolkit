import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import logging
from datetime import datetime
from config_loader import ConfigLoader
from execution_plan_parser import parse_execution_plan, calculate_percentage_difference


# ============================================================================
# COMPARISON FUNCTION
# ============================================================================

def compare_plans(plan1: Dict[str, Any], plan2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two execution plans and determine winner using weighted scoring.

    Args:
        plan1: First execution plan dictionary
        plan2: Second execution plan dictionary

    Returns:
        Dictionary containing comparison results and winner determination
    """
    # Use config_name if available, otherwise fall back to plan_name
    plan1_name = plan1.get('config_name', plan1['plan_name'])
    plan2_name = plan2.get('config_name', plan2['plan_name'])

    comparison = {
        'plan1_name': plan1_name,
        'plan2_name': plan2_name,
        'metrics': {},
        'winner': None,
        'winner_reasons': [],
        'weighted_score': {}
    }

    # Define metrics with weights (higher weight = more important)
    # Note: total_statements is excluded as lower isn't necessarily better
    metrics = [
        ('total_elapsed_time_ms', 'lower', 3.0),      # Most important
        ('total_logical_reads', 'lower', 2.5),        # Very important
        ('total_estimated_cost', 'lower', 2.0),       # Important
        ('total_cpu_time_ms', 'lower', 1.5),          # Moderately important
        ('optimizer_timeouts', 'lower', 2.0),         # Important (indicates problems)
        ('total_wait_time_ms', 'lower', 1.0)          # Less important
    ]

    plan1_score = 0.0
    plan2_score = 0.0
    total_weight = sum(weight for _, _, weight in metrics)

    for metric, better, weight in metrics:
        val1 = plan1['summary'][metric]
        val2 = plan2['summary'][metric]

        if val1 == val2:
            winner = 'tie'
        elif better == 'lower':
            winner = plan1_name if val1 < val2 else plan2_name
        else:
            winner = plan1_name if val1 > val2 else plan2_name

        # Calculate percentage difference
        pct_diff = calculate_percentage_difference(val1, val2)

        # Handle None (infinite difference)
        if pct_diff is None:
            pct_diff_display = 'N/A (baseline is zero)'
        else:
            pct_diff_display = round(pct_diff, 2)

        comparison['metrics'][metric] = {
            plan1_name: val1,
            plan2_name: val2,
            'winner': winner,
            'percent_difference': pct_diff_display,
            'weight': weight
        }

        # Add to weighted score
        if winner == plan1_name:
            plan1_score += weight
        elif winner == plan2_name:
            plan2_score += weight

    # Store weighted scores
    comparison['weighted_score'] = {
        plan1_name: round(plan1_score, 2),
        plan2_name: round(plan2_score, 2),
        'total_possible': total_weight
    }

    # Determine overall winner based on weighted score
    if plan1_score > plan2_score:
        comparison['winner'] = plan1_name
    elif plan2_score > plan1_score:
        comparison['winner'] = plan2_name
    else:
        comparison['winner'] = 'tie'

    # Generate winner reasons (only for metrics where winner won)
    for metric, data in comparison['metrics'].items():
        if data['winner'] != 'tie' and data['winner'] == comparison['winner']:
            pct_diff = data['percent_difference']
            if pct_diff != 'N/A (baseline is zero)':
                comparison['winner_reasons'].append(
                    f"{metric}: {data['winner']} is {abs(pct_diff):.1f}% better (weight: {data['weight']})"
                )
            else:
                comparison['winner_reasons'].append(
                    f"{metric}: {data['winner']} is better (weight: {data['weight']})"
                )

    return comparison


# ============================================================================
# CONFIGURATION AND LOGGING SETUP
# ============================================================================

# Load configuration
try:
    config = ConfigLoader()
except FileNotFoundError as e:
    print(f"[ERROR] {e}")
    print("Please ensure config.json exists in the Config directory.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Configuration error: {e}")
    print("Please check your config.json file for errors.")
    sys.exit(1)

# Get base directory
base_dir = config.get_base_dir()

# Setup logging
LOG_FILE = config.setup_logging(config.get_analysis_log_file())


def load_plan_config(config: ConfigLoader, base_dir: Path) -> Dict[str, Any]:
    """Load configuration file with plan file paths."""
    config_file = config.get_config_dir() / config.get_plan_config_file()
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
        logging.info("Please create a config file with the following structure:")
        logging.info("""
[
  {
    "ID": 1,
    "Name": "Version 1",
    "FullPath": "path/to/version1.sqlplan",
    "Description": "Description of version 1",
    "Active": true
  },
  {
    "ID": 2,
    "Name": "Version 2",
    "FullPath": "path/to/version2.sqlplan",
    "Description": "Description of version 2",
    "Active": true
  }
]
        """)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)


def main():
    """Main function to analyze execution plans."""

    logging.info("="*80)
    logging.info("EXECUTION PLAN ANALYSIS - STARTED")
    logging.info("="*80)
    logging.info(f"Log file: {LOG_FILE}")

    # Create output directory if it doesn't exist
    output_dir = config.get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load plan configuration
    plan_config_file = config.get_config_dir() / config.get_plan_config_file()
    logging.info(f"Loading configuration from {plan_config_file}...")
    plan_config = load_plan_config(config, base_dir)

    # Validate config
    if 'planFiles' not in plan_config or len(plan_config['planFiles']) < 2:
        logging.error("Config file must contain at least 2 plan files in 'planFiles' array")
        sys.exit(1)

    # Filter only active plan files
    all_plan_files = plan_config['planFiles']
    plan_files = [plan for plan in all_plan_files if plan.get('active', False)]

    logging.info(f"Total plan files in config: {len(all_plan_files)}")
    logging.info(f"Active plan files: {len(plan_files)}")

    if len(plan_files) < 2:
        logging.error(f"Need at least 2 active plan files, but only found {len(plan_files)}")
        logging.error("Please set 'active': true for at least 2 plans in the config file")
        sys.exit(1)

    # Get the first two active plans from config
    plan1_config = plan_files[0]
    plan2_config = plan_files[1]

    logging.info(f"\nPlan 1: {plan1_config['name']}")
    logging.info(f"  Path: {plan1_config['path']}")
    logging.info(f"  Description: {plan1_config.get('description', 'N/A')}")

    logging.info(f"\nPlan 2: {plan2_config['name']}")
    logging.info(f"  Path: {plan2_config['path']}")
    logging.info(f"  Description: {plan2_config.get('description', 'N/A')}")

    # Check if files exist
    plan1_path = Path(plan1_config['path'])
    plan2_path = Path(plan2_config['path'])

    if not plan1_path.exists():
        logging.error(f"Plan file not found: {plan1_path}")
        sys.exit(1)

    if not plan2_path.exists():
        logging.error(f"Plan file not found: {plan2_path}")
        sys.exit(1)

    # Parse both execution plans
    logging.info(f"\nParsing {plan1_config['name']}...")
    plan1 = parse_execution_plan(str(plan1_path))
    plan1['config_name'] = plan1_config['name']
    plan1['config_description'] = plan1_config.get('description', '')

    logging.info(f"Parsing {plan2_config['name']}...")
    plan2 = parse_execution_plan(str(plan2_path))
    plan2['config_name'] = plan2_config['name']
    plan2['config_description'] = plan2_config.get('description', '')

    # Compare plans
    logging.info("\nComparing execution plans...")
    comparison = compare_plans(plan1, plan2)

    # Create output
    analysis_timestamp_format = config.get_analysis_timestamp_format()
    output = {
        'analysis_timestamp': datetime.now().strftime(analysis_timestamp_format),
        'config_file': str(plan_config_file),
        'plan1': plan1,
        'plan2': plan2,
        'comparison': comparison
    }

    # Write to JSON file in Output folder
    json_filename = config.get_json_output_file()
    output_file = output_dir / json_filename
    logging.info(f"\nWriting results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logging.info(f"\n✅ Analysis complete! Results saved to {output_file}")

    # Print summary
    logging.info("\n" + "="*80)
    logging.info("SUMMARY")
    logging.info("="*80)
    logging.info(f"\nPlan 1: {plan1_config['name']}")
    logging.info(f"Plan 2: {plan2_config['name']}")
    logging.info(f"\nWinner: {comparison['winner']}")

    # Show weighted scores
    if 'weighted_score' in comparison:
        logging.info(f"\nWeighted Scores:")
        logging.info(f"  {plan1_config['name']}: {comparison['weighted_score'][plan1_config['name']]} / {comparison['weighted_score']['total_possible']}")
        logging.info(f"  {plan2_config['name']}: {comparison['weighted_score'][plan2_config['name']]} / {comparison['weighted_score']['total_possible']}")

    logging.info(f"\nKey Metrics:")
    logging.info(f"  Total Elapsed Time: {plan1['summary']['total_elapsed_time_ms']}ms vs {plan2['summary']['total_elapsed_time_ms']}ms")
    logging.info(f"  Total Logical Reads: {plan1['summary']['total_logical_reads']:,} vs {plan2['summary']['total_logical_reads']:,}")
    logging.info(f"  Total Estimated Cost: {plan1['summary']['total_estimated_cost']:.3f} vs {plan2['summary']['total_estimated_cost']:.3f}")
    logging.info(f"  Optimizer Timeouts: {plan1['summary']['optimizer_timeouts']} vs {plan2['summary']['optimizer_timeouts']}")
    logging.info(f"  Missing Indexes: {len(plan1['summary']['missing_indexes'])} vs {len(plan2['summary']['missing_indexes'])}")
    logging.info(f"  Total Warnings: {plan1['summary']['total_warnings']} vs {plan2['summary']['total_warnings']}")
    logging.info("\n" + "="*80)


if __name__ == '__main__':
    main()

