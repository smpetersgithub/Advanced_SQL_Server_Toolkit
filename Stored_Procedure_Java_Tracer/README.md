# Stored Procedure Java Tracer

**Author:** Scott Peters
**Date:** January 29, 2026

---

## Overview

The Stored Procedure Java Tracer is an automated analysis tool that traces the complete execution path from SQL Server stored procedures through Java DAO (Data Access Object) layers to UI components (Handlers, Actions, JSPs). This utility provides comprehensive mapping and dependency analysis for Java-based applications that interact with SQL Server databases.

## Purpose

**Trace the complete data flow path:**
- **Stored Procedures** → **DAO Classes** → **UI Handlers/Actions** → **JSP Pages**

This tool helps developers and architects understand:
- Which UI components call which stored procedures
- How data flows through the application layers
- Dependencies between database objects
- Impact analysis for database or code changes

---

## Key Features

### 1. **Complete UI Mapping**
- Scans Java source code to identify DAO classes and their stored procedure calls
- Maps DAO classes to UI components (Handlers, Actions, JSPs)
- Generates comprehensive CSV and Excel reports showing the complete call chain
- Supports multiple stored procedure invocation patterns in Java code

### 2. **Database Dependency Analysis**
- Connects to SQL Server to analyze object dependencies
- Identifies tables, views, and functions used by stored procedures
- Generates JSON reports with complete dependency trees
- Helps understand the impact of schema changes

### 3. **Final UI Mappings**
- Combines UI mapping and dependency data
- Creates consolidated reports for specific stored procedures
- Provides actionable insights for code refactoring and migration

### 4. **Automated Workflow**
- Single-click execution of all analysis steps
- Detailed logging for troubleshooting
- Clean, organized output files
- Built-in cleanup utilities

---

## Directory Structure

```
Stored_Procedure_Java_Tracer/
├── CLI - Stored Procedure Java Tracer.py    # Main CLI interface
├── Config/
│   ├── database-config.json                 # SQL Server connection settings
│   ├── Stored Procedures Input.txt          # List of procedures to analyze
│   └── cleanup_config.json                  # Cleanup configuration
├── Core/
│   ├── Python/
│   │   ├── config.ini                       # Main configuration file
│   │   ├── ascii_art.txt                    # CLI ASCII art
│   │   ├── 01_extract_complete_ui_mapping.py
│   │   ├── 02_generate_dependency_report.py
│   │   └── 03_create_final_ui_mappings.py
│   ├── SQL/
│   │   └── Determine Object Dependencies.sql
│   └── Logs/                                # Execution logs (auto-generated)
├── Output/                                  # Generated reports (auto-generated)
└── README.md                                # This file
```

---

## Prerequisites

### Software Requirements
- **Python 3.7+** with the following packages:
  - `pyodbc` - SQL Server connectivity
  - `openpyxl` - Excel file generation
  - `configparser` - Configuration management
- **SQL Server** - Access to the target database
- **ODBC Driver 17 for SQL Server** (or compatible version)
- **Java Source Code** - Access to the Java application source files

### Access Requirements
- Read access to Java source code directories
- SQL Server database credentials with permissions to:
  - Execute stored procedures
  - Query system catalog views (sys.sql_expression_dependencies)

---

## Configuration

### 1. Database Configuration
Edit `Config/database-config.json`:
```json
{
  "server": "your-server,port",
  "username": "your-username",
  "password": "your-password"
}
```

### 2. Main Configuration
Edit `Core/Python/config.ini`:

**Java Source Directories:**
```ini
java_source_dir_1 = C:\path\to\java\source\main
java_source_dir_2 = C:\path\to\java\common
```

**Project Paths** (auto-configured):
```ini
project_base_dir = C:\Advanced_SQL_Server_Toolkit\Stored_Procedure_Java_Tracer
output_dir = C:\Advanced_SQL_Server_Toolkit\Stored_Procedure_Java_Tracer\Output
log_dir = C:\Advanced_SQL_Server_Toolkit\Stored_Procedure_Java_Tracer\Core\Logs
```

