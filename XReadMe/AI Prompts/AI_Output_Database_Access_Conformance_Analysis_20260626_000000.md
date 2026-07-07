# Database Access Conformance Analysis
**Generated:** 2026-06-26  
**Scope:** Read-only analysis — no code was modified.

---

## 1. Executive Summary

Four utilities were analyzed to determine whether they access SQL Server databases using a consistent approach:

| Utility | Python DB Access | PowerShell/WPF UI | Config Structure |
|---|---|---|---|
| Database_Normalization_Analysis_Utility | `pyodbc` | WPF + `SqlClient` | Flat single-server |
| Database_Object_Dependency_Utility | `pyodbc` | WPF + `SqlClient` | Flat single-server |
| Query_Store_Analysis_Utility | `pyodbc` | WPF + `SqlClient` | Flat single-server (multi-file) |
| DDL_Generator_Utility | `pyodbc` | **CLI only** (no WPF) | **Nested multi-server array** |

**Overall verdict:** The core SQL Server connection mechanics (ODBC driver, connection string format, Windows/SQL authentication toggle, `TrustServerCertificate`) are highly consistent across all four utilities. However, meaningful inconsistencies exist in connection string method naming, configuration file structure, ConfigLoader API shape, error handling completeness, logging setup, PowerShell project-root resolution, and WPF connection disposal patterns.

---

## 2. Utility Architecture Overview

### 2.1 Database_Normalization_Analysis_Utility

| Layer | Technology |
|---|---|
| UI | WPF (PowerShell-hosted) |
| Python backend | `00_populate_columns_from_database.py`, `01_populate_keys_from_database.py`, `02_analyze_functional_dependencies.py`, `03_classify_dependency_relevance.py`, `04_generate_excel_report.py` |
| Config loader | `Core/Python/config_loader.py` |
| Database config | `Config/database-config.json` (flat single-server) |
| Primary config | `Config/config.json` + `Config/table-config.json` |
| DB connection | `pyodbc` (Python), `System.Data.SqlClient` (PS1) |

### 2.2 Database_Object_Dependency_Utility

| Layer | Technology |
|---|---|
| UI | WPF (PowerShell-hosted) |
| Python backend | `00_run_all_scripts.py`, `01_extract_complete_ui_mapping.py` through `07_format_excel_file.py` |
| Config loader | `Core/Python/config_loader.py` |
| Database config | `Config/database-config.json` (flat single-server) |
| Primary config | `Config/config.json` |
| DB connection | `pyodbc` (Python), `System.Data.SqlClient` (PS1) |

### 2.3 Query_Store_Analysis_Utility

| Layer | Technology |
|---|---|
| UI | WPF (PowerShell-hosted) |
| Python backend | `01_extract_query_store_data.py` through `06_lookup_query_by_id.py` + `run_all_scripts.py` |
| Config loader | `Core/Python/config_loader.py` |
| Database config | `Config/database-config.json` (flat single-server) |
| Primary config | `Config/config.json` + `Config/reports-config.json` + `Config/active-report-config.json` |
| DB connection | `pyodbc` (Python), `System.Data.SqlClient` (PS1) |

### 2.4 DDL_Generator_Utility

| Layer | Technology |
|---|---|
| UI | **CLI only** (`CLI - DDL Generator Utility.py`) — no WPF |
| Python backend | `01_generate_database_configs.py`, `02_create_directory_structure.py`, `03_execute_mssql_scripter.py` |
| Config loader | `Core/Python/config_loader.py` |
| Database config | `Config/database-config.json` (**nested multi-server array**) + dynamically generated per-server files under `Config/database_config/` |
| Primary config | `Config/config.json` |
| DB connection | `pyodbc` (Python) |

---

## 3. Detailed Comparison by Category

---

### 3.1 Connection Methods

#### Python Layer

All four utilities use `pyodbc` as the SQL Server connection library.

