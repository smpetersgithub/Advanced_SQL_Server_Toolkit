"""
Shared Execution Plan Parser Module

This module provides common functionality for parsing SQL Server execution plans.
It is used by both the comparison analysis and single plan analysis scripts.

Author: SQL Server Toolkit
Date: 2026-03-20
"""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional


# ============================================================================
# CONSTANTS
# ============================================================================

# Text preview and column limits
STATEMENT_TEXT_PREVIEW_LENGTH = 100
MAX_OUTPUT_COLUMNS = 10

# Default SQL Server namespace (fallback)
DEFAULT_NAMESPACE = 'http://schemas.microsoft.com/sqlserver/2004/07/showplan'

# Supported encodings for SQL Server execution plan files
SUPPORTED_ENCODINGS = ['utf-16', 'utf-8', 'utf-8-sig', 'latin-1']


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float with fallback to default.

    Args:
        value: Value to convert (can be None, string, number, etc.)
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value) if value not in (None, '', 'None') else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int with fallback to default.

    Args:
        value: Value to convert (can be None, string, number, etc.)
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value) if value not in (None, '', 'None') else default
    except (ValueError, TypeError):
        return default


def extract_namespace(root: ET.Element) -> Dict[str, str]:
    """
    Extract namespace from XML root element dynamically.

    Args:
        root: XML root element

    Returns:
        Dictionary with namespace mapping
    """
    # Try to extract namespace from root tag
    if root.tag.startswith('{'):
        namespace = root.tag[1:root.tag.index('}')]
        return {'sp': namespace}

    # Fallback to default SQL Server namespace
    return {'sp': DEFAULT_NAMESPACE}


def strip_namespace(tag: str) -> str:
    """
    Remove namespace from XML tag.

    Args:
        tag: XML tag with namespace

    Returns:
        Tag without namespace
    """
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag


