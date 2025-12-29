# Database Migration Utility

A comprehensive Python-based utility for orchestrating database migrations from SQL Server to target database platforms. This tool automates the extraction of DDL, transformation of database objects, and deployment to target systems through a workflow-driven approach managed by a Firebird configuration database.

## Overview

The Database Migration Utility provides an end-to-end solution for migrating SQL Server databases to other platforms. It uses a Firebird database as a central configuration repository to store migration workflows, PowerShell scripts, and Python scripts that orchestrate the migration process. The utility supports phased migrations with separate steps for DDL generation, transformation, and deployment.

## Key Features

- **Workflow-Driven Architecture**: Multi-step migration workflows stored in Firebird configuration database
- **Multi-Database Support**: Migrate multiple databases from source to target systems
- **Phased Migration**: Separate phases for discovery, DDL generation, transformation, and deployment
- **Database Blacklisting**: Exclude specific databases from migration process
- **DDL Generation**: Automated extraction of SQL Server DDL using mssql-scripter
- **Object-Level Deployment**: Deploy tables, table elements (FKs, indexes), and programmability objects separately
- **PowerShell Integration**: Execute PowerShell scripts dynamically from Firebird database
- **Python Script Execution**: Run Python scripts stored in the configuration database
- **Interactive CLI**: User-friendly menu-driven interface with color-coded output
- **Comprehensive Logging**: Detailed logs for troubleshooting and audit trails
- **Error Handling**: Continue-on-error options for resilient workflow execution

## Architecture

### Core Components

1. **Menu Interface** (`Menu - Database Migration Utility.py`): Interactive CLI for selecting migration operations
2. **Script Executor** (`script_executer.py`): Core engine that executes workflows, PowerShell scripts, and Python scripts from Firebird
3. **Firebird Configuration Database**: Central repository storing workflows, scripts, and migration metadata
4. **Utility Scripts**: Collection of PowerShell and Python scripts for specific migration tasks
5. **Configuration Files**: INI-based configuration for database connections and execution parameters

### Execution Modes

The script executor supports three execution modes:

- **Workflow Mode**: Executes a sequence of PowerShell scripts defined in workflow views
- **Master Mode**: Executes PowerShell scripts from master views for specific operations
- **Script Mode**: Executes individual Python scripts stored in the database

### Firebird Configuration Database

The Firebird database (`DATABASE_MIGRATION_UTILITY_CONFIGURATION_DATABASE.FDB`) stores:

- **Workflows**: Multi-step migration workflows with execution sequences
- **Master Views**: Collections of PowerShell commands for specific operations
- **Python Scripts**: Python code stored as text for dynamic execution
- **SQL Scripts**: SQL commands for database operations
- **Server Configurations**: Source and target server connection details
- **Database Metadata**: Information about databases to migrate

## Migration Workflow

### Step 1: Discover Databases

**Command**: `Databases`

- Connects to source SQL Server instances
- Queries for all available databases
- Imports database list into `IMPORT_DATABASE_INFORMATION` table
- Allows blacklisting of databases to exclude from migration

### Step 2: Generate DDL (Optional)

**Command**: `DDL`

- Generates DDL scripts from source SQL Server databases
- Uses mssql-scripter to extract object definitions
- Stores DDL in `Generated_Scripts/` directory
- Useful for review before migration

### Step 3: Build (Pre-Deployment)

**Command**: `Build`

- Executes pre-deployment operations
- Transforms DDL for target platform compatibility
- Creates deployment scripts
- Prepares SQL scripts for execution
- Validates object dependencies

### Step 4: Deploy Objects

**Deploy Tables**: `Tables`
- Deploys table DDL to target system
- Creates table structures without constraints

**Deploy Table Elements**: `Elements`
- Deploys foreign keys, indexes, and constraints
- Applied after table creation

**Deploy Programmability**: `All`
- Deploys views, stored procedures, and functions
- Applied after tables and elements

### Step 5: Full Migration (Testing)

**Command**: `Full`

- Executes complete build and deploy in one operation
- Useful for testing migration process
- Combines all deployment steps

### Cleanup

**Command**: `Delete`

- Removes generated folders and temporary files
- Cleans up `Generated_Scripts/`, `Logs/`, `Output_Files/`, `SQL_Scripts/`

## Directory Structure

```
Database_Migration_Utility/
├── Core/
│   ├── Databases/
│   │   └── DATABASE_MIGRATION_UTILITY_CONFIGURATION_DATABASE.FDB
│   ├── Utilities/
│   │   └── [Migration utility scripts]
│   ├── script_executer.py          # Core execution engine
│   ├── script_executer_config.ini  # Configuration file
│   └── ascii_art.txt               # CLI banner
├── Generated_Scripts/              # DDL output from mssql-scripter
├── Logs/                           # Execution logs
├── Output_Files/                   # Migration output files
├── SQL_Scripts/                    # Generated SQL scripts
├── Menu - Database Migration Utility.py  # Interactive CLI
└── Reset_Database_Migration_Utility (Drop Folders).py
```