| Utility | Python Connection Method |
|---|---|
| Normalization | `pyodbc.connect(connection_string, timeout=config.get_connection_timeout())` |
| Dependency | `pyodbc.connect(connection_string, timeout=config.get_connection_timeout())` |
| Query Store | `pyodbc.connect(connection_string, timeout=connection_timeout)` |
| DDL Generator | `pyodbc.connect(conn_str, timeout=config.get_connection_timeout())` |

**Consistent:** All four use `pyodbc.connect()` with a timeout argument. All read the timeout from `config.json` via the ConfigLoader (`get_connection_timeout()`, default = 10 seconds).

#### PowerShell / WPF Layer

The three utilities with WPF UIs (Normalization, Dependency, Query Store) all use `System.Data.SqlClient.SqlConnection` to test the database connection from the UI.

```powershell
# Pattern used by all three (Normalization, Dependency, Query Store)
Add-Type -AssemblyName System.Data
$connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
$connection.Open()
...
$connection.Close()  # (varies — see §3.5)
```

**DDL Generator has no WPF/PS1 connection testing layer.**

---

### 3.2 Authentication Handling

#### Configuration

All four utilities store authentication credentials in `Config/database-config.json` using a `windows_auth` boolean flag:

```json
{
  "servername": "...",
  "database": "...",
  "username": "...",
  "password": "...",
  "windows_auth": true
}
```

When `windows_auth` is `true`, `username` and `password` are ignored in connection string construction.

**Consistent:** The `windows_auth` field name, type (boolean), and default behavior (falls back to `false` = SQL auth) are identical across all four utilities.

#### Python ConfigLoader Validation of Authentication Fields

| Utility | Validates `username`/`password` when `windows_auth = false` |
|---|---|
| Normalization | ✅ Yes — raises `ValueError` with clear message |
| Dependency | ✅ Yes — raises `ValueError` with clear message |
| Query Store | ⚠️ Partial — only validates `servername`; `database` defaults to `'master'` if missing; no explicit validation of `username`/`password` |
| DDL Generator | ✅ Yes — reads from caller-supplied arguments; validation is in caller code |

**Inconsistency:** The Query Store ConfigLoader `get_connection_string()` silently defaults the `database` to `'master'` if the key is absent from `database-config.json`, whereas Normalization and Dependency raise a `ValueError`. This means a misconfigured QS `database-config.json` (missing the `database` key) would silently connect to `master` rather than failing loudly.

#### PowerShell (WPF) Authentication

All three WPF utilities build their ADO.NET connection strings using the same pattern:

```powershell
$useWindowsAuth = $script:chkWindowsAuth -and $script:chkWindowsAuth.IsChecked
if ($useWindowsAuth) {
    $connectionString = "Server=$server;Database=$database;Integrated Security=True;TrustServerCertificate=True;Connection Timeout=5;"
} else {
    $connectionString = "Server=$server;Database=$database;User ID=$username;Password=$password;TrustServerCertificate=True;Connection Timeout=5;"
}
```

**Consistent:** The branch logic and connection string keywords are identical across all three WPF utilities.

---

### 3.3 Connection String Construction

#### Python ODBC Connection Strings

All four Python ConfigLoaders produce connection strings in the same format:

**Windows Authentication:**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;DATABASE=...;Trusted_Connection=yes;TrustServerCertificate=yes;
```

**SQL Server Authentication:**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...;TrustServerCertificate=yes;
```

**Consistent across all four utilities:** ODBC keyword order, `TrustServerCertificate=yes`, `Trusted_Connection=yes`, `UID`/`PWD` naming.

#### Key Method Name Difference

| Utility | Method Name | Signature |
|---|---|---|
| Normalization | `get_connection_string()` | Zero-argument — reads from loaded config |
| Dependency | `get_connection_string()` | Zero-argument — reads from loaded config |
| Query Store | `get_connection_string()` | Zero-argument — reads from loaded config |
| DDL Generator | `build_connection_string()` | **Parameterized** — accepts `server`, `user`, `password`, `db_name`, `driver_hint`, `windows_auth` |

**Inconsistency:** The DDL Generator uses a different method name (`build_connection_string`) and signature. This is architecturally justified by the multi-server design (it cannot read from a single pre-loaded config), but the naming diverges from the pattern established by the other three utilities. The docstring for `build_connection_string()` explicitly documents this difference.

