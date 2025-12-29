import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, List, Any
import sys
import logging
from datetime import datetime
import configparser

def parse_execution_plan(file_path: str) -> Dict[str, Any]:
    """Parse SQL Server execution plan XML file and extract statistics."""
    
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Define namespace
    ns = {'sp': 'http://schemas.microsoft.com/sqlserver/2004/07/showplan'}
    
    plan_name = Path(file_path).stem
    
    result = {
        'plan_name': plan_name,
        'file_path': file_path,
        'statements': [],
        'warnings': [],
        'summary': {
            'total_estimated_cost': 0.0,
            'total_elapsed_time_ms': 0,
            'total_cpu_time_ms': 0,
            'total_logical_reads': 0,
            'total_statements': 0,
            'optimizer_timeouts': 0,
            'missing_indexes': [],
            'total_warnings': 0
        }
    }
    
    # Find all statements
    statements = root.findall('.//sp:StmtSimple', ns)
    
    for stmt in statements:
        statement_id = stmt.get('StatementId')
        statement_type = stmt.get('StatementType')
        statement_cost = float(stmt.get('StatementSubTreeCost', 0))
        optimizer_level = stmt.get('StatementOptmLevel')
        early_abort_reason = stmt.get('StatementOptmEarlyAbortReason')
        estimated_rows = float(stmt.get('StatementEstRows', 0))
        
        # Get query text (truncated for readability)
        statement_text = stmt.get('StatementText', '')
        statement_text_preview = statement_text[:100].replace('\n', ' ').replace('\r', ' ')
        
        # Get query time stats
        query_time_stats = stmt.find('.//sp:QueryTimeStats', ns)
        cpu_time = 0
        elapsed_time = 0
        if query_time_stats is not None:
            cpu_time = int(query_time_stats.get('CpuTime', 0))
            elapsed_time = int(query_time_stats.get('ElapsedTime', 0))
        
        # Get runtime counters (logical reads, actual rows, etc.)
        runtime_counters = stmt.find('.//sp:RunTimeCountersPerThread[@Thread="0"]', ns)
        logical_reads = 0
        actual_rows = 0
        actual_executions = 0
        
        if runtime_counters is not None:
            logical_reads = int(runtime_counters.get('ActualLogicalReads', 0))
            actual_rows = int(runtime_counters.get('ActualRows', 0))
            actual_executions = int(runtime_counters.get('ActualExecutions', 0))
        
        # Check for missing indexes
        missing_indexes = []
        missing_index_groups = stmt.findall('.//sp:MissingIndexGroup', ns)
        for group in missing_index_groups:
            impact = float(group.get('Impact', 0))
            missing_index = group.find('.//sp:MissingIndex', ns)
            if missing_index is not None:
                database = missing_index.get('Database', '')
                schema = missing_index.get('Schema', '')
                table = missing_index.get('Table', '')
                
                # Get columns
                equality_cols = []
                inequality_cols = []
                include_cols = []
                
                for col_group in missing_index.findall('.//sp:ColumnGroup', ns):
                    usage = col_group.get('Usage')
                    cols = [col.get('Name') for col in col_group.findall('.//sp:Column', ns)]
                    
                    if usage == 'EQUALITY':
                        equality_cols = cols
                    elif usage == 'INEQUALITY':
                        inequality_cols = cols
                    elif usage == 'INCLUDE':
                        include_cols = cols
                
                missing_indexes.append({
                    'impact_percent': impact,
                    'database': database,
                    'schema': schema,
                    'table': table,
                    'equality_columns': equality_cols,
                    'inequality_columns': inequality_cols,
                    'include_columns': include_cols
                })

        # Check for warnings - generic approach to capture all warning types
        warnings = []
        warning_elements = stmt.findall('.//sp:Warnings', ns)
        for warning_elem in warning_elements:
            # Iterate through all child elements of Warnings
            for child in warning_elem:
                # Get the warning type from the element tag (remove namespace)
                warning_type = child.tag.replace('{http://schemas.microsoft.com/sqlserver/2004/07/showplan}', '')

                # Create warning entry with type and all attributes
                warning_entry = {
                    'type': warning_type,
                    'statement_id': statement_id
                }

                # Add all attributes from the warning element
                warning_entry.update(child.attrib)

                warnings.append(warning_entry)

        # Add warnings to result
        result['warnings'].extend(warnings)

        # Get operators with detailed node information
        node_details = []
        node_id = 0

        for op in stmt.findall('.//sp:RelOp', ns):
            node_id += 1
            op_type = op.get('LogicalOp')
            op_cost = float(op.get('EstimatedTotalSubtreeCost', 0))
            op_rows = float(op.get('EstimateRows', 0))

            # Detailed node information
            node_info = {
                'statement_id': statement_id,
                'node_id': node_id,
                'node_type': op_type,
                'physical_op': op.get('PhysicalOp', ''),
                'logical_op': op_type,
                'estimated_cost': op_cost,
                'estimated_rows': op_rows,
                'estimated_cpu_cost': float(op.get('EstimateCPU', 0)),
                'estimated_io_cost': float(op.get('EstimateIO', 0)),
                'estimated_executions': float(op.get('EstimateExecutions', 1)),
                'parallel': 'Yes' if op.get('Parallel') == '1' or op.get('Parallel') == 'true' else 'No'
            }

            # Get actual runtime information if available
            runtime_info = op.find('.//sp:RunTimeInformation/sp:RunTimeCountersPerThread', ns)
            if runtime_info is not None:
                node_info['actual_rows'] = int(runtime_info.get('ActualRows', 0))
                node_info['actual_executions'] = int(runtime_info.get('ActualExecutions', 0))
                node_info['actual_rebinds'] = int(runtime_info.get('ActualRebinds', 0))
                node_info['actual_rewinds'] = int(runtime_info.get('ActualRewinds', 0))
            else:
                node_info['actual_rows'] = 0
                node_info['actual_executions'] = 0
                node_info['actual_rebinds'] = 0
                node_info['actual_rewinds'] = 0

            # Extract table/index information
            table_index = ''
            seek_predicates = ''
            predicate = ''
            output_list = ''

            # Check for Index Scan/Seek
            index_scan = op.find('.//sp:IndexScan', ns)
            if index_scan is not None:
                obj = index_scan.find('.//sp:Object', ns)
                if obj is not None:
                    database = obj.get('Database', '')
                    schema = obj.get('Schema', '')
                    table = obj.get('Table', '')
                    index = obj.get('Index', '')
                    if index:
                        table_index = f"[{database}].[{schema}].[{table}].[{index}]" if database else f"[{schema}].[{table}].[{index}]"
                    else:
                        table_index = f"[{database}].[{schema}].[{table}]" if database else f"[{schema}].[{table}]"

                # Get seek predicates from ScalarString attribute
                seek_preds = index_scan.findall('.//sp:SeekPredicates//sp:ScalarOperator[@ScalarString]', ns)
                if seek_preds:
                    seek_predicates = ' AND '.join([pred.get('ScalarString', '') for pred in seek_preds if pred.get('ScalarString')])

                # Get predicate (filter) from ScalarString attribute
                pred_elem = index_scan.find('.//sp:Predicate/sp:ScalarOperator[@ScalarString]', ns)
                if pred_elem is not None:
                    predicate = pred_elem.get('ScalarString', '')

            # Check for Table Scan
            table_scan = op.find('.//sp:TableScan', ns)
            if table_scan is not None:
                obj = table_scan.find('.//sp:Object', ns)
                if obj is not None:
                    database = obj.get('Database', '')
                    schema = obj.get('Schema', '')
                    table = obj.get('Table', '')
                    table_index = f"[{database}].[{schema}].[{table}]" if database else f"[{schema}].[{table}]"

                # Get predicate from ScalarString attribute
                pred_elem = table_scan.find('.//sp:Predicate/sp:ScalarOperator[@ScalarString]', ns)
                if pred_elem is not None:
                    predicate = pred_elem.get('ScalarString', '')

            # Check for other operations with objects (Update/Insert/Delete)
            if not table_index:
                for op_name in ['Update', 'Insert', 'Delete']:
                    update_op = op.find(f'.//sp:{op_name}', ns)
                    if update_op is not None:
                        obj = update_op.find('.//sp:Object', ns)
                        if obj is not None:
                            database = obj.get('Database', '')
                            schema = obj.get('Schema', '')
                            table = obj.get('Table', '')
                            table_index = f"[{database}].[{schema}].[{table}]" if database else f"[{schema}].[{table}]"
                        break

            # Get output list
            output_elem = op.find('.//sp:OutputList', ns)
            if output_elem is not None:
                columns = []
                for col_ref in output_elem.findall('.//sp:ColumnReference', ns):
                    col_name = col_ref.get('Column', '')
                    if col_name:
                        columns.append(col_name)
                output_list = ', '.join(columns[:10])  # Limit to first 10 columns
                if len(columns) > 10:
                    output_list += '...'

            # Check for warnings at node level
            warnings_elem = op.find('.//sp:Warnings', ns)
            warnings_text = ''
            if warnings_elem is not None:
                warning_types = []
                for child in warnings_elem:
                    warning_type = child.tag.replace('{http://schemas.microsoft.com/sqlserver/2004/07/showplan}', '')
                    warning_types.append(warning_type)
                warnings_text = ', '.join(warning_types)

            node_info['table_index'] = table_index
            node_info['seek_predicates'] = seek_predicates
            node_info['predicate'] = predicate
            node_info['output_list'] = output_list
            node_info['warnings'] = warnings_text

            node_details.append(node_info)

        # Build statement info
        statement_info = {
            'statement_id': statement_id,
            'statement_type': statement_type,
            'statement_text_preview': statement_text_preview,
            'estimated_cost': statement_cost,
            'estimated_rows': estimated_rows,
            'optimizer_level': optimizer_level,
            'early_abort_reason': early_abort_reason,
            'cpu_time_ms': cpu_time,
            'elapsed_time_ms': elapsed_time,
            'wait_time_ms': elapsed_time - cpu_time,
            'logical_reads': logical_reads,
            'actual_rows': actual_rows,
            'actual_executions': actual_executions,
            'missing_indexes': missing_indexes,
            'node_details': node_details
        }

        result['statements'].append(statement_info)
        
        # Update summary
        result['summary']['total_estimated_cost'] += statement_cost
        result['summary']['total_elapsed_time_ms'] += elapsed_time
        result['summary']['total_cpu_time_ms'] += cpu_time
        result['summary']['total_logical_reads'] += logical_reads
        result['summary']['total_statements'] += 1
        
        if early_abort_reason == 'TimeOut':
            result['summary']['optimizer_timeouts'] += 1
        
        if missing_indexes:
            result['summary']['missing_indexes'].extend(missing_indexes)
    
    # Calculate total wait time
    result['summary']['total_wait_time_ms'] = (
        result['summary']['total_elapsed_time_ms'] -
        result['summary']['total_cpu_time_ms']
    )

    # Count total warnings
    result['summary']['total_warnings'] = len(result['warnings'])

    return result


