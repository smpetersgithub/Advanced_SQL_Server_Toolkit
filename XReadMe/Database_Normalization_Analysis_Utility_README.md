# Database Normalization Analysis Utility

> 🐙 **Part of the [Advanced SQL Server Toolkit](https://github.com/smpetersgithub/Advanced_SQL_Server_Toolkit)**
> A collection of professional-grade utilities for SQL Server database management and analysis.

A comprehensive Windows desktop application for analyzing functional dependencies in SQL Server databases with automated normalization analysis and detailed Excel reporting.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

![Database Normalization Analysis Utility](Core/WPF/Assets/ui-screenshot.png)

## 📋 Overview

The Database Normalization Analysis Utility is a powerful tool designed to help database administrators and developers analyze functional dependencies in SQL Server tables. It automatically discovers primary and unique keys, identifies functional dependencies (including composite keys), detects transitive dependencies, and generates comprehensive Excel reports with intelligent relevance classification.

### Key Features

- 🔑 **Automatic Key Discovery** - Retrieves primary and unique keys directly from SQL Server schema
- 🔍 **Functional Dependency Analysis** - Discovers single-column and composite functional dependencies (including trivial dependencies)
- 🔗 **Transitive Dependency Detection** - Identifies dependency chains including composite transitive dependencies and 2NF violations
- 🎯 **Relevance Classification** - Automatically classifies dependencies as MINIMAL, REDUNDANT, PARTIAL_DEPENDENCY, PRIMARY_KEY, UNIQUE_KEY, or TRIVIAL
- 📊 **Excel Export** - Professional Excel reports with color-coded tabs, AutoFilter, rich text formatting, and intelligent formatting
- 💾 **Configuration Management** - Split configuration files for database credentials and table metadata
- 🗂️ **Schema Support** - Full support for schema-qualified table names (e.g., `norm.TableName`)
- 🎨 **Modern WPF UI** - Clean interface with progress indicators, real-time logging, and one-click analysis
- 🔇 **Silent Operation** - Background Python script execution without console windows

## 🚀 Quick Start

### Prerequisites

- **Windows OS** (Windows 10 or later recommended)
- **Python 3.8+** with the following packages:
  - `pyodbc`
  - `openpyxl`
- **SQL Server** with ODBC Driver 17 for SQL Server
- **PowerShell 5.1+** (included with Windows)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/smpetersgithub/Database-Normalization-Analysis-Utility.git
   cd Database-Normalization-Analysis-Utility
   ```

2. **Install Python dependencies:**
   ```bash
   pip install pyodbc openpyxl
   ```

3. **Launch the application:**
   - Double-click `Database Normalization Analysis Utility.lnk`
   - Or run: `Core\WPF\Scripts\Build\Database Normalization Analysis Utility.exe`

## 📖 Usage Guide

### Main Window Tabs

The application features a modern WPF interface with four main tabs:

#### **📊 Analysis Tab**
The Analysis tab provides a user-friendly form to set up your analysis:

#### **Table Analysis Section**
- **Table Name** - The SQL Server table to analyze (supports schema-qualified names like `norm.TableName`)
- **Columns** - List of columns to include in the analysis (one per line)

#### **Keys Section**
- **Primary Key** - Primary key column(s) (comma-separated for composite keys) - Auto-populated by "Determine Columns and Keys"
- **Unique Key** - Unique key column(s) (comma-separated for composite keys) - Auto-populated by "Determine Columns and Keys"

#### **Action Buttons**
- **💾 Save Configuration** - Saves database connection and table settings to configuration files
- **📋 Determine Columns and Keys** - Automatically retrieves columns and keys from the database schema
- **▶️ Run Full Analysis** - Executes all 4 analysis steps and generates the Excel report

#### **🔌 Connection Tab**
The Connection tab manages database connectivity:

- **Database Configuration Form**:
  - **Server Name** - SQL Server instance (e.g., `localhost` or `server,port`)
  - **Database** - Database name
  - **Username** - SQL Server authentication username
  - **Password** - SQL Server authentication password (masked for security)
- **Action Buttons**:
  - **🔌 Test Connection** - Verify database connectivity before running analysis
  - **💾 Save Configuration** - Persist connection settings to `Config/database-config.json`
- **Auto-save** - Connection details are automatically saved when modified
- **Connection Status** - Real-time feedback on connection test results

#### **⚙️ Configuration Tab**
The Configuration tab provides centralized configuration file management:

- **Configuration File Selector** - Dropdown to select which config file to view/edit
  - `config.json` - Python script settings (paths, analysis parameters, Excel formatting)
  - `database-config.json` - Database connection settings
  - `table-config.json` - Table metadata (columns, keys)
- **Live JSON Editor** - Edit configuration files with syntax highlighting
- **Auto-Save** - Changes are automatically saved after 1 second of inactivity
- **JSON Validation** - Prevents saving invalid JSON with error messages
- **Action Buttons**:
  - **🔄 Refresh** - Reload configuration from disk (discards unsaved changes)
  - **📋 Copy Path** - Copy the full file path to clipboard
  - **💾 Save Config** - Manually save the current configuration

#### **📝 Output Log Tab**
- **Real-time logging** of all operations
- **Color-coded messages** for easy reading
- **Detailed progress** for each analysis step
- **Error diagnostics** for troubleshooting

### Toolbar Buttons

| Icon | Button                  | Description                                                                         |
|------|-------------------------|-------------------------------------------------------------------------------------|
| ▶️  | **Run Full Analysis**   | Executes all 4 analysis steps in sequence and automatically opens the Excel report  |
| 📁  | **Open Output Folder**  | Opens the `Output` folder in Windows Explorer where all generated reports are saved |
| 🗑️  | **Clear Output Folder** | Deletes all files in the Output folder after user confirmation                      |

### Quick Start Workflow

1. **Configure Database Connection**
   - Fill in server name, database, username, and password
   - Enter the table name you want to analyze (e.g., `MyTable` or `norm.MyTable` for schema-qualified names)

2. **Determine Columns and Keys**
   - Click **📋 Determine Columns and Keys** to automatically retrieve columns and keys from the database schema
   - Or manually enter the columns (one per line) if you prefer

3. **Save Configuration**
   - Click **💾 Save Configuration** to save your settings for future use

4. **Run Full Analysis**
   - Click **▶️ Run Full Analysis** in the Configuration tab or toolbar
   - Watch the progress in the Output Log tab
   - The Excel report will be generated in the Output folder

### Excel Report Structure

The generated Excel report contains 4 comprehensive tabs:

| Sheet                          | Description                                  | Features                                                    |
|--------------------------------|----------------------------------------------|-------------------------------------------------------------|
| **Summary**                    | High-level overview of analysis results      | Total dependencies, transitive chains, key statistics       |
| **Functional Dependencies**    | Complete list of all functional dependencies | Color-coded by relevance, AutoFilter enabled, includes trivial dependencies |
| **Transitive Dependencies**    | Dependency chains (A → B → C)                | Shows both single-column and composite transitive dependencies, identifies 2NF violations |
| **No Functional Dependencies** | Columns with no dependencies found           | Helps identify independent attributes                       |

### Key Excel Features

- ✅ **Color-Coded Relevance** - MINIMAL (green), REDUNDANT (gray), PARTIAL_DEPENDENCY (red), PRIMARY_KEY (blue), UNIQUE_KEY (purple), TRIVIAL (yellow)
- ✅ **Rich Text Formatting** - Primary keys highlighted in red within dependency descriptions
- ✅ **Auto-Filters** - All sheets have filters enabled for easy data exploration
- ✅ **Auto-Sized Columns** - Columns automatically sized for readability (max 80 characters)
- ✅ **Frozen Headers** - Top row frozen for easy scrolling
- ✅ **Composite Key Support** - Multi-column determinants displayed clearly
- ✅ **Trivial Dependencies** - Now included in analysis for completeness
- ✅ **2NF Violation Detection** - Composite transitive dependencies identified as partial dependencies

## 📁 Project Structure

```
Database-Normalization-Analysis-Utility/
├── Core/
│   ├── Python/                          # Python analysis scripts
│   │   ├── 00_populate_columns_from_database.py
│   │   ├── 01_populate_keys_from_database.py
│   │   ├── 02_analyze_functional_dependencies.py
│   │   ├── 03_classify_dependency_relevance.py
│   │   ├── 04_generate_excel_report.py
│   │   └── config_loader.py             # Centralized configuration loader
│   ├── WPF/                             # WPF UI components
│   │   ├── Assets/                      # Icons and images
│   │   │   └── icons8-file-cabinet-64.png
│   │   └── Scripts/                     # PowerShell scripts
│   │       ├── Main.ps1
│   │       ├── MainWindow.xaml
│   │       ├── NormalizationAnalysisFunctions.ps1
│   │       └── Build/                   # Compiled EXE
│   └── SQL/                             # SQL query examples
├── Config/                              # Configuration files
│   ├── database-config.json             # Database connection settings
│   ├── table-config.json                # Table metadata (columns, keys)
│   └── config.json                      # Python script settings
├── Examples/                            # Example SQL tables for testing
│   ├── Example_1_2NF_Toothbrush.sql
│   ├── Example_2_3NF_Tournament.sql
│   ├── Example_3_BCNF_CourtBookings.sql
│   └── TABLE_REFERENCE.txt              # Reference guide for all examples
├── Output/                              # Generated Excel reports
├── Sign-PowerShellScripts.ps1           # Script signing utility
├── Verify-Signatures.ps1                # Signature verification
└── README.md
```

## 📚 Example Tables

The `Examples/` folder contains comprehensive SQL examples demonstrating various normalization forms:

| Example | Normal Form | Table Name | Description |
|---------|-------------|------------|-------------|
| **Example 1** | 2NF | `norm.NF2_Toothbrush` | Demonstrates 2NF violations with partial dependencies |
| **Example 2** | 3NF | `norm.NF3_Tournament` | Shows transitive dependencies and 3NF normalization |
| **Example 3** | BCNF | `norm.BCNF_CourtBookings` | Illustrates Boyce-Codd Normal Form violations |
| **Example 4** | 4NF | `norm.NF4_Restaurant` | Multi-valued dependencies example |
| **Example 5** | 5NF | `norm.NF5_Traveling_Salesman` | Join dependencies and 5NF decomposition |
| **Example 6** | 6NF | `norm.NF6_Employees` | Temporal data and 6NF normalization |

All examples use the `norm` schema and include detailed comments explaining the normalization concepts. See `Examples/TABLE_REFERENCE.txt` for complete details.



## 🔧 Configuration

The utility uses split configuration files for better organization:

### `Config/database-config.json` - Database Connection

```json
{
  "servername": "localhost,1433",
  "database": "MyDatabase",
  "username": "username",
  "password": "password"
}
```

### `Config/table-config.json` - Table Metadata

```json
{
  "table": "norm.MyTable",
  "columns": [
    "Column1",
    "Column2",
    "Column3"
  ],
  "primarykey": ["Column1", "Column2"],
  "uniquekey": []
}
```

### `Config/config.json` - Python Settings

```json
{
  "paths": {
    "database_config": "Config/database-config.json",
    "table_config": "Config/table-config.json",
    "output_directory": "Output",
    "functional_dependencies_output": "Output/functional_dependencies.json"
  },
  "analysis": {
    "max_determinant_size": 3,
    "progress_update_interval": 10
  },
  "database": {
    "odbc_driver": "ODBC Driver 17 for SQL Server",
    "default_schema": "dbo"
  },
  "excel": {
    "header_color": "366092",
    "relevance_colors": {
      "MINIMAL": "C6EFCE",
      "REDUNDANT": "D3D3D3",
      "PARTIAL_DEPENDENCY": "FFC7CE",
      "PRIMARY_KEY": "BDD7EE",
      "UNIQUE_KEY": "E2CFEA",
      "TRIVIAL": "FFEB9C"
    }
  }
}
```

### Configuration Fields

**Database Connection:**
- **servername** - SQL Server instance (format: `server` or `server,port`)
- **database** - Target database name
- **username** - SQL Server authentication username
- **password** - SQL Server authentication password

**Table Metadata:**
- **table** - Table name to analyze (supports schema-qualified names like `norm.TableName`)
- **columns** - Array of column names to include in analysis
- **primarykey** - Primary key column(s) (string or array for composite keys)
- **uniquekey** - Unique key column(s) (array)

**Python Settings:**
- **max_determinant_size** - Maximum number of columns in composite determinants (default: 3)
- **default_schema** - Default schema when not specified in table name (default: `dbo`)
- **relevance_colors** - Excel color codes for each dependency classification

## 🎯 Advanced Features

### Functional Dependency Analysis

The utility analyzes functional dependencies up to composite keys of size 3:

- **Single-column determinants** - A → B
- **Two-column determinants** - A, B → C
- **Three-column determinants** - A, B, C → D

A functional dependency A → B means "column A determines column B" - for each unique value of A, there is exactly one value of B.

### Transitive Dependency Detection

The utility detects both single-column and composite transitive dependency chains:

**Single-Column Transitive Dependencies:**
- **2-step chains** - A → B → C
- **3-step chains** - A → B → C → D
- **N-step chains** - Any length dependency chain

**Composite Transitive Dependencies (2NF Violations):**
- **(A, B) → C → D** - Composite key determines C, which determines D
- Identifies partial dependencies where non-prime attributes depend on part of the primary key
- Highlighted as "Composite (2NF Violation)" in the Transitive Dependencies sheet

Transitive dependencies indicate potential normalization issues (violations of 3NF for single-column, 2NF for composite).

### Relevance Classification

Each functional dependency is automatically classified:

| Classification | Description | Use Case |
|----------------|-------------|----------|
| **MINIMAL** | Smallest determinant for a dependent | Most important - focus on these |
| **REDUNDANT** | Superset of a minimal determinant | Can be ignored - implied by smaller determinant |
| **PARTIAL_DEPENDENCY** | Non-prime attribute depends on part of composite PK | **2NF VIOLATION** - requires normalization |
| **PRIMARY_KEY** | Determinant is the primary key | Expected - validates table design |
| **UNIQUE_KEY** | Determinant is a unique key | Expected - validates constraints |
| **TRIVIAL** | Determinant contains the dependent | Noise - A, B → A is always true |

### Analysis Steps

The utility executes 4 sequential steps:

1. **Step 1: Populate Keys from Database**
   - Connects to SQL Server
   - Queries `INFORMATION_SCHEMA` and `sys.indexes` for primary and unique keys
   - Supports schema-qualified table names (e.g., `norm.TableName`)
   - Updates `table-config.json` with discovered keys

2. **Step 2: Analyze Functional Dependencies**
   - Generates all column combinations (single, pairs, triples)
   - Tests each combination for functional dependencies using SQL queries
   - **Includes trivial dependencies** (e.g., {A, B} → A)
   - Outputs results to `Output/functional_dependencies.json`

3. **Step 3: Classify Dependency Relevance**
   - Loads functional dependencies from JSON
   - Applies two-pass classification algorithm
   - Identifies MINIMAL, REDUNDANT, PARTIAL_DEPENDENCY, PRIMARY_KEY, UNIQUE_KEY, and TRIVIAL
   - Adds `relevance` and `relevance_reason` fields

4. **Step 4: Generate Excel Report**
   - Creates Excel workbook with 4 tabs
   - Applies color coding, AutoFilter, and rich text formatting
   - **Highlights primary keys in red** within dependency descriptions
   - Detects and labels composite transitive dependencies as 2NF violations
   - Saves to `Output/` folder with timestamp

## 📊 Metrics Analyzed

### Functional Dependency Metrics

For each functional dependency, the utility captures:

- **Determinant** - Column(s) that determine other columns
- **Dependent** - Column that is determined
- **Determinant Size** - Number of columns in the determinant (1, 2, or 3)
- **Relevance** - Classification (MINIMAL, REDUNDANT, etc.)
- **Relevance Reason** - Explanation of the classification
- **Is Composite** - Whether the determinant has multiple columns

### Transitive Dependency Metrics

For each transitive dependency chain:

- **Chain** - Complete dependency path (e.g., A → B → C)
- **Chain Length** - Number of steps in the chain
- **Start Column** - First column in the chain
- **End Column** - Last column in the chain
- **Intermediate Columns** - Columns in the middle of the chain

## 🛠️ Troubleshooting

### Common Issues

**Issue: Python scripts fail to run**
- Ensure Python 3.8+ is installed and in PATH
- Install required packages: `pip install pyodbc openpyxl`
- Verify ODBC Driver 17 for SQL Server is installed

**Issue: Cannot connect to SQL Server**
- Verify server name and port are correct
- Check SQL Server authentication credentials
- Ensure SQL Server allows remote connections
- Verify firewall settings allow SQL Server traffic

**Issue: Excel files won't open**
- Check that Microsoft Excel is installed
- Verify Output folder permissions
- Close any open Excel files with the same name
- Check for antivirus blocking file access

**Issue: Keys not populated**
- Verify the table exists in the specified database
- Check that the username has permissions to query `INFORMATION_SCHEMA` and `sys.indexes`
- Ensure the table has a primary key or unique constraint defined
- For schema-qualified names, verify the schema exists (e.g., `norm.TableName`)

**Issue: Invalid object name error**
- Ensure you're using the correct schema name (e.g., `norm.TableName` not `dbo.norm.TableName`)
- Verify the table exists in the specified schema
- Check that the default schema in `config.json` is correct

**Issue: No functional dependencies found**
- Verify the columns list includes multiple columns
- Check that the table has data
- Ensure the columns have actual functional relationships
- Review the Output Log for SQL errors


### Python Console Windows Appearing

If you see Python console windows flashing during analysis:
- Rebuild the EXE using `Core\WPF\Scripts\Build\Create-EXE-and-Shortcut.bat`
- The compiled EXE suppresses console windows automatically

### Output Log

All operations are logged in real-time to the **Output Log** tab:
- Connection status
- SQL queries executed
- Functional dependencies discovered
- Classification results
- Excel report generation status
- Errors and warnings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test thoroughly with different SQL Server tables
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/my-feature`
7. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Scott Peters**
- GitHub: [@smpetersgithub](https://github.com/smpetersgithub)

## 🙏 Acknowledgments

- Icons provided by [Icons8](https://icons8.com)
- Built with Python, PowerShell, and WPF
- Uses pyodbc and openpyxl libraries
- Inspired by database normalization theory (Codd's Normal Forms)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on [GitHub Issues](https://github.com/smpetersgithub/Database-Normalization-Analysis-Utility/issues)
- Check existing issues for solutions
- Review the Output Log tab for detailed error information

---

**Made with ❤️ for SQL Server DBAs and Database Developers**