#### ODBC Driver Auto-Detection

All four utilities implement identical ODBC driver auto-detection logic:

```python
drivers_to_try = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server"
]
```

**Consistent:** The priority list, method name `_get_available_odbc_driver()`, and `get_odbc_driver()` behavior (respects explicit `odbc_driver` config unless set to `'auto'`) are identical across all four utilities.

#### PS1 vs Python Connection Timeout

| Context | Timeout Source | Value |
|---|---|---|
| Python scripts | `config.json` → `database.connection_timeout` | Configurable (default 10 seconds) |
| PS1 WPF connection test | **Hardcoded** in connection string | Always 5 seconds |

**Inconsistency:** The Python layer uses a configurable timeout from `config.json`. The PowerShell WPF layer hardcodes `Connection Timeout=5` in the ADO.NET connection string for the UI test function. These are different values and the PS1 value cannot be changed without editing code.

---

### 3.4 Configuration Management

#### `database-config.json` Structure

| Utility | Structure |
|---|---|
| Normalization | Flat object: `{ "servername": ..., "database": ..., "username": ..., "password": ..., "windows_auth": ... }` |
| Dependency | Flat object: same as Normalization |
| Query Store | Flat object: same as Normalization |
| DDL Generator | **Nested array:** `{ "servers": [{ "parent_name": ..., "servername": ..., "port": ..., "username": ..., "password": ..., "windows_auth": ..., "databases_include": [...], "active": ... }] }` |

**Major Inconsistency:** The DDL Generator's `database-config.json` uses a fundamentally different structure — an array of server objects, each with a `databases_include` whitelist and an `active` flag. The other three utilities use a flat single-server object. This difference is intentional (DDL must manage multiple servers) but means the configuration management is not transferable between utilities.

#### `config.json` Structure

**Normalization:**
```json
{
  "paths": { "database_config", "table_config", "output_directory", "functional_dependencies_output" },
  "analysis": { "max_determinant_size", "progress_update_interval" },
  "database": { "odbc_driver", "default_schema", "connection_timeout" },
  "excel": { ... },
  "logging": { "show_progress", "show_sql_queries", "log_level", "log_format", "timestamp_format" }
}
```

**Dependency:**
```json
{
  "description": "...",
  "version": "1.0",
  "paths": { "java_source_dirs", "project_base_dir", "output_dir", "log_dir", "database_config" },
  "files": { "database_config", "database_object_input", ... },   ← database_config duplicated here
  "database": { "odbc_driver", "connection_timeout" },
  "logging": { "log_level", "log_format", "timestamp_format" },
  "formatting": { "naming_convention", ... }
}
```

**Query Store:**
```json
{
  "description": "...",
  "version": "2.0",
  "paths": {
    "logs": { "base_dir": "Logs" },           ← nested, different from others
    "database_config": "...",
    "config": { "reports_config": ..., "active_report_config": ... },
    "github_repo": { "procs": ..., "functions": ... }
  },
  "database": { "odbc_driver", "connection_timeout" },
  "processing": { "xml_plan_download_batch_size", ... },
  "logging": { "log_level", "log_format", "timestamp_format" },
  "sql_modifications": { "datetime_conversion": { ... } }
}
```

**DDL Generator:**
```json
{
  "paths": {
    "workspace_dir": "C:\\Advanced_SQL_Server_Toolkit\\DDL_Generator_Utility",   ← absolute path
    "config_dir": "Config",
    "database_config_dir": "Config\\database_config",
    "log_dir": "Logs",
    "generated_scripts_dir": "Output"
  },
  "files": { "sql_server_connections_file", "commands_config_file" },
  "logging": { "log_format", "log_level", "timestamp_format", "log_filemode" },   ← log_filemode unique
  "database": { "odbc_driver", "connection_timeout", "commit_every_n_tables" },   ← commit_every_n_tables unique
  "mssql_scripter": { "default_options", "max_retry_attempts" }                   ← unique section
}
```