def deduplicate_missing_indexes(indexes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate missing indexes based on key fields.

    Args:
        indexes: List of missing index dictionaries

    Returns:
        Deduplicated list of indexes
    """
    seen = set()
    unique_indexes = []

    for idx in indexes:
        # Create a unique key from database, schema, table, and columns
        key = (
            idx.get('database', ''),
            idx.get('schema', ''),
            idx.get('table', ''),
            tuple(idx.get('equality_columns', [])),
            tuple(idx.get('inequality_columns', [])),
            tuple(idx.get('include_columns', []))
        )

        if key not in seen:
            seen.add(key)
            unique_indexes.append(idx)

    return unique_indexes


def calculate_percentage_difference(val1: float, val2: float) -> Optional[float]:
    """
    Calculate percentage difference between two values.

    Args:
        val1: First value
        val2: Second value (baseline)

    Returns:
        Percentage difference or None if baseline is zero
    """
    if val2 == 0:
        if val1 == 0:
            return 0.0
        return None  # Infinite difference

    return ((val1 - val2) / val2) * 100


def is_parallel(value: Optional[str]) -> str:
    """
    Convert parallel attribute to Yes/No.

    Args:
        value: Parallel attribute value from XML

    Returns:
        'Yes' if parallel, 'No' otherwise
    """
    return 'Yes' if value in ('1', 'true', 'True') else 'No'


def extract_object_name(obj, include_database: bool = True) -> str:
    """
    Extract fully qualified object name from XML object element.

    Args:
        obj: XML object element
        include_database: Whether to include database name

    Returns:
        Fully qualified object name
    """
    if obj is None:
        return ''

    database = obj.get('Database', '')
    schema = obj.get('Schema', '')
    table = obj.get('Table', '')
    index = obj.get('Index', '')

    # Build name based on what's available
    if index:
        if include_database and database:
            return f"[{database}].[{schema}].[{table}].[{index}]"
        return f"[{schema}].[{table}].[{index}]"
    else:
        if include_database and database:
            return f"[{database}].[{schema}].[{table}]"
        return f"[{schema}].[{table}]"


def extract_parameters(stmt: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract parameter information from execution plan statement.

    Args:
        stmt: Statement XML element
        ns: Namespace dictionary

    Returns:
        List of parameter dictionaries with name, compiled value, runtime value, and data type
    """
    parameters = []

    # Find ParameterList in QueryPlan
    query_plan = stmt.find('.//sp:QueryPlan', ns)
    if query_plan is None:
        return parameters

    param_list = query_plan.find('.//sp:ParameterList', ns)
    if param_list is None:
        return parameters

    # Extract each parameter
    for col_ref in param_list.findall('.//sp:ColumnReference', ns):
        param_name = col_ref.get('Column', '')
        compiled_value = col_ref.get('ParameterCompiledValue', '')
        runtime_value = col_ref.get('ParameterRuntimeValue', '')
        data_type = col_ref.get('ParameterDataType', '')

        # Only add if we have a parameter name
        if param_name:
            parameters.append({
                'parameter_name': param_name,
                'compiled_value': compiled_value if compiled_value else 'N/A',
                'runtime_value': runtime_value if runtime_value else compiled_value if compiled_value else 'N/A',
                'data_type': data_type if data_type else 'Unknown'
            })

    return parameters




# ============================================================================
# MAIN PARSING FUNCTION
# ============================================================================

def parse_execution_plan(file_path: str) -> Dict[str, Any]:
    """
    Parse SQL Server execution plan XML file and extract statistics.

    Args:
        file_path: Path to the .sqlplan XML file

    Returns:
        Dictionary containing parsed execution plan data

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file cannot be decoded or parsed
    """
    # Validate file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Execution plan file not found: {file_path}")

    # Try different encodings for SQL Server execution plans
    xml_content = None
    used_encoding = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                xml_content = f.read()
            used_encoding = encoding
            logging.debug(f"Successfully decoded {file_path} using {encoding}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if xml_content is None:
        raise ValueError(f"Could not decode file {file_path} with any supported encoding: {SUPPORTED_ENCODINGS}")

    logging.info(f"Successfully decoded {file_path} using {used_encoding} encoding")

    # Parse XML
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML in {file_path}: {e}")

    # Extract namespace dynamically
    ns = extract_namespace(root)
    logging.debug(f"Using namespace: {ns['sp']}")

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

    # Validate that we found statements
    if not statements:
        logging.warning(f"No statements found in execution plan: {file_path}")
        logging.warning("The execution plan may be empty or have an unexpected structure")

    for stmt in statements:
        statement_id = stmt.get('StatementId')
        statement_type = stmt.get('StatementType')
        statement_cost = safe_float(stmt.get('StatementSubTreeCost'), 0.0)
        optimizer_level = stmt.get('StatementOptmLevel')
        early_abort_reason = stmt.get('StatementOptmEarlyAbortReason')
        estimated_rows = safe_float(stmt.get('StatementEstRows'), 0.0)

        # Get query text (truncated for readability)
        statement_text = stmt.get('StatementText', '')
        statement_text_preview = statement_text[:STATEMENT_TEXT_PREVIEW_LENGTH].replace('\n', ' ').replace('\r', ' ')

        # Extract parameters
        parameters = extract_parameters(stmt, ns)

        # Get query time stats
        query_time_stats = stmt.find('.//sp:QueryTimeStats', ns)
        cpu_time = 0
        elapsed_time = 0
        if query_time_stats is not None:
            cpu_time = safe_int(query_time_stats.get('CpuTime'), 0)
            elapsed_time = safe_int(query_time_stats.get('ElapsedTime'), 0)

        # Get runtime counters (logical reads, actual rows, etc.)
        runtime_counters = stmt.find('.//sp:RunTimeCountersPerThread[@Thread="0"]', ns)
        logical_reads = 0
        actual_rows = 0
        actual_executions = 0

        if runtime_counters is not None:
            logical_reads = safe_int(runtime_counters.get('ActualLogicalReads'), 0)
            actual_rows = safe_int(runtime_counters.get('ActualRows'), 0)
            actual_executions = safe_int(runtime_counters.get('ActualExecutions'), 0)

        # Check for missing indexes
        missing_indexes = []
        missing_index_groups = stmt.findall('.//sp:MissingIndexGroup', ns)
        for group in missing_index_groups:
            impact = safe_float(group.get('Impact'), 0.0)
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
                warning_type = strip_namespace(child.tag)

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
            op_cost = safe_float(op.get('EstimatedTotalSubtreeCost'), 0.0)
            op_rows = safe_float(op.get('EstimateRows'), 0.0)

            # Detailed node information
            node_info = {
                'statement_id': statement_id,
                'node_id': node_id,
                'node_type': op_type,
                'physical_op': op.get('PhysicalOp', ''),
                'logical_op': op_type,
                'estimated_cost': op_cost,
                'estimated_rows': op_rows,
                'estimated_cpu_cost': safe_float(op.get('EstimateCPU'), 0.0),
                'estimated_io_cost': safe_float(op.get('EstimateIO'), 0.0),
                'estimated_executions': safe_float(op.get('EstimateExecutions'), 1.0),
                'parallel': is_parallel(op.get('Parallel'))
            }

            # Get actual runtime information if available
            runtime_info = op.find('.//sp:RunTimeInformation/sp:RunTimeCountersPerThread', ns)
            if runtime_info is not None:
                node_info['actual_rows'] = safe_int(runtime_info.get('ActualRows'), 0)
                node_info['actual_executions'] = safe_int(runtime_info.get('ActualExecutions'), 0)
                node_info['actual_rebinds'] = safe_int(runtime_info.get('ActualRebinds'), 0)
                node_info['actual_rewinds'] = safe_int(runtime_info.get('ActualRewinds'), 0)
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
                table_index = extract_object_name(obj)

                # Get seek predicates from ScalarString attribute
                seek_preds = index_scan.findall('.//sp:SeekPredicates//sp:ScalarOperator[@ScalarString]', ns)
                if seek_preds:
                    pred_list = [pred.get('ScalarString', '') for pred in seek_preds if pred.get('ScalarString')]
                    if pred_list:  # Only join if we have predicates
                        seek_predicates = ' AND '.join(pred_list)

                # Get predicate (filter) from ScalarString attribute
                pred_elem = index_scan.find('.//sp:Predicate/sp:ScalarOperator[@ScalarString]', ns)
                if pred_elem is not None:
                    predicate = pred_elem.get('ScalarString', '')

            # Check for Table Scan
            table_scan = op.find('.//sp:TableScan', ns)
            if table_scan is not None:
                obj = table_scan.find('.//sp:Object', ns)
                table_index = extract_object_name(obj)

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
                        table_index = extract_object_name(obj)
                        if table_index:
                            break

            # Get output list
            output_elem = op.find('.//sp:OutputList', ns)
            if output_elem is not None:
                columns = []
                for col_ref in output_elem.findall('.//sp:ColumnReference', ns):
                    col_name = col_ref.get('Column', '')
                    if col_name:
                        columns.append(col_name)
                output_list = ', '.join(columns[:MAX_OUTPUT_COLUMNS])  # Limit to first N columns
                if len(columns) > MAX_OUTPUT_COLUMNS:
                    output_list += '...'

            # Check for warnings at node level
            warnings_elem = op.find('.//sp:Warnings', ns)
            warnings_text = ''
            if warnings_elem is not None:
                warning_types = []
                for child in warnings_elem:
                    warning_type = strip_namespace(child.tag)
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
            'wait_time_ms': max(0, elapsed_time - cpu_time),  # Prevent negative wait time
            'logical_reads': logical_reads,
            'actual_rows': actual_rows,
            'actual_executions': actual_executions,
            'parameters': parameters,
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

    # Deduplicate missing indexes
    result['summary']['missing_indexes'] = deduplicate_missing_indexes(
        result['summary']['missing_indexes']
    )

    # Calculate total wait time
    result['summary']['total_wait_time_ms'] = max(0,
        result['summary']['total_elapsed_time_ms'] -
        result['summary']['total_cpu_time_ms']
    )

    # Count total warnings
    result['summary']['total_warnings'] = len(result['warnings'])

    return result


