# DDL Generator Utility

An automated Python-based utility for generating Data Definition Language (DDL) scripts from SQL Server databases using Microsoft's `mssql-scripter` tool. This utility streamlines the process of extracting database schemas, stored procedures, views, functions, and table definitions across multiple SQL Server instances.

## Overview

The DDL Generator Utility provides a command-line interface for automating the extraction of database objects from SQL Server environments. It connects to multiple SQL Server instances, discovers databases, and generates organized DDL scripts for version control, documentation, or migration purposes.

## Key Features

- **Multi-Server Support**: Connect to and process multiple SQL Server instances simultaneously
- **Automated Discovery**: Automatically discovers all databases on configured SQL Server instances
- **Selective Processing**: Configure which databases to include or exclude from DDL generation
- **Organized Output**: Creates a hierarchical directory structure (Parent/Server/Database) for generated scripts
- **Flexible Export Options**: Export table DDL to single files or individual object scripts (views, functions, stored procedures)
- **Configuration-Driven**: JSON-based configuration for servers, databases, and export commands
- **Progress Tracking**: Real-time progress display during DDL generation
- **Comprehensive Logging**: Detailed logs for troubleshooting and audit trails
- **Interactive CLI**: User-friendly command-line interface with menu-driven options

## Architecture

### Core Components

The utility consists of three main processing scripts:

1. **Database Configuration Generator**: Connects to SQL Server instances and creates individual configuration files for each discovered database
2. **Directory Structure Creator**: Builds the output directory hierarchy based on database configurations
3. **DDL Script Executor**: Runs `mssql-scripter` commands to generate DDL scripts for active databases

### Configuration Files

- **config.ini**: Main configuration file containing paths, logging settings, and database connection parameters
- **sql_server_connections.json**: Defines SQL Server instances, credentials, and connection details
- **commands_config.json**: Configurable `mssql-scripter` commands for different export scenarios
- **database_config/*.json**: Auto-generated configuration files for each database (one per server)

## Workflow

### Step 1: Generate Database Configurations

The utility connects to each SQL Server instance defined in `sql_server_connections.json` and:
- Queries the master database for all available databases
- Creates a configuration file containing database metadata (name, state, recovery model, etc.)
- Marks databases as active/inactive based on their state
- Stores configuration in the `Config/database_config/` directory

### Step 2: Generate DDL Scripts

Once database configurations are created:
- Creates the output directory structure (`Generated_Scripts/Parent/Server/Database/`)
- Executes configured `mssql-scripter` commands for each active database
- Generates DDL scripts for tables, views, stored procedures, functions, and other objects
- Organizes output files by database and object type

## Output Structure

Generated scripts are organized hierarchically:

```
Generated_Scripts/
├── ParentName1/
│   ├── ServerName1/
│   │   ├── Database1/
│   │   │   ├── ParentName1.Database1.TablesFull.sql
│   │   │   ├── dbo.StoredProcedure1.sql
│   │   │   ├── dbo.View1.sql
│   │   │   └── ...
│   │   └── Database2/
│   │       └── ...
│   └── ServerName2/
│       └── ...
└── ParentName2/
    └── ...
```

## Export Options

The utility supports multiple export configurations:

- **Table DDL**: Exports all table definitions, schemas, user-defined types, and table types to a single file
- **Programmability Objects**: Exports views, functions, and stored procedures as individual files
- **Custom Commands**: Define additional `mssql-scripter` commands in `commands_config.json`

## Requirements

- **Python 3.7+**: Required for running the utility scripts
- **mssql-scripter**: Microsoft's command-line tool for scripting SQL Server objects
- **pyodbc**: Python library for SQL Server connectivity
- **SQL Server Access**: Appropriate permissions to read database metadata and objects

## Configuration

### SQL Server Connections

Define your SQL Server instances in `Config/sql_server_connections.json`:
- Server name and parent grouping
- Authentication credentials (SQL Server or Windows Authentication)
- Active/inactive status for selective processing

### Export Commands

Customize DDL export behavior in `Config/commands_config.json`:
- Define which object types to export
- Specify output file naming conventions
- Configure `mssql-scripter` parameters
- Enable/disable specific export commands

## Use Cases

- **Version Control**: Generate DDL scripts for tracking database schema changes in Git
- **Documentation**: Create comprehensive database documentation from live systems
- **Migration Planning**: Extract schemas for database migration projects
- **Disaster Recovery**: Maintain up-to-date DDL backups for rapid recovery
- **Environment Comparison**: Compare schemas across development, test, and production environments
- **Compliance & Audit**: Document database structures for regulatory requirements

## Logging

All operations are logged with timestamps and severity levels:
- Log files are stored in the `Logs/` directory
- Separate log files for each execution
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Detailed error messages for troubleshooting

## Best Practices

- Review and update `sql_server_connections.json` before running the utility
- Test with a small number of databases before processing entire environments
- Verify `mssql-scripter` is installed and accessible from the command line
- Review generated configurations in `Config/database_config/` before DDL generation
- Use version control to track changes in generated DDL scripts
- Schedule regular executions to maintain current schema documentation

---

**Note**: This utility requires the `mssql-scripter` tool to be installed. Install via: `pip install mssql-scripter`

