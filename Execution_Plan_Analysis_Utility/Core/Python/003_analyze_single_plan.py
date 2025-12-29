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
        
        # Get query text (full and preview)
        statement_text = stmt.get('StatementText', '')
        statement_text_preview = statement_text
        if len(statement_text_preview) > 200:
            statement_text_preview = statement_text_preview[:200] + '...'
        
        # Get runtime statistics if available
        runtime_info = stmt.find('.//sp:QueryTimeStats', ns)
        elapsed_time = 0
        cpu_time = 0
        
        if runtime_info is not None:
            elapsed_time = int(runtime_info.get('ElapsedTime', 0))
            cpu_time = int(runtime_info.get('CpuTime', 0))
        
        # Get I/O statistics
        io_stats = stmt.find('.//sp:RunTimeCountersPerThread', ns)
        logical_reads = 0
        
        if io_stats is not None:
            logical_reads = int(io_stats.get('ActualLogicalReads', 0))
        
        # Check for optimizer timeout
        if early_abort_reason == 'TimeOut':
            result['summary']['optimizer_timeouts'] += 1
        
        # Get operators with detailed node information
        operators = []
        node_details = []
        node_id = 0

        for op in stmt.findall('.//sp:RelOp', ns):
            node_id += 1
            op_type = op.get('LogicalOp')
            op_cost = float(op.get('EstimatedTotalSubtreeCost', 0))
            op_rows = float(op.get('EstimateRows', 0))

            # Basic operator info (for backward compatibility)
            operators.append({
                'type': op_type,
                'estimated_cost': op_cost,
                'estimated_rows': op_rows
            })

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

            # Check for other operations with objects (Nested Loops, Hash Match, etc.)
            if not table_index:
                # Check for Update/Insert/Delete
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
        
        # Get missing indexes for this statement
        statement_missing_indexes = []
        missing_index_groups = stmt.findall('.//sp:MissingIndexGroup', ns)
        for group in missing_index_groups:
            impact = float(group.get('Impact', 0))
            missing_index = group.find('.//sp:MissingIndex', ns)
            if missing_index is not None:
                database = missing_index.get('Database', '')
                schema = missing_index.get('Schema', '')
                table = missing_index.get('Table', '')

                # Get columns
                equality_columns = []
                inequality_columns = []
                include_columns = []

                for col_group in missing_index.findall('.//sp:ColumnGroup', ns):
                    usage = col_group.get('Usage')
                    columns = [col.get('Name') for col in col_group.findall('.//sp:Column', ns)]

                    if usage == 'EQUALITY':
                        equality_columns = columns
                    elif usage == 'INEQUALITY':
                        inequality_columns = columns
                    elif usage == 'INCLUDE':
                        include_columns = columns

                missing_index_info = {
                    'impact_percent': impact,
                    'database': database,
                    'schema': schema,
                    'table': table,
                    'equality_columns': equality_columns,
                    'inequality_columns': inequality_columns,
                    'include_columns': include_columns
                }

                # Add to statement
                statement_missing_indexes.append(missing_index_info)

                # Add to summary only if not already present (deduplicate by table and columns)
                is_duplicate = False
                for existing_mi in result['summary']['missing_indexes']:
                    if (existing_mi['database'] == database and
                        existing_mi['schema'] == schema and
                        existing_mi['table'] == table and
                        existing_mi['equality_columns'] == equality_columns and
                        existing_mi['inequality_columns'] == inequality_columns and
                        existing_mi['include_columns'] == include_columns):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    result['summary']['missing_indexes'].append(missing_index_info)
        
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
        
        # Get actual rows and executions if available
        actual_rows = 0
        actual_executions = 0
        wait_time_ms = 0

        runtime_counters = stmt.find('.//sp:RunTimeCountersPerThread', ns)
        if runtime_counters is not None:
            actual_rows = int(runtime_counters.get('ActualRows', 0))
            actual_executions = int(runtime_counters.get('ActualExecutions', 0))

        # Add statement to results
        statement_data = {
            'statement_id': statement_id,
            'statement_type': statement_type,
            'statement_text': statement_text,
            'statement_text_preview': statement_text_preview,
            'estimated_cost': statement_cost,
            'optimizer_level': optimizer_level,
            'early_abort_reason': early_abort_reason,
            'estimated_rows': estimated_rows,
            'elapsed_time_ms': elapsed_time,
            'cpu_time_ms': cpu_time,
            'wait_time_ms': wait_time_ms,
            'logical_reads': logical_reads,
            'actual_rows': actual_rows,
            'actual_executions': actual_executions,
            'missing_indexes': statement_missing_indexes,
            'operators': operators,
            'node_details': node_details
        }

        result['statements'].append(statement_data)

        # Update summary
        result['summary']['total_estimated_cost'] += statement_cost
        result['summary']['total_elapsed_time_ms'] += elapsed_time
        result['summary']['total_cpu_time_ms'] += cpu_time
        result['summary']['total_logical_reads'] += logical_reads
        result['summary']['total_statements'] += 1

    # Calculate total wait time
    result['summary']['total_wait_time_ms'] = (
        result['summary']['total_elapsed_time_ms'] -
        result['summary']['total_cpu_time_ms']
    )

    # Count total warnings
    result['summary']['total_warnings'] = len(result['warnings'])

    return result


# ============================================================================
# CONFIGURATION AND LOGGING SETUP
# ============================================================================

# Calculate base directory dynamically (project root)
# Current structure: ProjectRoot\Core\Python\003_analyze_single_plan.py
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
log_filename = ini_config['Logging']['single_plan_analysis_log_file']
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
    plan_config_file = base_dir / ini_config['Paths']['config_dir'] / ini_config['Paths']['plan_config_file']
    logging.info(f"Loading configuration from {plan_config_file}...")
    config = load_plan_config(ini_config, base_dir)

    # Get active plan files
    all_plan_files = config['planFiles']
    plan_files = [plan for plan in all_plan_files if plan.get('active', False)]

    logging.info(f"Total plan files in config: {len(all_plan_files)}")
    logging.info(f"Active plan files: {len(plan_files)}")

    if len(plan_files) == 0:
        logging.error("No active plan files found in configuration!")
        logging.info("Please mark at least one plan as active in the configuration.")
        sys.exit(1)

    # Analyze each plan individually
    results = []

    for idx, plan_info in enumerate(plan_files, 1):
        plan_name = plan_info['name']
        plan_path = plan_info['path']
        plan_description = plan_info.get('description', '')

        logging.info(f"\nPlan {idx}: {plan_name}")
        logging.info(f"  Path: {plan_path}")
        logging.info(f"  Description: {plan_description}")

        logging.info(f"\nParsing {plan_name}...")
        plan_data = parse_execution_plan(plan_path)
        plan_data['config_name'] = plan_name  # Add the config name
        plan_data['description'] = plan_description

        results.append(plan_data)

    # Create output directory if it doesn't exist
    output_dir = base_dir / ini_config['Paths']['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results to JSON
    json_filename = ini_config['Files']['json_single_plan_output_file']
    output_file = output_dir / json_filename

    # Create output structure
    output_data = {
        'analysis_timestamp': datetime.now().strftime(ini_config['Logging']['analysis_timestamp_format']),
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
    logging.info(f"\nTotal plans analyzed: {len(results)}")

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


if __name__ == '__main__':
    main()