### 3. Stored Procedures Input
Edit `Config/Stored Procedures Input.txt` - add one stored procedure name per line:
```
prGetCustomerData
prUpdateOrderStatus
prGenerateReport
```

---

## Usage

### Quick Start

1. **Launch the CLI:**
   ```
   python "CLI - Stored Procedure Java Tracer.py"
   ```

2. **Configure your inputs:**
   - Option 2: Edit Stored Procedures Input
   - Add the stored procedures you want to analyze

3. **Run the analysis:**
   - Option 1: Run Complete Analysis
   - Wait for all three steps to complete

4. **View results:**
   - Option 3: Open Output Folder
   - Review the generated CSV/Excel/JSON files

---

## Output Files

### Generated Reports

All output files are saved to the `Output/` directory:

#### 1. Complete_StoredProc_to_UI_Mapping.csv / .xlsx
**Complete mapping from stored procedures to UI components**

Columns:
- `Stored Procedure` - Name of the stored procedure
- `DAO Class` - Java DAO class that calls the procedure
- `DAO File` - Full path to the DAO source file
- `UI Component` - UI Handler, Action, or JSP that uses the DAO
- `UI Type` - Type of UI component (Handler, Action, JSP, etc.)
- `UI File` - Full path to the UI source file

**Use Case:** Understand which UI screens are affected by stored procedure changes

#### 2. Object_Dependency_List.json
**Database object dependencies in JSON format**

Structure:
```json
{
  "prGetCustomerData": {
    "dependencies": [
      "dbo.Customers",
      "dbo.Orders",
      "dbo.fnGetCustomerStatus"
    ]
  }
}
```

**Use Case:** Impact analysis for database schema changes

#### 3. UI_Mappings_Final.csv
**Consolidated report for specific stored procedures**

Combines UI mapping and dependency data for the procedures listed in `Stored Procedures Input.txt`

**Use Case:** Focused analysis for migration or refactoring projects

---

## How It Works

### Step 1: Extract Complete UI Mapping

**Scans Java source code to build the call chain:**

1. **Scan DAO Files:**
   - Searches for Java classes ending with `DAO`
   - Identifies stored procedure calls using multiple patterns:
     - `prepareCall("{call dbo.procedureName")`
     - `getCallableStatement("{call procedureName")`
     - `execute("procedureName")`
     - `super(ds, "procedureName")`
     - `SQL = "dbo.procedureName"`

2. **Scan UI Files:**
   - Searches for Handlers, Actions, and JSP files
   - Identifies DAO usage patterns:
     - `import` statements for DAO classes
     - `new DaoClassName()` instantiations

3. **Build Mapping:**
   - Creates relationships: Stored Proc → DAO → UI Component
   - Generates CSV and Excel reports

### Step 2: Generate Dependency Report

**Analyzes database object dependencies:**

1. **Connect to SQL Server:**
   - Uses credentials from `database-config.json`
   - Queries system catalog views

2. **Execute Dependency Query:**
   - Runs `Determine Object Dependencies.sql`
   - Identifies tables, views, functions used by each stored procedure

3. **Generate JSON Report:**
   - Creates structured dependency data
   - Saves to `Object_Dependency_List.json`

### Step 3: Create Final UI Mappings

**Combines data for targeted analysis:**

1. **Read Input:**
   - Loads stored procedures from `Stored Procedures Input.txt`

2. **Filter and Combine:**
   - Extracts relevant mappings from Step 1
   - Merges with dependency data from Step 2

3. **Generate Final Report:**
   - Creates `UI_Mappings_Final.csv`
   - Provides focused view for specific procedures

---

## Supported Java Patterns

### DAO Stored Procedure Invocation Patterns

The tool recognizes these common patterns for calling stored procedures in Java:

```java
// Pattern 1: prepareCall
CallableStatement cs = connection.prepareCall("{call dbo.prGetData}");

// Pattern 2: getCallableStatement
CallableStatement cs = getCallableStatement("{call prGetData}");

// Pattern 3: execute method
execute("prGetData");

// Pattern 4: super constructor
super(ds, "prGetData");

// Pattern 5: SQL constant
private static final String SQL = "dbo.prGetData";
```

### UI to DAO Patterns

```java
// Import pattern
import com.example.dao.CustomerDAO;

// Instantiation pattern
CustomerDAO dao = new CustomerDAO();
```

---

## Troubleshooting

### Common Issues

**1. "Configuration file not found"**
- Ensure `Core/Python/config.ini` exists
- Check file paths are correct

**2. "Database connection failed"**
- Verify SQL Server is accessible
- Check credentials in `Config/database-config.json`
- Ensure ODBC Driver 17 is installed

**3. "No stored procedures found"**
- Verify Java source directories in `config.ini`
- Check that DAO files use supported invocation patterns
- Review logs in `Core/Logs/` for details

**4. "Permission denied" errors**
- Ensure SQL Server user has permissions to query system views
- Check file system permissions for Output and Logs directories

### Viewing Logs

All scripts generate detailed logs in `Core/Logs/`:
- `log_01_extract_complete_ui_mapping_YYYYMMDD_HHMMSS.log`
- `log_02_generate_dependency_report_YYYYMMDD_HHMMSS.log`
- `log_03_create_final_ui_mappings_YYYYMMDD_HHMMSS.log`

Use **Option 4: Open Logs Folder** from the CLI menu to access logs.

---

## Use Cases

### 1. **Database Migration Planning**
- Identify all UI components affected by stored procedure changes
- Understand dependencies before migrating to a new database platform
- Estimate migration effort based on complexity of call chains

### 2. **Code Refactoring**
- Find all usages of a stored procedure across the application
- Identify candidates for consolidation or elimination
- Plan refactoring with complete impact visibility

### 3. **Impact Analysis**
- Assess the impact of changing a database table or view
- Trace from database objects → stored procedures → DAOs → UI
- Communicate changes to stakeholders with clear reports

### 4. **Documentation**
- Generate up-to-date documentation of application architecture
- Visualize data flow through application layers
- Onboard new developers with clear mapping reports

### 5. **Performance Optimization**
- Identify frequently-called stored procedures
- Find redundant DAO calls in UI components
- Optimize based on actual usage patterns

---

## Tips and Best Practices

### Configuration
- **Keep database credentials secure** - Use environment variables or secure vaults in production
- **Update Java source paths** when project structure changes
- **Backup config files** before making changes

### Analysis
- **Start with a small set** of stored procedures to validate configuration
- **Review logs** after each run to catch issues early
- **Use Excel reports** for easier filtering and analysis

### Maintenance
- **Run cleanup regularly** to free disk space
- **Archive important reports** before running cleanup
- **Update the tool** when Java code patterns change

---

## Advanced Configuration

### Adding Custom Java Patterns

To support additional stored procedure invocation patterns, edit:
`Core/Python/01_extract_complete_ui_mapping.py`

Add new regex patterns:
```python
sp_pattern6 = re.compile(r'yourCustomPattern\s*\(\s*["\']([a-zA-Z0-9_]+)["\']', re.IGNORECASE)
```

### Customizing Output Format

Modify the CSV/Excel generation code in:
- `01_extract_complete_ui_mapping.py` - UI mapping format
- `03_create_final_ui_mappings.py` - Final report format

---

## Version History

**v1.0 - January 29, 2026**
- Initial release
- Complete UI mapping functionality
- Database dependency analysis
- Automated workflow with CLI interface
- Excel and JSON report generation

---

## Support

For issues, questions, or feature requests, contact:
**Scott Peters**

---

## License

Internal tool for use within the organization.

---

## Acknowledgments

This utility was developed to streamline database migration and code refactoring projects by providing automated tracing of stored procedure usage through Java application layers.

