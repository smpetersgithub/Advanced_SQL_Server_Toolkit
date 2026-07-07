# Changes Applied — Database Access Conformance Analysis Standardization

**Applied:** 2026-06-19 11:20:17 (CDT)
**Reference Report:** `AI_Output_Database_Access_Conformance_Analysis.md`

---

## Summary

All 8 standardization recommendations from the conformance analysis report have been fully applied across the four SQL Server utilities:

- Database_Normalization_Analysis_Utility (DNAU)
- Database_Object_Dependency_Utility (DODU)
- Query_Store_Analysis_Utility (QSAU)
- DDL_Generator_Utility (no changes required — already used a different config pattern by design)

---

## Changes Applied

### 1. Standardize `database_config` Key Path in config.json
- **DNAU** `Config/config.json` — no structural change needed (already in `paths`)
- **DODU** `Config/config.json` — moved `database_config` from `files` section → `paths` section
- **QSAU** `Config/config.json` — moved `database_config` from `paths.config.database_config` → `paths.database_config` (top-level under `paths`)

### 2. Make Logging Configurable (DNAU and DODU)
- **DNAU** `Config/config.json` — added `log_level`, `log_format`, `timestamp_format` keys to existing `logging` section
- **DODU** `Config/config.json` — added new `logging` section with `log_level`, `log_format`, `timestamp_format`
- **DNAU** `Core/Python/config_loader.py` — updated `setup_logging()` to read `log_level`, `log_format`, `timestamp_format` from `config['logging']` instead of hardcoded values
- **DODU** `Core/Python/config_loader.py` — updated `setup_logging()` to read `log_level`, `log_format`, `timestamp_format` from `config['logging']` instead of hardcoded values

### 3. Standardize ODBC Driver Source for QSAU
- **QSAU** `Config/config.json` — added `database` section with `"odbc_driver": "auto"`
- **QSAU** `Core/Python/config_loader.py` — updated `get_odbc_driver()` to read from `config['database']['odbc_driver']` (was reading from `database-config.json`), consistent with DNAU/DODU

### 4. Add `windows_auth` to QSAU Database Config Files
- **QSAU** `Config/database-config.json` — added `"windows_auth": false`
- **QSAU** `Config/database-config-demo.json` — added `"windows_auth": false`; also fixed pre-existing bug: `"server"` key renamed to `"servername"` to match expected schema

### 5. Add Configurable Connection Timeout to All Utilities
- **DNAU** `Config/config.json` — added `"connection_timeout": 10` to `database` section
- **DODU** `Config/config.json` — added `"connection_timeout": 10` to `database` section
- **QSAU** `Config/config.json` — added `"connection_timeout": 10` to new `database` section
- **DNAU** `Core/Python/config_loader.py` — added `get_connection_timeout()` method
- **DODU** `Core/Python/config_loader.py` — added `get_connection_timeout()` method; also fixed `get_database_config_file()` to read from `paths` (was `files`)
- **QSAU** `Core/Python/config_loader.py` — added `get_connection_timeout()` method
- **All pyodbc.connect() calls updated** (10 files total):
  - DNAU: `00_populate_columns_from_database.py`, `01_populate_keys_from_database.py`, `02_analyze_functional_dependencies.py`
  - DODU: `02_generate_dependency_report_reverse_ui_lookup.py`, `04_generate_dependency_report_reverse.py`, `05_generate_dependency_report_forward.py`
  - QSAU: `01_extract_query_store_data.py`, `02_extract_xml_execution_plans.py`, `04_extract_index_and_statistics_for_tables.py`, `06_lookup_query_by_id.py`

### 6. Standardize QSAU Error Exit to `sys.exit(1)`
- Added `import sys` to QSAU scripts 01, 02, 03, 04, 05
- Replaced bare `raise` in `main()` exception handler with `sys.exit(1)` in all five scripts
- Note: `raise` statements in `06_lookup_query_by_id.py` helper function `execute_lookup_query()` were intentionally left as-is (they propagate to callers)