def compare_plans(plan1: Dict[str, Any], plan2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two execution plans and determine winner."""

    # Use config_name if available, otherwise fall back to plan_name
    plan1_name = plan1.get('config_name', plan1['plan_name'])
    plan2_name = plan2.get('config_name', plan2['plan_name'])

    comparison = {
        'plan1_name': plan1_name,
        'plan2_name': plan2_name,
        'metrics': {},
        'winner': None,
        'winner_reasons': []
    }
    
    # Compare metrics
    metrics = [
        ('total_estimated_cost', 'lower'),
        ('total_elapsed_time_ms', 'lower'),
        ('total_cpu_time_ms', 'lower'),
        ('total_logical_reads', 'lower'),
        ('total_statements', 'lower'),
        ('optimizer_timeouts', 'lower'),
        ('total_wait_time_ms', 'lower')
    ]
    
    plan1_wins = 0
    plan2_wins = 0
    
    for metric, better in metrics:
        val1 = plan1['summary'][metric]
        val2 = plan2['summary'][metric]

        if val1 == val2:
            winner = 'tie'
        elif better == 'lower':
            winner = plan1_name if val1 < val2 else plan2_name
        else:
            winner = plan1_name if val1 > val2 else plan2_name

        # Calculate percentage difference
        if val2 != 0:
            pct_diff = ((val1 - val2) / val2) * 100
        else:
            pct_diff = 0 if val1 == 0 else 100

        comparison['metrics'][metric] = {
            plan1_name: val1,
            plan2_name: val2,
            'winner': winner,
            'percent_difference': round(pct_diff, 2)
        }

        if winner == plan1_name:
            plan1_wins += 1
        elif winner == plan2_name:
            plan2_wins += 1
    
    # Determine overall winner
    if plan1_wins > plan2_wins:
        comparison['winner'] = plan1_name
    elif plan2_wins > plan1_wins:
        comparison['winner'] = plan2_name
    else:
        comparison['winner'] = 'tie'
    
    # Generate winner reasons
    for metric, data in comparison['metrics'].items():
        if data['winner'] != 'tie' and data['winner'] == comparison['winner']:
            comparison['winner_reasons'].append(
                f"{metric}: {data['winner']} is {abs(data['percent_difference']):.1f}% better"
            )
    
    return comparison


# ============================================================================
# CONFIGURATION AND LOGGING SETUP
# ============================================================================

# Calculate base directory dynamically (project root)
# Current structure: ProjectRoot\Core\Python\001_analyze_execution_plans.py
# So we need to go up 2 levels: Python -> Core -> ProjectRoot
base_dir = Path(__file__).parent.parent.parent

# Load the INI configuration file
ini_config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config_file = Path(__file__).parent / 'config.ini'
ini_config.read(config_file, encoding='utf-8')

# Create logs directory if it doesn't exist (relative to base_dir)
logs_dir = base_dir / ini_config['Paths']['logs_dir']
logs_dir.mkdir(parents=True, exist_ok=True)

# Create log filename with timestamp
timestamp_format = ini_config['Logging']['timestamp_format']
timestamp = datetime.now().strftime(timestamp_format)
log_filename = ini_config['Logging']['analysis_log_file']
LOG_FILE = logs_dir / f'{log_filename}_{timestamp}.log'

# Configure logging
log_format = ini_config['Logging']['log_format']
log_level = getattr(logging, ini_config['Logging']['log_level'])
log_filemode = ini_config.get('Logging', 'log_filemode', fallback='w')

# Configure logging - file only, no console output
logging.basicConfig(
    filename=str(LOG_FILE),
    level=log_level,
    format=log_format,
    filemode=log_filemode
)


def load_plan_config(ini_config: configparser.ConfigParser, base_dir: Path) -> Dict[str, Any]:
    """Load configuration file with plan file paths."""
    config_file = base_dir / ini_config['Paths']['config_dir'] / ini_config['Paths']['plan_config_file']
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
    output_dir = base_dir / ini_config['Paths']['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load plan configuration
    plan_config_file = base_dir / ini_config['Paths']['config_dir'] / ini_config['Paths']['plan_config_file']
    logging.info(f"Loading configuration from {plan_config_file}...")
    config = load_plan_config(ini_config, base_dir)

    # Validate config
    if 'planFiles' not in config or len(config['planFiles']) < 2:
        logging.error("Config file must contain at least 2 plan files in 'planFiles' array")
        sys.exit(1)

    # Filter only active plan files
    all_plan_files = config['planFiles']
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
    analysis_timestamp_format = ini_config['Logging']['analysis_timestamp_format']
    output = {
        'analysis_timestamp': datetime.now().strftime(analysis_timestamp_format),
        'config_file': str(plan_config_file),
        'plan1': plan1,
        'plan2': plan2,
        'comparison': comparison
    }

    # Write to JSON file in Output folder
    json_filename = ini_config['Files']['json_output_file']
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
    logging.info(f"\nKey Metrics:")
    logging.info(f"  Total Elapsed Time: {plan1['summary']['total_elapsed_time_ms']}ms vs {plan2['summary']['total_elapsed_time_ms']}ms")
    logging.info(f"  Total Logical Reads: {plan1['summary']['total_logical_reads']:,} vs {plan2['summary']['total_logical_reads']:,}")
    logging.info(f"  Total Estimated Cost: {plan1['summary']['total_estimated_cost']:.3f} vs {plan2['summary']['total_estimated_cost']:.3f}")
    logging.info(f"  Optimizer Timeouts: {plan1['summary']['optimizer_timeouts']} vs {plan2['summary']['optimizer_timeouts']}")
    logging.info(f"  Missing Indexes: {len(plan1['summary']['missing_indexes'])} vs {len(plan2['summary']['missing_indexes'])}")
    logging.info("\n" + "="*80)


if __name__ == '__main__':
    main()

