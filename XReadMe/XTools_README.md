# XTools - Cross-Utility Tools

Centralized utilities and helper scripts for the Advanced SQL Server Toolkit.

## Purpose

The XTools directory contains shared utilities that are used across multiple components of the toolkit. This eliminates code duplication and provides a single location for common functionality.

## Available Tools

### 1. Copy-ReadmeFiles.ps1

**Purpose:** Centralize all README files from the toolkit into the `xReadMe` directory.

**Features:**
- ✅ Automatically finds all README.md files in the toolkit
- ✅ Copies them to a centralized location with descriptive names
- ✅ Excludes common folders (node_modules, .git, etc.)
- ✅ Supports WhatIf mode for preview
- ✅ Provides detailed copy summary

**Usage:**
```powershell
# Copy all README files
.\Copy-ReadmeFiles.ps1

# Preview what would be copied
.\Copy-ReadmeFiles.ps1 -WhatIf

# Custom source and destination
.\Copy-ReadmeFiles.ps1 -SourcePath "C:\MyProject" -DestinationPath "C:\MyProject\Docs"
```

**Output Files (12 README files copied):**
1. `00_Main_Toolkit_README.md` - Main toolkit README
2. `Advanced_SQL_Code_Snippets_README.md`
3. `BabelfishCompass_Utility_README.md`
4. `Database_Normalization_Analysis_Utility_README.md`
5. `Database_Object_Dependency_Utility_README.md`
6. `DDL_Generator_Utility_README.md`
7. `Execution_Plan_Analysis_Utility_README.md`
8. `Query_Store_Analysis_Utility_README.md`
9. `Query_Store_Analysis_Utility_AI_Prompt_backup_README.md`
10. `System_Catalog_Extractor_Utility_README.md`
11. `XTools_README.md` - This file
12. `XTools_Convert_PNG_to_ICO_README.md`

**Naming Convention:**
- Main toolkit README → `00_Main_Toolkit_README.md`
- Utility READMEs → `{UtilityName}_README.md`
- Subdirectory READMEs → `{UtilityName}_{SubPath}_README.md`

---

### 2. Generate-DirectoryTree.ps1

**Purpose:** Create visual directory tree structures for documentation.

**Features:**
- ✅ Generates text-based tree visualization
- ✅ Configurable depth limit
- ✅ Exclude specific folders and file patterns
- ✅ Optional file inclusion
- ✅ Optional comment placeholders
- ✅ Save to file or display to console

**Usage:**
```powershell
# Generate tree for current directory
.\Generate-DirectoryTree.ps1

# Generate tree with max depth of 2
.\Generate-DirectoryTree.ps1 -Path "C:\MyProject" -MaxDepth 2

# Generate tree and save to file
.\Generate-DirectoryTree.ps1 -OutputFile "tree.txt"

# Generate tree with comment placeholders
.\Generate-DirectoryTree.ps1 -AddComments

# Directories only (no files)
.\Generate-DirectoryTree.ps1 -IncludeFiles:$false
```

**Example Output:**
```
MyProject/
|-- Config/
|   |-- database-config.json
|   +-- settings.json
|-- Core/
|   |-- Python/
|   |   +-- main.py
|   +-- WPF/
|       +-- Scripts/
+-- README.md
```

**Note:** The script uses ASCII characters (`|--`, `+--`) instead of Unicode box-drawing characters for maximum compatibility.

---

### 3. Convert_PNG_to_ICO/

**Purpose:** Centralized PNG to ICO conversion utility.

**Location:** `XTools/Convert_PNG_to_ICO/`

**Features:**
- ✅ Batch conversion from configuration file
- ✅ Single file conversion
- ✅ Automatic directory creation
- ✅ Comprehensive error handling
- ✅ Detailed conversion summary

**Usage:**
```powershell
cd Convert_PNG_to_ICO

# Convert all files from config
.\Convert-PngToIco.ps1 -ConvertAll

# Convert single file
.\Convert-PngToIco.ps1 -PngPath "image.png" -IcoPath "output.ico"
```

See `Convert_PNG_to_ICO/README.md` for detailed documentation.

---

## Directory Structure

```
XTools/
|-- Convert_PNG_to_ICO/            # PNG to ICO converter
|   |-- Convert-PngToIco.ps1
|   |-- convert-config.json
|   +-- README.md
|-- Copy-ReadmeFiles.ps1           # README file copier
|-- Generate-DirectoryTree.ps1     # Directory tree generator
+-- README.md                      # This file
```

---

## Benefits of Centralization

1. **Single Source of Truth** - One location for common utilities
2. **Reduced Duplication** - Eliminates duplicate code across utilities
3. **Easier Maintenance** - Update once, benefit everywhere
4. **Consistent Behavior** - Same functionality across all utilities
5. **Better Documentation** - Centralized documentation for shared tools

---

## Adding New Tools

To add a new tool to XTools:

1. Create the PowerShell script in the `XTools` directory
2. Add comprehensive help documentation (`.SYNOPSIS`, `.DESCRIPTION`, `.EXAMPLE`)
3. Include error handling and validation
4. Add color-coded console output for better UX
5. Update this README with the new tool information
6. Test thoroughly before committing

---

## Naming Conventions

- **Scripts:** Use PascalCase with verb-noun format (e.g., `Copy-ReadmeFiles.ps1`)
- **Directories:** Use PascalCase with underscores (e.g., `Convert_PNG_to_ICO`)
- **Config Files:** Use kebab-case (e.g., `convert-config.json`)

---

## Notes

- All scripts support `-WhatIf` or preview modes where applicable
- All scripts include comprehensive error handling
- All scripts provide detailed output and summaries
- All scripts use color-coded console output for clarity

---

## Version History

- **2026-03-15** - Initial creation with three utilities:
  - **Copy-ReadmeFiles.ps1** - Copies 12 README files to centralized xReadMe directory
  - **Generate-DirectoryTree.ps1** - Creates ASCII-based directory tree visualizations
  - **Convert_PNG_to_ICO/** - Centralized PNG to ICO converter with 8 configured conversions

## Statistics

- **Total Utilities:** 3
- **README Files Managed:** 12
- **PNG to ICO Conversions:** 8
- **Lines of Code:** ~500+