**Identified `config.json` Inconsistencies:**

| Issue | Detail |
|---|---|
| Paths structure depth | Normalization/DDL: flat paths keys. Dependency: paths + files. QS: nested paths sub-objects. |
| Absolute path in config | DDL's `workspace_dir` is a hardcoded absolute Windows path. All others derive paths from `__file__`. |
| `database_config` duplication | Dependency config.json lists `database_config` in **both** `paths` and `files` sections. |
| `version` and `description` fields | Present in Dependency ("1.0") and QS ("2.0"). Absent in Normalization and DDL. |
| `log_dir` path key | Normalization: `paths.log_dir` (via `get_log_dir()`). Dependency: `paths.log_dir`. QS: `paths.logs.base_dir` (nested). DDL: `paths.log_dir`. QS diverges from all others. |
| Utility-specific sections | Each utility adds config sections only it uses (`analysis`/`excel` in Normalization, `formatting` in Dependency, `processing`/`sql_modifications` in QS, `mssql_scripter`/`commit_every_n_tables` in DDL). This is appropriate but reflects no shared schema. |

---

### 3.5 Error Handling

#### Python ConfigLoader Initialization

| Utility | Raises on missing config file | Raises on invalid JSON | Raises on missing required keys |
|---|---|---|---|
| Normalization | ✅ `FileNotFoundError` | ✅ `json.JSONDecodeError` (with context) | ✅ `ValueError` / `KeyError` |
| Dependency | ✅ `FileNotFoundError` | ✅ `json.JSONDecodeError` (with context) | ✅ `ValueError` for db fields |
| Query Store | ✅ `FileNotFoundError` (via `if not exists`) | ⚠️ **No `json.JSONDecodeError` handling** in `_load_reports_config()` or `_load_active_report_config()` | ⚠️ Partial — only `servername` validated |
| DDL Generator | ✅ `FileNotFoundError` | ✅ `json.JSONDecodeError` (with context) | ✅ `KeyError` for required sections |

**Inconsistency:** The Query Store ConfigLoader's `_load_reports_config()` and `_load_active_report_config()` methods do **not** wrap `json.load()` in a try/except for `json.JSONDecodeError`. If either reports config file contains malformed JSON, an unhandled exception would propagate uncaught. The other three utilities all explicitly catch `json.JSONDecodeError`.

#### Python Script `main()` Functions

All four utilities follow the same pattern in script `main()` functions:

```python
try:
    config = ConfigLoader()
except (FileNotFoundError, ValueError, KeyError) as e:
    print(f"[ERROR] Configuration error: {e}")
    sys.exit(1)
```

**Consistent:** Config initialization is always wrapped with appropriate exception types and `sys.exit(1)` on failure.

#### PowerShell `Test-DatabaseConnection` Error Handling

All three WPF utilities use try/catch/finally for connection testing. However, there are notable differences in the `finally` block (resource cleanup):

| Utility | Connection Disposal Pattern |
|---|---|
| Normalization | `finally`: checks `if ($connection.State -eq [System.Data.ConnectionState]::Open)` before calling `.Close()`, then always `.Dispose()` |
| Dependency | `finally`: does NOT check state before calling `.Close()` (called explicitly in `try`), calls `.Dispose()` in `finally` |
| Query Store | In `try`: calls `.Open()`, `.ServerVersion`, `.Close()`. In `finally`: calls `.Dispose()` but does NOT check `if ($null -ne $connection)` consistently |

**Inconsistency:** The Normalization utility is the most defensive — it checks the connection state before attempting to close it. The Dependency utility calls `.Close()` explicitly inside the `try` block but does not recheck state in `finally`. The Query Store utility also closes within `try` but additionally retrieves `ServerVersion` and shows it in the success message (extra capability not present in others).

**Additional behavioral difference — Query Store WPF only:**
- Disables `$script:btnTestConnection.IsEnabled = $false` during the test and re-enables in `finally`. Normalization and Dependency do **not** disable the button.
- Shows SQL Server version in the success message box (`$version = $connection.ServerVersion`). Others only confirm server/database.

