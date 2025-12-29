# System Catalog Extractor Utility

A comprehensive Python-based utility for extracting SQL Server system catalog information, Dynamic Management Views (DMVs), and custom query results into a centralized SQLite database. This tool enables cross-server analysis, performance monitoring, and metadata aggregation across multiple SQL Server instances.

## Overview

The System Catalog Extractor Utility automates the collection of SQL Server metadata and performance metrics from multiple servers into a single SQLite database. It provides a unified interface for managing both standard DMV extractions and custom analytical queries, making it ideal for database administrators, performance analysts, and DevOps teams managing large SQL Server estates.

## Key Features

- **Multi-Server Support**: Extract data from multiple SQL Server instances simultaneously
- **Comprehensive DMV Coverage**: Pre-configured access to 400+ SQL Server Dynamic Management Views and Functions
- **Custom Query Framework**: Define and execute custom SQL queries with results stored in SQLite
- **Category-Based Organization**: DMVs and queries organized by functional categories (Performance Tuning, Security, Execution, etc.)
- **Flexible Activation**: Enable/disable specific DMVs or queries individually or by category
- **SQLite Output**: All data consolidated into a portable SQLite database for analysis
- **Batch Processing**: Efficient batch insertion with configurable batch sizes
- **Progress Tracking**: Real-time progress indicators during extraction
- **Comprehensive Logging**: Detailed logs for troubleshooting and audit trails
- **Interactive CLI**: User-friendly command-line interface for configuration and execution
- **Summary Statistics**: Automated generation of extraction statistics and metadata

## Architecture

### Core Components

The utility consists of four main processing scripts:

1. **Delete Tables** (`0100_delete_tables.py`): Cleans up SQLite tables before extraction
2. **ETL System Catalog** (`0200_etl_system_catalog.py`): Extracts data from configured DMVs and DMFs
3. **ETL Custom Queries** (`0300_etl_custom_queries.py`): Executes custom queries and stores results
4. **ETL Summary Statistics** (`0400_etl_summary_statistics.py`): Generates extraction metadata and statistics

### Configuration Files

- **config.ini**: Main configuration file containing paths, database settings, and ETL parameters
- **sql_server_connections.json**: Defines SQL Server instances, credentials, and connection details
- **data_management_views_config.json**: Configuration for 400+ DMVs/DMFs with activation status
- **custom_queries.json**: Custom query definitions with SQLite table mappings
- **cleanup_config.json**: Table cleanup rules for pre-extraction cleanup

## DMV Categories

DMVs and custom queries are organized into functional categories:

- **Performance Tuning**: Query statistics, execution plans, wait stats, index usage
- **Execution**: Query execution details, cached plans, sessions
- **Security**: Permissions, logins, database principals, encryption
- **Database Management**: Database files, space usage, backup history
- **Index & Statistics**: Index metadata, statistics, fragmentation
- **Transaction & Locking**: Active transactions, locks, deadlocks
- **Memory & Resource**: Memory usage, resource governor, buffer pool
- **I/O & Storage**: I/O statistics, file stats, disk usage
- **Replication & Availability**: Replication status, Always On, mirroring
- **Query Analysis**: Query plans, execution statistics, plan cache

## Workflow

### Step 1: Configure Connections

Define SQL Server instances in `sql_server_connections.json`:
- Server names and parent grouping
- Authentication credentials
- Active/inactive status for selective processing

### Step 2: Configure Extractions

**DMV Configuration:**
- Review and activate desired DMVs in `data_management_views_config.json`
- Activate/deactivate by category or individual DMV
- DMFs (Dynamic Management Functions) require parameters and are excluded from automatic extraction

**Custom Query Configuration:**
- Define custom queries in `custom_queries.json`
- Specify SQLite table names and DDL scripts
- Configure execution scope (server or database level)
- Set truncate/append behavior

### Step 3: Execute Extraction

Run the extraction process:
1. Optional: Clean up existing SQLite tables
2. Extract DMV data from all active SQL Server instances
3. Execute custom queries and store results
4. Generate summary statistics and metadata

### Step 4: Analyze Data

Query the SQLite database to:
- Compare metrics across servers
- Identify performance bottlenecks
- Track changes over time
- Generate reports and dashboards

## Output Structure

All extracted data is stored in a single SQLite database:

```
SQLite/
└── sqlite_system_catalog_output.db
    ├── sys_dm_exec_cached_plans
    ├── sys_dm_exec_query_stats
    ├── sys_databases
    ├── sys_tables
    ├── plan_sys_dm_exec_query_stats (custom)
    ├── plan_sys_dm_exec_cached_plans (custom)
    └── ... (400+ tables)
```

Each table includes metadata columns:
- `parent_name`: Server grouping identifier
- `servername`: SQL Server instance name
- `databasename`: Database name (for database-scoped queries)
- `extraction_datetime`: Timestamp of data extraction

## Custom Query Framework

Custom queries support:
- **Server-level queries**: Execute once per server (e.g., server configuration)
- **Database-level queries**: Execute for each database on each server (e.g., table statistics)
- **External SQL files**: Store complex queries in separate `.sql` files
- **Custom DDL**: Define SQLite table structures for query results
- **Truncate/Append**: Control data retention behavior

## Use Cases

- **Performance Monitoring**: Track query performance, wait stats, and resource usage across servers
- **Capacity Planning**: Analyze database growth, space usage, and resource consumption trends
- **Security Auditing**: Monitor permissions, logins, and security configurations
- **Index Optimization**: Identify missing indexes, unused indexes, and fragmentation
- **Troubleshooting**: Investigate blocking, deadlocks, and performance issues
- **Compliance Reporting**: Generate audit reports from centralized metadata
- **Environment Comparison**: Compare configurations across dev, test, and production
- **Historical Analysis**: Track changes in database metadata over time

## Requirements

- **Python 3.7+**: Required for running the utility scripts
- **pyodbc**: Python library for SQL Server connectivity
- **SQLite3**: Built-in Python library for SQLite database operations
- **SQL Server Access**: Appropriate VIEW SERVER STATE and VIEW DATABASE STATE permissions

## Best Practices

- Start with a small subset of DMVs to test the extraction process
- Review DMV descriptions to understand data being collected
- Schedule regular extractions to build historical trends
- Use categories to organize and activate related DMVs together
- Monitor SQLite database size and implement data retention policies
- Test custom queries in SSMS before adding to configuration
- Review logs after each extraction for errors or warnings
- Back up the SQLite database regularly for historical analysis

## Logging

All operations are logged with timestamps and severity levels:
- Log files stored in the `Logs/` directory
- Separate log files for each execution and script
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Detailed error messages with SQL Server connection details

---

**Note**: This utility requires appropriate SQL Server permissions to query system DMVs. Ensure service accounts have VIEW SERVER STATE and VIEW DATABASE STATE permissions.

