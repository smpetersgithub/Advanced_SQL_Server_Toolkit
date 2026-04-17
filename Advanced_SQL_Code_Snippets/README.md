# Advanced SQL Code Snippets

A curated collection of advanced SQL Server code snippets and utilities designed to solve complex database challenges and automate common development tasks.

## Overview

This directory contains production-ready SQL scripts and SSMS code snippets that address advanced database scenarios including data profiling, dependency analysis, data transformation, and validation. Each snippet is designed to be reusable, well-documented, and immediately applicable to real-world database projects.

## Categories

### Miscellaneous Utilities

A collection of versatile SQL utilities for data analysis, transformation, and validation:

- **Data Profiling**: Automated column-level data profiling that analyzes data quality metrics including null counts, empty strings, and pattern detection across table columns
- **Date Calculations**: Utilities for calculating date differences in various formats (character-based and table-based outputs)
- **Excel Integration**: Tools for generating Excel-compatible concatenated strings from SQL query results
- **Pivot Operations**: Automated pivot table generation with dynamic column creation and aggregation functions
- **Table Validation**: Comprehensive table comparison and validation scripts for identifying differences between datasets

### Object Dependencies

Advanced dependency analysis tools for understanding and navigating complex database relationships:

- **Foreign Key Path Analysis**: Discover and visualize foreign key relationship paths between tables
- **Object Dependency Mapping**: Trace object dependencies across databases to understand how views, stored procedures, and functions are interconnected
- **Dependency Path Discovery**: Identify both forward and reverse dependency chains for impact analysis and refactoring

## File Formats

Each utility is provided in two formats:

- **`.sql` files**: Standalone SQL scripts that can be executed directly in SSMS or any SQL Server client
- **`.snippet` files**: SSMS code snippets that can be imported into SQL Server Management Studio for quick access via IntelliSense

## Usage

### Running SQL Scripts

1. Open the `.sql` file in SQL Server Management Studio
2. Review and modify any database names or parameters as needed
3. Execute the script against your target database

### Installing SSMS Snippets

1. In SSMS, go to **Tools** → **Code Snippets Manager**
2. Select **SQL** as the language
3. Click **Import** and navigate to the `.snippet` files
4. Once imported, access snippets by typing the snippet name and pressing `Tab` or `Ctrl+K, Ctrl+X`

## Key Features

- **Production-Ready**: All scripts are tested and designed for use in production environments
- **Well-Documented**: Each script includes detailed comments explaining purpose, parameters, and usage
- **Dynamic SQL**: Many utilities use dynamic SQL generation for maximum flexibility
- **Error Handling**: Robust error handling and validation built into stored procedures
- **Reusable**: Designed as templates that can be easily adapted to specific use cases

## Requirements

- SQL Server 2016 or later (some scripts may work on earlier versions)
- Appropriate database permissions for the operations being performed
- SQL Server Management Studio (for `.snippet` files)

## Best Practices

- Always review and test scripts in a development environment before running in production
- Modify database names, schema names, and table names to match your environment
- Review dynamic SQL output before execution when applicable
- Consider performance implications when running profiling or dependency analysis on large databases

## Contributing

These snippets represent common patterns and solutions for advanced SQL Server development. Feel free to adapt and extend them for your specific needs.

---

**Note**: Some scripts reference the `WideWorldImporters` sample database for demonstration purposes. Replace with your own database name as needed.