---

### 3.6 Logging

#### Python Logging — Consistent Elements

All four utilities:
- Use Python `logging` module
- Configure dual-output handlers: `FileHandler` (to file) + `StreamHandler` (to console)
- Name log files as `log_{script_name}_{timestamp}.log`
- Use `setup_logging(script_name)` method in `ConfigLoader`, returning the log `Path`
- Default log level: `INFO`
- Default format: `%(asctime)s - %(levelname)s - %(message)s`
- Default timestamp format: `%Y%m%d_%H%M%S`

#### Python Logging — Inconsistencies

| Issue | Detail |
|---|---|
| Log file mode | DDL's `setup_logging()` reads `log_filemode` from config.json (`'a'` = append by default). Normalization, Dependency, and QS use `logging.basicConfig(..., force=True)` which effectively resets handlers each call (equivalent to write/overwrite mode). |
| CLI log format (DDL) | DDL's CLI script (`CLI - DDL Generator Utility.py`) uses `'[%(asctime)s] [%(levelname)s] %(message)s'` with brackets. All ConfigLoader-based `setup_logging()` calls use `'%(asctime)s - %(levelname)s - %(message)s'` with dashes. |
| CLI logging setup location | DDL CLI configures logging at **module level** (`logging.basicConfig(...)` outside any function) at import time. All other utilities defer logging setup to `config.setup_logging()` called from `main()`. |
| QS log path config key | QS refers to the log directory via `paths.logs.base_dir` (nested). Normalization and Dependency use `paths.log_dir` (flat). DDL uses `paths.log_dir` (flat). QS's `get_log_dir()` method is actually named `get_logs_base_dir()` — different from all others. |

#### PowerShell Logging

All three WPF utilities implement a `Log-Output` function for appending timestamped messages to the UI output log control and writing to the console. The implementation is consistent across all three.

---

### 3.7 Naming Conventions

#### File Naming — Consistent

| Element | Convention | Used By |
|---|---|---|
| Config files | `kebab-case.json` | All four |
| Python scripts | `##_description_snake_case.py` | All four |
| Log files | `log_{script_name}_{timestamp}.log` | All four |
| Config loader | `config_loader.py` | All four |
| WPF functions file | `{UtilityName}Functions.ps1` | Normalization, Dependency, QS |

#### Naming Inconsistencies

| Issue | Detail |
|---|---|
| `get_log_dir()` vs `get_logs_base_dir()` | QS ConfigLoader uses `get_logs_base_dir()`. All others use `get_log_dir()`. Same purpose, different name. |
| `run_all_scripts.py` prefix | Dependency uses `00_run_all_scripts.py` (numbered). QS uses `run_all_scripts.py` (no number). |
| `build_connection_string()` vs `get_connection_string()` | DDL uses a different method name as discussed in §3.3. |
| PS1 `Initialize-*` function signature | Normalization takes `[string]$ScriptDirectory`; Dependency takes no path parameter (uses `$PSScriptRoot`); QS takes `[string]$ProjectRoot`. |

---

### 3.8 Code Organization

#### Directory Structure — Consistent

All four utilities follow the same top-level layout:

```
UtilityName/
  Config/           ← JSON configuration files
  Core/
    Python/         ← Python scripts including config_loader.py
    SQL/            ← SQL files (Normalization, Dependency, QS only)
    WPF/            ← WPF scripts (Normalization, Dependency, QS only)
  Logs/             ← Log output
  Output/           ← Analysis output
  README.md
```

#### Organization Inconsistencies

| Issue | Detail |
|---|---|
| WPF presence | Normalization, Dependency, QS have WPF GUIs. DDL has no WPF — CLI only. |
| SQL subdirectory | Normalization, Dependency, and QS have `Core/SQL/` for SQL files. DDL has no `Core/SQL/` (uses `mssql-scripter` externally, not embedded SQL queries). |
| Additional config subdirectory | DDL has `Config/database_config/` for dynamically generated per-server configs. No other utility has this. |
| `__pycache__` present in repo | All utilities have `__pycache__/` directories checked in. Not a functional issue but indicates the `.gitignore` (if any) does not exclude compiled bytecode. |

