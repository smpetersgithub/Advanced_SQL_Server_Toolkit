# Advanced SQL Server Toolkit

A comprehensive collection of professional-grade utilities and tools for SQL Server database administration, migration, analysis, and development. This toolkit provides end-to-end solutions for managing SQL Server environments, from metadata extraction to database migration and performance analysis.

## 📚 Toolkit Overview

This repository contains nine specialized utilities and one reusable template, each designed to solve specific database challenges:

---

## 🛠️ Utilities

### 0. **Advanced SQL Code Snippets**
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

### 1. **BabelfishCompass Utility (ANTLR SQL Syntax Scanner)**
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

### 3. **Database Normalization Analysis Utility**
**Purpose**: Analyze functional dependencies and database normalization with automated Excel reporting

Windows desktop application for analyzing functional dependencies in SQL Server tables. Automatically discovers primary and unique keys, identifies functional dependencies (including composite keys), detects transitive dependencies, and generates comprehensive Excel reports with intelligent relevance classification.

**Key Features**:
- Automatic key discovery from SQL Server schema
- Functional dependency analysis (single and composite keys up to size 3)
- Transitive dependency detection (unlimited chain length, including 2NF violations)
- Intelligent relevance classification (MINIMAL, REDUNDANT, PARTIAL_DEPENDENCY, etc.)
- Excel export with color-coded tabs and rich text formatting
- Modern WPF UI with progress indicators and real-time logging
- Schema-qualified table name support

**Use Cases**: Database normalization analysis, schema design validation, identifying 2NF/3NF violations, educational purposes, data modeling

---

### 4. **Database Object Dependency Utility**
**Purpose**: Analyze and visualize SQL Server object dependencies with comprehensive Excel reporting

Windows desktop application for analyzing forward and reverse dependencies between SQL Server database objects. Generates detailed dependency reports showing what objects reference a given object (reverse dependencies) and what objects are referenced by a given object (forward dependencies).

**Key Features**:
- Forward and reverse dependency analysis
- Multi-object batch processing
- Excel export with formatted dependency trees
- UI mapping for stored procedures and views
- Comprehensive dependency path visualization
- Modern WPF interface with real-time logging

**Use Cases**: Impact analysis before making changes, understanding object relationships, refactoring planning, documentation, dependency mapping

---

### 5. **Execution Plan Analysis Utility**
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

### 6. **Query Store Analysis Utility**
**Purpose**: Extract and analyze SQL Server Query Store data with AI-ready performance reports

Python-based toolkit for analyzing SQL Server Query Store data, extracting execution plans, and generating AI-ready performance analysis reports. Automates the extraction of top resource-consuming queries, downloads XML execution plans, and converts them to structured JSON for AI analysis.

**Key Features**:
- Top resource-consuming query extraction from Query Store
- XML execution plan download and parsing
- Table name extraction from execution plans
- Index and statistics metadata extraction for referenced tables
- XML to JSON conversion for AI analysis
- Multiple execution plan detection for plan regression analysis
- AI-ready output with pre-calculated summaries

**Use Cases**: Query performance tuning, identifying missing indexes, detecting stale statistics, plan regression analysis, index usage pattern analysis

---

## 📂 Repository Structure

```
Advanced_SQL_Server_Toolkit/
├── Advanced_SQL_Code_Snippets/                  # SQL code snippets and utilities
├── BabelfishCompass_Utility/                    # ANTLR SQL analyzer (Babelfish Compass)
├── DDL_Generator_Utility/                       # DDL script generation
├── Database_Normalization_Analysis_Utility/     # Functional dependency and normalization analysis
├── Database_Object_Dependency_Utility/          # Object dependency analysis and visualization
├── Execution_Plan_Analysis_Utility/             # Execution plan analysis and comparison
├── Query_Store_Analysis_Utility/                # Query Store data extraction and AI analysis
├── Master_Cleanup.py                            # Master cleanup script for all utilities
└── README.md                                    # This file
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