## Configuration

### script_executer_config.ini

Key configuration sections:

**[Paths]**
- `LOG_DIR`: Directory for log files
- `DB_PATH`: Path to Firebird configuration database

**[Database]**
- `DB_USER`: Firebird username (default: SYSDBA)
- `DB_PASSWORD`: Firebird password
- `DB_CHARSET`: Character set (UTF8)

**[Logging]**
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Log message format
- `LOG_FILE_MODE`: Append or overwrite logs

**[PowerShell]**
- `EXECUTION_POLICY`: PowerShell execution policy (Bypass, Unrestricted, etc.)
- `DELETE_TEMP_SCRIPTS`: Clean up temporary PowerShell files

**[Execution]**
- `CONTINUE_ON_ERROR`: Continue workflow on script failure
- `SCRIPT_TIMEOUT`: Maximum execution time for scripts

**[Database_Queries]**
- Table and column names for workflows, master views, and scripts

## Requirements

### Software Dependencies

1. **Python 3.7+**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install colorama chardet firebird-driver psycopg2-binary
   ```

2. **Firebird Database 5.0+**
   - Download: https://firebird.org/
   - Or use PowerShell to download:
   ```powershell
   New-Item -ItemType Directory C:\Temp -Force | Out-Null
   curl.exe -L "https://sourceforge.net/projects/firebird/files/v5.0.3/Firebird-5.0.3.1683-0-windows-x64.exe/download" `
     -o "C:\Temp\Firebird-5.0.3.1683-0-windows-x64.exe"
   ```

3. **mssql-scripter**
   - Microsoft's command-line tool for scripting SQL Server objects
   - Installation: https://github.com/microsoft/mssql-scripter

### Python Packages

- **colorama**: Terminal color output for CLI
- **chardet**: Character encoding detection
- **firebird-driver**: Firebird database connectivity
- **psycopg2-binary**: PostgreSQL connectivity (for target databases)

## Usage

### Interactive Menu

Run the menu interface:
```bash
python "Menu - Database Migration Utility.py"
```

Menu options:
- **Databases**: Import source database list
- **DDL**: Generate DDL scripts only
- **Build**: Execute pre-deployment build process
- **Tables**: Deploy table structures
- **Elements**: Deploy foreign keys and indexes
- **All**: Deploy views, procedures, and functions
- **Full**: Complete build and deploy (testing)
- **Delete**: Clean up generated folders
- **Exit**: Quit the utility

### Command-Line Execution

Execute specific workflows directly:
```bash
python Core/script_executer.py <execution_id> <execution_type>
```

Examples:
```bash
# Execute workflow ID 1
python Core/script_executer.py 1 workflow

# Execute master view ID 5
python Core/script_executer.py 5 master

# Execute Python script ID 3
python Core/script_executer.py 3 script
```

## Use Cases

- **SQL Server to PostgreSQL Migration**: Migrate databases from SQL Server to PostgreSQL/Babelfish
- **Platform Modernization**: Move legacy SQL Server databases to cloud platforms
- **Database Consolidation**: Merge multiple SQL Server instances into a single target
- **Environment Cloning**: Replicate database structures across environments
- **Schema Comparison**: Generate DDL for comparison and analysis
- **Disaster Recovery**: Create portable DDL backups for recovery scenarios

## Best Practices

1. **Test First**: Use the `Full` command on test databases before production migration
2. **Review DDL**: Generate DDL separately to review transformations
3. **Blacklist Carefully**: Exclude system databases and non-migratable databases
4. **Monitor Logs**: Check logs after each step for errors and warnings
5. **Phased Deployment**: Deploy tables, elements, and programmability separately
6. **Backup Configuration**: Regularly backup the Firebird configuration database
7. **Version Control**: Store generated DDL in version control for tracking
8. **Validate Connections**: Test source and target connections before migration

## Troubleshooting

### Common Issues

**Firebird Connection Errors**
- Verify Firebird service is running
- Check username/password in `script_executer_config.ini`
- Ensure database file path is correct

**PowerShell Execution Errors**
- Verify execution policy allows script execution
- Check PowerShell version compatibility
- Review logs for specific script errors

**mssql-scripter Not Found**
- Ensure mssql-scripter is installed and in PATH
- Test mssql-scripter from command line

**Migration Failures**
- Review logs in `Logs/` directory
- Check source/target connectivity
- Verify database permissions

## Logging

All operations are logged with detailed information:
- Log files stored in `Logs/` directory
- Configurable log levels for verbosity control
- Separate logs for each execution
- Includes timestamps, execution IDs, and error details

## Limitations

- Requires manual configuration of Firebird database workflows
- PowerShell scripts are Windows-specific
- mssql-scripter required for DDL generation
- Some SQL Server features may require manual transformation
- Target platform compatibility depends on DDL transformation scripts

---

**Note**: This utility requires proper configuration of the Firebird database with migration workflows and scripts. Consult documentation for setting up workflows and configuring source/target connections.