#### ConfigLoader Class Shape — Comparison

| Feature | Normalization | Dependency | Query Store | DDL |
|---|---|---|---|---|
| Module docstring | ✅ Detailed | ✅ Present | ✅ Detailed | ✅ Detailed |
| `__init__` raises on bad config | ✅ Multiple error types | ✅ Multiple error types | ✅ (partial) | ✅ Multiple error types |
| Explicit `_validate_config()` method | ✅ `_validate_python_config()` + `_validate_database_config()` | ❌ Inline in load methods | ❌ None | ✅ `_validate_config()` |
| `get_connection_string()` | ✅ Zero-arg | ✅ Zero-arg | ✅ Zero-arg | ❌ Renamed + parameterized |
| File open encoding | ❌ No explicit encoding (uses system default) | ✅ `encoding='utf-8'` | ✅ `encoding='utf-8'` | ✅ `encoding='utf-8'` |
| db_config lazy loading / caching | ❌ Loaded in `__init__` | ✅ `_db_config` cache | ✅ `database_config` cache | N/A (multi-server) |
| `reload_configs()` method | ❌ | ❌ | ✅ | ❌ |
| Type annotations (return types) | Partial | Partial | Partial | More extensive |
| `setup_logging()` configurable filemode | ❌ | ❌ | ❌ | ✅ |

---

### 3.9 General Coding Patterns and Best Practices

#### Observations

| # | Observation | Utilities Affected |
|---|---|---|
| 1 | **Absolute path in config.json** — DDL's `workspace_dir` is hardcoded as `C:\Advanced_SQL_Server_Toolkit\DDL_Generator_Utility`. Changing the installation path requires editing `config.json`. All other utilities derive their root from `Path(__file__).parent.parent.parent`, making them location-independent. | DDL Generator only |
| 2 | **Redundant path in config.json** — DDL's `ConfigLoader.get_workspace_dir()` returns `Path(config['paths']['workspace_dir'])` (the hardcoded absolute value) while `get_config_dir()` uses `self.project_root` (derived from `__file__`). If the directory is moved, these two will disagree. | DDL Generator only |
| 3 | **`database_config` key duplicated** — Dependency's `config.json` lists `database_config` under both the `paths` section and the `files` section, pointing to the same file. The ConfigLoader reads from `paths.database_config` only; the `files.database_config` entry is unused dead configuration. | Dependency only |
| 4 | **Missing file encoding in `_load_json()`** — Normalization's `ConfigLoader._load_json()` calls `open(file_path, 'r')` without specifying `encoding='utf-8'`. On Windows systems where the system locale is not UTF-8, this could fail to read JSON files containing non-ASCII characters (e.g., server names or passwords with special characters). All other utilities explicitly use `encoding='utf-8'`. | Normalization only |
| 5 | **Missing `json.JSONDecodeError` handling** — Query Store ConfigLoader's `_load_reports_config()` and `_load_active_report_config()` do not wrap `json.load()` in try/except. Malformed JSON in `reports-config.json` or `active-report-config.json` will raise an unhandled exception that bypasses the `main()` guard. | Query Store only |
| 6 | **Password comment in PS1** — Query Store `Save-DatabaseConfiguration` contains the comment `# SECURITY: Do not log password`. This is a good practice note. The other two WPF utilities do not log passwords either, but they lack this explicit security annotation. | Minor — QS only has annotation |
| 7 | **Server version display on connection test** — Query Store `Test-DatabaseConnection` retrieves `$connection.ServerVersion` and includes it in the success message. Normalization and Dependency do not. This extra capability is useful but introduces behavioral inconsistency in the UI experience. | QS only |
| 8 | **Button disabling during connection test** — Query Store disables `btnTestConnection` during the async test and re-enables it in `finally`. Normalization and Dependency do not disable the button. | QS only |
| 9 | **PS1 function documentation style** — Normalization uses PowerShell comment-based help (`<# .SYNOPSIS .DESCRIPTION .OUTPUTS #>`) for key PS1 functions. Dependency and Query Store generally do not use this pattern, relying instead on inline `Write-Host "[INFO]..."` comments. | Normalization vs Dependency/QS |
| 10 | **PS1 project root determination** — Three different mechanisms are used across the three WPF utilities: Normalization passes `$ScriptDirectory` as a parameter; Dependency uses `$PSScriptRoot`; Query Store receives `$ProjectRoot` pre-calculated from `Main.ps1`. All navigate up 3 levels (`Scripts → WPF → Core → ProjectRoot`), so the result is the same, but the mechanism differs. | All WPF utilities |
| 11 | **Config version tracking** — Dependency has `"version": "1.0"` and QS has `"version": "2.0"` in `config.json`. Normalization and DDL have no version field. This makes it harder to track config schema evolution for two of the four utilities. | Normalization + DDL |
| 12 | **`commit_every_n_tables` in DDL database config** — The DDL `config.json` has a `commit_every_n_tables: 10` setting in the `database` section that does not appear to be used by any of the three current Python scripts. It may be a placeholder for future functionality or a leftover from a previous implementation. | DDL Generator only |
| 13 | **`show_progress` / `show_sql_queries` logging flags** — Normalization's `config.json` has `logging.show_progress` and `logging.show_sql_queries` fields (exposed via `should_show_progress()` and `should_show_sql_queries()` getters). None of the other three utilities have these flags, so the per-utility logging verbosity control is not consistent. | Normalization only |

