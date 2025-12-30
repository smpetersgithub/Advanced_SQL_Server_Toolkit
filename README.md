# Advanced SQL Server Toolkit

A comprehensive collection of professional-grade utilities and tools for SQL Server database administration, migration, analysis, and development. This toolkit provides end-to-end solutions for managing SQL Server environments, from metadata extraction to database migration and performance analysis.

## 📚 Toolkit Overview

This repository contains seven specialized utilities and one reusable template, each designed to solve specific database challenges:

---

## 🛠️ Utilities

#### 1. BabelfishCompass Utility
**Purpose:** Leverage ANTLR-based SQL parsing for advanced T-SQL analysis and code assessment

Repurposes the Babelfish Compass tool to harness its powerful ANTLR (ANother Tool for Language Recognition) parser for analyzing SQL Server code. While Babelfish Compass was designed for PostgreSQL migration assessment, this utility exploits its grammar-based parsing engine to perform deep syntax analysis, pattern detection, and code quality assessment on T-SQL codebases.

**Key Features**:
- ANTLR-Powered Parsing: Leverages grammar-based T-SQL parser to generate Abstract Syntax Trees (AST)
- Syntax Pattern Detection: Identifies complex SQL patterns, anti-patterns, and language feature usage
- Code Structure Analysis: Analyzes query complexity, nesting depth, and procedural logic patterns
- Batch Processing: Parse and analyze hundreds of SQL files automatically
- SQLite Integration: Import parsed results into SQLite for custom analysis and reporting

**Use Cases:**
- SQL code quality analysis and anti-pattern detection
- T-SQL feature inventory and complexity assessment
- Syntax validation and code standards enforcement
- Custom SQL parsing rules and pattern matching
- Code refactoring opportunity identification
- Migration assessment (not limited to Babelfish/PostgreSQL)

🔗 [Babelfish Compass – SQL Server compatibility analysis tool](https://github.com/babelfish-for-postgresql/babelfish_compass)    
🔗 [ANTLR](https://www.antlr.org/)

---

### 2. **DDL Generator Utility**
**Purpose**: Automated DDL script generation from SQL Server databases

Extracts Data Definition Language (DDL) scripts from multiple SQL Server instances using Microsoft's mssql-scripter. Organizes output by server, database, and object type for version control and documentation.

**Key Features**:
- Multi-server DDL extraction
- Automated database discovery
- Selective database processing (active/inactive)
- Hierarchical directory organization
- Configurable export options (tables, views, procedures, functions)

**Use Cases**: Version control, documentation, disaster recovery, environment comparison, migration planning

🔗 [mssql-scripter](https://github.com/microsoft/mssql-scripter)

---

### 3. **System Catalog Extractor Utility**
**Purpose**: Extract SQL Server system catalog, DMVs, and custom queries into SQLite

Consolidates metadata and performance metrics from multiple SQL Server instances into a centralized SQLite database. Provides access to 400+ Dynamic Management Views (DMVs) with category-based organization.

**Key Features**:
- 400+ pre-configured DMVs/DMFs
- Custom query framework for analytical queries
- Category-based organization (Performance, Security, Execution, etc.)
- Multi-server support with batch processing
- SQLite output for cross-server analysis

**Use Cases**: Performance monitoring, capacity planning, security auditing, index optimization, compliance reporting

---

### 4. **Execution Plan Analysis Utility**
**Purpose**: Analyze and compare SQL Server execution plans with Excel reporting

Windows desktop application for detailed execution plan analysis. Compares plans side-by-side, identifies performance bottlenecks, and generates comprehensive Excel reports with color-coded insights.

**Key Features**:
- Side-by-side execution plan comparison
- Individual plan analysis with detailed metrics
- Excel export with color-coded formatting
- Cardinality estimation warnings (10x errors)
- Configuration management and batch processing

**Use Cases**: Query performance tuning, execution plan comparison, cardinality estimation analysis, performance troubleshooting

---

### 5. **Advanced SQL Code Snippets**
**Purpose**: Curated collection of advanced SQL Server code snippets and utilities

Production-ready SQL scripts and SSMS code snippets for complex database challenges including data profiling, dependency analysis, data transformation, and validation.

**Key Features**:
- Data profiling and quality analysis
- Foreign key path analysis and dependency mapping
- Pivot operations and Excel integration
- Table validation and comparison
- SSMS snippet integration

**Use Cases**: Data profiling, dependency analysis, impact analysis, data validation, development automation

---

### 6. **WPF PowerShell Template**
**Purpose**: Reusable template for building WPF applications with PowerShell

Foundation for creating professional desktop utilities with modern graphical interfaces, tabbed navigation, and JSON-based configuration. Not a utility itself, but a template for building custom tools.

**Key Features**:
- WPF application framework with STA mode
- Tabbed navigation and DataGrid integration
- JSON configuration management
- Modular XAML and PowerShell organization
- Executable creation support

**Use Cases**: Building custom database administration tools, deployment utilities, monitoring dashboards, configuration managers

---

## 📂 Repository Structure

```
Advanced_SQL_Server_Toolkit/
├── BabelfishCompass_Utility/           # ANTLR SQL analyzer
├── DDL_Generator_Utility/              # DDL script generation
├── Database_Migration_Utility/         # Database migration orchestration
├── System_Catalog_Extractor_Utility/   # DMV and metadata extraction
├── Execution_Plan_Analysis_Utility/    # Execution plan analysis
├── Advanced_SQL_Code_Snippets/         # SQL code snippets
├── WPF_Powershell_Template/            # WPF application template
└── README.md                           # This file
```

Each utility contains its own detailed README with installation instructions, configuration guides, and usage examples.

---

## 🔧 General Requirements

Most utilities require:
- **Python 3.7+** with various packages (see individual utility READMEs)
- **SQL Server** access with appropriate permissions
- **Windows OS** (for WPF-based utilities)
- **PowerShell 5.1+** (for PowerShell-based utilities)

Specific requirements vary by utility. Consult each utility's README for detailed prerequisites.

---

## 📖 Getting Started

1. **Choose a utility** based on your needs (see descriptions above)
2. **Navigate to the utility directory** and read its README
3. **Install prerequisites** as specified in the utility's documentation
4. **Configure** the utility using provided configuration files
5. **Run** the utility following the usage instructions

---

## 🤝 Contributing

These utilities represent production-tested solutions for real-world database challenges. Feel free to adapt and extend them for your specific needs.

---

## 📧 Contact

**Author**: Scott Peters
**Website**: https://advancedsqlpuzzles.com

---

**Note**: Each utility is self-contained with its own configuration, dependencies, and documentation. Refer to individual README files for detailed information.

