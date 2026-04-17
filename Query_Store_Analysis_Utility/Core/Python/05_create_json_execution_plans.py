"""
Analyze All XML Execution Plans and Save as JSON

This script processes all XML execution plan files from the XML_Execution_Plans directory,
analyzes each one using the same parsing logic, and saves individual JSON files
to the json_execution_plans directory.
"""

import logging
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from config_loader import ConfigLoader


def parse_execution_plan(file_path: str) -> Optional[Dict[str, Any]]:
    """Parse SQL Server execution plan XML file and extract comprehensive plan data.

    Extracts:
    - Statement details (type, cost, optimizer level, query text)
    - Operators and detailed node information (physical/logical ops, costs, rows)
    - Runtime statistics (elapsed time, CPU time, I/O stats, actual rows)
    - Warnings (all types including optimizer timeouts)
    - Missing index recommendations
    - Statistics usage information
    - Table/index references with predicates and seek conditions

    Supports multiple statement types: StmtSimple, StmtCond, StmtCursor, StmtReceive.

    Args:
        file_path: Path to the XML execution plan file

    Returns:
        Dictionary containing parsed execution plan data, or None if parsing fails

    Raises:
        FileNotFoundError: If file doesn't exist
        ET.ParseError: If XML is malformed
        ValueError: If file path is invalid
    """
    # Validate input
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"XML file not found: {file_path}")

    if not file_path_obj.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Parse XML - Note: For untrusted XML, consider using defusedxml
    # Current implementation is safe for trusted SQL Server execution plans
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ET.ParseError(f"Failed to parse XML file {file_path_obj.name}: {str(e)}")

    # Define namespace
    ns = {'sp': 'http://schemas.microsoft.com/sqlserver/2004/07/showplan'}

    plan_name = Path(file_path).stem

    # Extract object_name, query_id, and plan_id from filename
    # Format: <ObjectName>_QueryID_<id>_PlanID_<id>
    parts = plan_name.split('_')
    object_name = 'Unknown'
    query_id = None
    plan_id = None

    # Find QueryID and PlanID in the filename
    for i, part in enumerate(parts):
        if part == 'QueryID' and i + 1 < len(parts):
            query_id = parts[i + 1]
        elif part == 'PlanID' and i + 1 < len(parts):
            plan_id = parts[i + 1]

    # Extract object name (everything before _QueryID_)
    if 'QueryID' in parts:
        query_id_index = parts.index('QueryID')
        object_name = '_'.join(parts[:query_id_index])

    result = {
        'plan_name': plan_name,
        'object_name': object_name,
        'query_id': query_id,
        'plan_id': plan_id,
        'file_path': str(file_path),
        'statements': [],
        'warnings': [],
        'statistics': [],
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

    # Find all statements - SQL Server execution plans can contain multiple statement types:
    # StmtSimple (SELECT, INSERT, UPDATE, DELETE), StmtCond (IF...THEN...ELSE),
    # StmtCursor, StmtReceive, etc.
    statements = root.findall('.//sp:StmtSimple', ns)
    statements.extend(root.findall('.//sp:StmtCond', ns))
    statements.extend(root.findall('.//sp:StmtCursor', ns))
    statements.extend(root.findall('.//sp:StmtReceive', ns))

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

        # Extract optimizer statistics usage
        query_plan = stmt.find('.//sp:QueryPlan', ns)
        if query_plan is not None:
            stats_usage = query_plan.find('.//sp:OptimizerStatsUsage', ns)
            if stats_usage is not None:
                for stat_info in stats_usage.findall('.//sp:StatisticsInfo', ns):
                    stat_entry = {
                        'statement_id': statement_id,
                        'database': stat_info.get('Database', ''),
                        'schema': stat_info.get('Schema', ''),
                        'table': stat_info.get('Table', ''),
                        'statistics': stat_info.get('Statistics', ''),
                        'modification_count': int(stat_info.get('ModificationCount', 0)),
                        'sampling_percent': float(stat_info.get('SamplingPercent', 0)),
                        'last_update': stat_info.get('LastUpdate', '')
                    }
                    result['statistics'].append(stat_entry)

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


def main():
    """Main execution function."""
    # Initialize config loader
    config = ConfigLoader()

    # Setup logging - returns the log file path
    log_file = config.setup_logging('script_05')

    # Get logger instance
    logger = logging.getLogger(__name__)

    # Get active report settings
    active_report_key, report_settings = config.get_active_report_settings()

    # Build report-specific paths
    project_root = config.get_project_root()
    report_base_dir = project_root / report_settings['output']['base_dir']
    xml_plans_dir = report_base_dir / report_settings['output']['xml_plans_dir']
    json_output_dir = report_base_dir / report_settings['output']['json_plans_dir']
    xml_extension = config.get_xml_file_extension()

    logger.info("=" * 70)
    logger.info(f"{report_settings['name']} - Analyze XML Execution Plans")
    logger.info("=" * 70)
    logger.info(f"Active Report: {active_report_key}")
    logger.info(f"XML Plans Directory: {xml_plans_dir}")
    logger.info(f"JSON Output Directory: {json_output_dir}")
    logger.info(f"XML File Extension: {xml_extension}")

    try:
        # Validate XML plans directory exists
        if not xml_plans_dir.exists():
            logger.error(f"XML plans directory not found: {xml_plans_dir}")
            raise FileNotFoundError(f"XML plans directory not found: {xml_plans_dir}")

        if not xml_plans_dir.is_dir():
            logger.error(f"Path is not a directory: {xml_plans_dir}")
            raise ValueError(f"Path is not a directory: {xml_plans_dir}")

        # Create output directory if it doesn't exist
        json_output_dir.mkdir(parents=True, exist_ok=True)

        # Get all XML plan files
        xml_files = list(xml_plans_dir.glob(f"*{xml_extension}"))

        if not xml_files:
            logger.warning(f"No {xml_extension} files found in {xml_plans_dir}")
            return

        logger.info(f"Found {len(xml_files)} XML execution plan files to process")

        # Process each XML file
        success_count = 0
        failed_count = 0

        for idx, xml_file in enumerate(xml_files, 1):
            logger.info(f"[{idx}/{len(xml_files)}] Processing: {xml_file.name}")

            try:
                # Parse the execution plan
                plan_data = parse_execution_plan(str(xml_file))

                if plan_data is None:
                    logger.error(f"  ✗ Failed to parse {xml_file.name}")
                    failed_count += 1
                    continue

                # Add analysis timestamp
                plan_data['analysis_timestamp'] = datetime.now().isoformat()

                # Create JSON filename (same as XML but with .json extension)
                json_filename = xml_file.stem + ".json"
                json_output_path = json_output_dir / json_filename

                # Save to JSON
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(plan_data, f, indent=2)

                logger.info(f"  ✓ Saved to: {json_filename}")
                logger.info(f"    Statements: {plan_data['summary']['total_statements']}")
                logger.info(f"    Estimated Cost: {plan_data['summary']['total_estimated_cost']:.3f}")
                logger.info(f"    Logical Reads: {plan_data['summary']['total_logical_reads']:,}")
                logger.info(f"    Warnings: {plan_data['summary']['total_warnings']}")
                logger.info(f"    Missing Indexes: {len(plan_data['summary']['missing_indexes'])}")

                success_count += 1

            except ET.ParseError as e:
                logger.error(f"  ✗ XML parsing error in {xml_file.name}: {str(e)}")
                failed_count += 1
            except Exception as e:
                logger.error(f"  ✗ Error processing {xml_file.name}: {str(e)}", exc_info=True)
                failed_count += 1

        logger.info("=" * 70)
        logger.info(f"Analysis completed!")
        logger.info(f"  Total plans: {len(xml_files)}")
        logger.info(f"  Successfully processed: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"JSON files saved to: {json_output_dir}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()