---

## 4. Consolidated Findings by Dimension

### 4.1 What Is Consistent

- **ODBC driver**: All four use `pyodbc`; all auto-detect from the same ordered driver list (18 → 17 → 13 → 11 → Native Client → SQL Server).
- **ODBC connection string format**: Identical keywords (`DRIVER`, `SERVER`, `DATABASE`, `Trusted_Connection`, `UID`, `PWD`, `TrustServerCertificate`) and values across all four.
- **`windows_auth` boolean field**: Present in all `database-config.json` files; same field name, same logic.
- **`TrustServerCertificate=yes`**: Applied in all Python ODBC strings.
- **ConfigLoader class name**: All four use the class name `ConfigLoader`.
- **`config_loader.py` file name**: Consistent across all four.
- **`setup_logging()` method**: Present in all four; same signature; all return the log file `Path`.
- **Log file naming pattern**: `log_{script_name}_{timestamp}.log` — consistent.
- **Numbered script convention**: `01_`, `02_`, `03_` prefix used in all Python backend scripts.
- **`sys.exit(1)` on config failure**: Consistent in all `main()` functions.
- **WPF connection string keywords** (PS1): `Integrated Security=True`, `TrustServerCertificate=True`, `Connection Timeout=5` — identical across Normalization, Dependency, and Query Store.
- **`Log-Output` PS1 function**: All three WPF utilities implement the same `Log-Output` pattern.

### 4.2 What Is Inconsistent