### 7. Fix DODU PowerShell `server` → `servername` Bug (Critical)
- **DODU** `Core/WPF/Scripts/DatabaseObjectDependencyFunctions.ps1` — fixed `Save-DatabaseConfiguration` function: `server = $server` → `servername = $server`
- This was a critical bug: saved config files were written with key `server` but all readers (Python ConfigLoader, `Load-DatabaseConfiguration`) expected key `servername`, causing failures when reloading saved configs
- File re-signed with Authenticode certificate after edit ✅

### 8. Align DNAU and DODU `Main.ps1` Quality with QSAU
- **DNAU** `Core/WPF/Scripts/Main.ps1` — added `#Requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`
- **DODU** `Core/WPF/Scripts/Main.ps1` — added `#Requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`
- Both files re-signed with Authenticode certificate after edit ✅

---

## PowerShell Script Re-Signing

The following code-signed `.ps1` files were modified and re-signed using each utility's `Sign-PowerShellScripts.ps1`:

| File | Utility | Signature Status |
|------|---------|-----------------|
| `Core/WPF/Scripts/Main.ps1` | DNAU | Valid ✅ |
| `Core/WPF/Scripts/Main.ps1` | DODU | Valid ✅ |
| `Core/WPF/Scripts/DatabaseObjectDependencyFunctions.ps1` | DODU | Valid ✅ |

Certificate: `CN=PowerShell Code Signing - Advanced SQL Server Toolkit`
Thumbprint: `98E50BCC472EA19F2E935023EF73CA8DFACF8D66`
Expires: 2031-03-05

---

## Files Modified

| File | Utility | Change Type |
|------|---------|-------------|
| `Config/config.json` | DNAU | Added `connection_timeout`, `log_level`, `log_format`, `timestamp_format` |
| `Config/config.json` | DODU | Moved `database_config` to `paths`; added `connection_timeout`; added `logging` section |
| `Config/config.json` | QSAU | Moved `database_config` to `paths`; added `database` section |
| `Config/database-config.json` | QSAU | Added `windows_auth` |
| `Config/database-config-demo.json` | QSAU | Fixed `server`→`servername`; added `windows_auth` |
| `Core/Python/config_loader.py` | DNAU | Configurable `setup_logging()`; added `get_connection_timeout()` |
| `Core/Python/config_loader.py` | DODU | Fixed `get_database_config_file()` path; configurable `setup_logging()`; added `get_connection_timeout()` |
| `Core/Python/config_loader.py` | QSAU | Fixed `_load_database_config()` path; updated `get_odbc_driver()`; added `get_connection_timeout()` |
| `Core/Python/00_populate_columns_from_database.py` | DNAU | Added connection timeout |
| `Core/Python/01_populate_keys_from_database.py` | DNAU | Added connection timeout |
| `Core/Python/02_analyze_functional_dependencies.py` | DNAU | Added connection timeout |
| `Core/Python/02_generate_dependency_report_reverse_ui_lookup.py` | DODU | Added connection timeout |
| `Core/Python/04_generate_dependency_report_reverse.py` | DODU | Added connection timeout |
| `Core/Python/05_generate_dependency_report_forward.py` | DODU | Added connection timeout |
| `Core/Python/01_extract_query_store_data.py` | QSAU | Added `import sys`, `sys.exit(1)`, connection timeout |
| `Core/Python/02_extract_xml_execution_plans.py` | QSAU | Added `import sys`, `sys.exit(1)`, connection timeout |
| `Core/Python/03_extract_table_names_from_xml_plans.py` | QSAU | Added `import sys`, `sys.exit(1)` |
| `Core/Python/04_extract_index_and_statistics_for_tables.py` | QSAU | Added `import sys`, `sys.exit(1)`, connection timeout |
| `Core/Python/05_create_json_execution_plans.py` | QSAU | Added `import sys`, `sys.exit(1)` |
| `Core/WPF/Scripts/Main.ps1` | DNAU | Added `#Requires`, `Set-StrictMode`, `$ErrorActionPreference` |
| `Core/WPF/Scripts/Main.ps1` | DODU | Added `#Requires`, `Set-StrictMode`, `$ErrorActionPreference` |
| `Core/WPF/Scripts/DatabaseObjectDependencyFunctions.ps1` | DODU | Fixed `server`→`servername` bug |