| Priority | Category | Inconsistency |
|---|---|---|
| **High** | Config structure | `database-config.json` is a flat object in 3 utilities but a nested server array in DDL. |
| **High** | Error handling | QS ConfigLoader does not catch `json.JSONDecodeError` for secondary config files. |
| **High** | Config paths | Absolute `workspace_dir` hardcoded in DDL `config.json`; all others use `__file__`-relative paths. |
| **Medium** | Connection method | DDL uses `build_connection_string(server, user, ...)` (parameterized). Others use `get_connection_string()` (zero-arg). |
| **Medium** | Auth validation | QS silently defaults `database` to `'master'` when the key is missing; others raise `ValueError`. |
| **Medium** | File encoding | Normalization `_load_json()` does not specify `encoding='utf-8'`; all others do. |
| **Medium** | Config paths structure | QS uses `paths.logs.base_dir` (nested); others use flat `paths.log_dir`. Method also renamed to `get_logs_base_dir()` in QS vs `get_log_dir()` in all others. |
| **Medium** | Duplicate config key | Dependency has `database_config` in both `paths` and `files` sections. |
| **Medium** | PS1 root resolution | Three different mechanisms (parameter, `$PSScriptRoot`, pre-calculated) across the three WPF utilities. |
| **Low** | PS1 connection test behavior | QS adds server version display + button disable; Normalization does state-check before close; Dependency does not. |
| **Low** | Log filemode | DDL supports configurable append/overwrite mode; others do not. |
| **Low** | CLI logging format | DDL CLI uses bracket-delimited format `[timestamp]`; ConfigLoader scripts use dash-delimited. |
| **Low** | CLI logging timing | DDL CLI sets up logging at module level; others defer to `main()`. |
| **Low** | PS1 documentation style | Normalization uses comment-based help; Dependency and QS use inline comments. |
| **Low** | Config version tracking | Only Dependency and QS have `version` field in `config.json`. |
| **Low** | `reload_configs()` | Only QS ConfigLoader implements this method. |
| **Low** | db_config caching | Normalization loads in `__init__`; Dependency and QS use lazy caching; DDL is multi-server by design. |

---

## 5. Summary Scorecard

| Criterion | Consistent? | Notes |
|---|---|---|
| Connection library (Python) | ✅ Fully consistent | All use `pyodbc` |
| ODBC driver auto-detection | ✅ Fully consistent | Identical logic in all four |
| Connection string format | ✅ Fully consistent | Same keywords and values |
| `windows_auth` support | ✅ Fully consistent | Same field, same branching logic |
| `TrustServerCertificate` | ✅ Fully consistent | Present in all connection strings |
| Connection timeout | ⚠️ Minor difference | Python: configurable (default 10s); PS1: hardcoded 5s |
| `get_connection_string()` API | ⚠️ DDL diverges | DDL uses `build_connection_string()` (parameterized) |
| Auth field validation | ⚠️ QS partial | QS silently defaults `database` to `master` |
| `database-config.json` structure | ❌ Major difference | DDL is nested multi-server; others are flat single-server |
| `config.json` structure | ⚠️ Varies | Each utility extends the schema differently; no shared standard |
| ConfigLoader class name | ✅ Fully consistent | All named `ConfigLoader` |
| `setup_logging()` pattern | ✅ Mostly consistent | Minor difference in filemode handling |
| Log file naming | ✅ Fully consistent | All use `log_{name}_{timestamp}.log` |
| Error handling (config load) | ⚠️ QS incomplete | QS missing `JSONDecodeError` handling for secondary configs |
| File encoding in ConfigLoader | ⚠️ Normalization | Only Normalization omits explicit `encoding='utf-8'` |
| PS1 connection test disposal | ⚠️ Minor differences | Three slightly different cleanup patterns |
| PS1 project root resolution | ⚠️ Minor differences | Three different mechanisms |

---

## 6. Observations Not Requiring Action (By Design)

The following differences are intentional and architecturally appropriate; they are documented here for completeness:

1. **DDL Generator multi-server database config** — The nested `servers` array in `database-config.json` is required because DDL must connect to multiple SQL Server instances. The flat single-server format used by other utilities cannot support this use case.

2. **DDL `build_connection_string()` parameterization** — The method accepts server/credentials as arguments because the DDL loop iterates over multiple servers from the config array. A zero-argument getter reading from a single pre-loaded config would not be workable.

3. **DDL has no WPF UI** — The DDL Generator operates in CLI mode, which explains the absence of `System.Data.SqlClient` connection testing and the different logging format.

4. **QS has multiple config files** — The Query Store utility manages multiple report types (Top Resource Consuming, High Plan Count, High Variation), which justifies separating the report definitions (`reports-config.json`) from the active selection (`active-report-config.json`) and main settings (`config.json`).

5. **Per-utility sections in `config.json`** — Each utility has domain-specific settings (e.g., `analysis.max_determinant_size` in Normalization, `mssql_scripter` in DDL) that are appropriately scoped to that utility. The presence of unique sections in each `config.json` is expected.

---

*End of analysis. No code was modified.*

