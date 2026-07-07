# Database Access Conformance Analysis
**Generated:** 2026-06-25 15:25:53  
**Scope:** Read-only analysis — no code was modified  
**Utilities Analyzed:**
- `Database_Normalization_Analysis_Utility`
- `Database_Object_Dependency_Utility`
- `Query_Store_Analysis_Utility`
- `DDL_Generator_Utility`

---

## Executive Summary

The four utilities share a broadly consistent architectural pattern: a Python `ConfigLoader` class reads JSON configuration files, builds an ODBC connection string, and delegates SQL execution to `pyodbc`. Three utilities also include a PowerShell/WPF UI layer that performs a separate connection test using `System.Data.SqlClient.SqlConnection`.

However, **significant inconsistencies exist** across all major dimensions examined: connection string construction, authentication support, configuration structure, config validation depth, ODBC driver handling, logging behavior, and PowerShell connection test implementation. These are documented in full below.

---

## 1. Architecture Overview

| Dimension | Normalization | Object Dependency | Query Store | DDL Generator |
|---|---|---|---|---|
| **Python DB library** | `pyodbc` | `pyodbc` | `pyodbc` | `pyodbc` |
| **Config loader class** | `ConfigLoader` | `ConfigLoader` | `ConfigLoader` | `ConfigLoader` |
| **WPF/PowerShell UI** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No (CLI only) |
| **PowerShell DB test** | ✅ `SqlClient` | ✅ `SqlClient` | ✅ `SqlClient` | N/A |
| **Multi-server support** | ❌ Single server | ❌ Single server | ❌ Single server | ✅ Multiple servers |
| **Number of config files** | 3 | 2 | 4 | 2 + per-server files |

---

## 2. Connection Methods

### 2.1 Python — `pyodbc`

All four utilities use `pyodbc` as the sole Python library for SQL Server access. Connections are opened via:

```python
pyodbc.connect(connection_string, timeout=config.get_connection_timeout())
```

**Three utilities** (Normalization, Object Dependency, Query Store) use the context manager pattern (`with pyodbc.connect(...) as conn:`) which ensures automatic connection closure.

**DDL Generator** uses an explicit non-context-manager call inside a helper function `try_sqlserver_connect()` and relies on the `with` block at the call site in the script.

### 2.2 PowerShell — `System.Data.SqlClient.SqlConnection`

Three utilities (Normalization, Object Dependency, Query Store) use the .NET `System.Data.SqlClient.SqlConnection` in their WPF `Test-DatabaseConnection` function. The DDL Generator has no WPF layer.

---

## 3. Connection String Construction

### 3.1 Python Connection Strings

All four utilities produce ODBC connection strings with the same key/value structure:

**Windows Authentication (Normalization, Object Dependency, Query Store):**
```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=<server>;DATABASE=<db>;Trusted_Connection=yes;TrustServerCertificate=yes;
```

**SQL Server Authentication (all four):**
```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=<server>;DATABASE=<db>;UID=<user>;PWD=<password>;TrustServerCertificate=yes;
```

**DDL Generator only** — connection string is built via a parametric method signature:
```python
def get_connection_string(self, server, user="", password="", db_name="master",
                           driver_hint=None, windows_auth=False) -> str:
```
This differs from the other three utilities where `get_connection_string()` is parameterless and reads from the internally loaded database config.

### 3.2 PowerShell Connection Strings

| Utility | Auth Keyword | Connection Timeout | User Auth Keyword |
|---|---|---|---|
| Normalization | `Integrated Security=True` | `Connection Timeout=5` ✅ | `User ID=` |
| Object Dependency | `Integrated Security=True` | **Missing** ⚠️ | `User Id=` ⚠️ |
| Query Store | `Integrated Security=True` | `Connection Timeout=5` ✅ | `User ID=` |

**Inconsistencies:**
- **Object Dependency** is missing `Connection Timeout` in its PowerShell connection string. The other two utilities hardcode `Connection Timeout=5`.
- **Object Dependency** uses `User Id=` (mixed case) while Normalization and Query Store use `User ID=` (uppercase). Both are valid in SqlClient but are inconsistent.

---

## 4. Authentication Handling

### 4.1 Python

| Utility | Windows Auth Supported | SQL Auth Supported | `windows_auth` Config Flag |
|---|---|---|---|
| Normalization | ✅ | ✅ | `windows_auth: true/false` |
| Object Dependency | ✅ | ✅ | `windows_auth: true/false` |
| Query Store | ✅ | ✅ | `windows_auth: true/false` |
| DDL Generator | ❌ Not in config | ✅ | **No `windows_auth` flag** ⚠️ |

**Inconsistency:** The DDL Generator's `database-config.json` has no `windows_auth` flag, and its `get_connection_string()` method accepts a `windows_auth` parameter directly at call time. Windows Authentication is therefore not configurable via the JSON config file, unlike all other utilities. The actual database-config.json for this utility only contains `servers[]` with `username`/`password` fields.

### 4.2 PowerShell

All three WPF utilities check `$script:chkWindowsAuth.IsChecked` to determine authentication type, which is consistent.

---

## 5. Configuration Management

### 5.1 Config File Structure

#### Normalization — 3 config files:
- `Config/config.json` — Python settings, paths, analysis params, Excel, logging
- `Config/database-config.json` — `{servername, database, username, password, windows_auth}`
- `Config/table-config.json` — `{table, columns, primarykey, uniquekey}`

#### Object Dependency — 2 config files:
- `Config/config.json` — paths, files, database driver settings, logging, formatting
- `Config/database-config.json` — `{servername, database, username, password, windows_auth}`

#### Query Store — 4 config files:
- `Config/config.json` — paths, processing, logging, SQL modification settings
- `Config/database-config.json` — `{servername, database, username, password, windows_auth}`
- `Config/reports-config.json` — report definitions per report type
- `Config/active-report-config.json` — selects the active report

#### DDL Generator — 2 + N config files:
- `Config/config.json` — paths, logging, database driver, mssql_scripter settings
- `Config/database-config.json` — `{servers: [{parent_name, servername, port, username, password, databases_include, active}]}`
- `Config/database_config/database_config_<server>.json` — auto-generated per-server files

### 5.2 Database Config Structure Differences

| Field | Normalization | Object Dependency | Query Store | DDL Generator |
|---|---|---|---|---|
| `servername` | ✅ flat | ✅ flat | ✅ flat | ✅ in `servers[]` |
| `database` | ✅ flat | ✅ flat | ✅ flat | ❌ not in master config |
| `username` | ✅ flat | ✅ flat | ✅ flat | ✅ in `servers[]` |
| `password` | ✅ flat | ✅ flat | ✅ flat | ✅ in `servers[]` |
| `windows_auth` | ✅ flat | ✅ flat | ✅ flat | ❌ absent |
| `port` | ❌ absent | ❌ absent | ❌ absent | ✅ in `servers[]` |
| `parent_name` | ❌ absent | ❌ absent | ❌ absent | ✅ in `servers[]` |
| `databases_include` | ❌ absent | ❌ absent | ❌ absent | ✅ in `servers[]` |
| `active` flag | ❌ absent | ❌ absent | ❌ absent | ✅ in `servers[]` |

The DDL Generator's nested server/database config structure is fundamentally different from the other three utilities. This is intentional given its multi-server scope, but it means the config loading logic is not interchangeable.

### 5.3 Notable Config Differences in `config.json`

| Setting | Normalization | Object Dependency | Query Store | DDL Generator |
|---|---|---|---|---|
| `odbc_driver` | `"ODBC Driver 17 for SQL Server"` ⚠️ | `"ODBC Driver 17 for SQL Server"` ⚠️ | `"auto"` ✅ | `"auto"` ✅ |
| `connection_timeout` | `10` | `10` | `10` | `10` |
| `log_filemode` | ❌ absent (append) | ❌ absent (append) | ❌ absent (append) | `"w"` (overwrite) ⚠️ |
| `log_dir` | via `paths.log_dir` (absent, uses project root/Logs) | `"Logs"` | `paths.logs.base_dir` | `"Logs"` |
| `commit_every_n_tables` | ❌ absent | ❌ absent | ❌ absent | ✅ `10` |
| `mssql_scripter` section | ❌ absent | ❌ absent | ❌ absent | ✅ present |

---

## 6. ODBC Driver Handling

All four utilities implement an identical `_get_available_odbc_driver()` method that tries drivers in order: 18, 17, 13, 11, Native Client 11.0, SQL Server. The auto-detect logic and error message are character-for-character identical across all four.

**Inconsistency — `odbc_driver` default:**
- Normalization and Object Dependency explicitly configure `"ODBC Driver 17 for SQL Server"` in `config.json`, overriding auto-detect.
- Query Store and DDL Generator set `"auto"`, enabling dynamic driver selection.

This means Normalization and Object Dependency will **fail** if only ODBC Driver 18 is installed and Driver 17 is not, while Query Store and DDL Generator would succeed.

---

## 7. Error Handling

### 7.1 Python Error Handling

All utilities follow the same general pattern at the `main()` entry point:

```python
try:
    config = ConfigLoader()
except (FileNotFoundError, ValueError, KeyError) as e:
    print(f"[ERROR] Configuration error: {e}")
    sys.exit(1)
```

Script-level database operations handle:

| Exception Type | Normalization | Object Dependency | Query Store | DDL Generator |
|---|---|---|---|---|
| `pyodbc.Error` | ✅ caught | ✅ caught | ✅ caught | ✅ caught |
| `ValueError` | ✅ caught | ✅ caught | ✅ caught | ✅ caught |
| `FileNotFoundError` | ✅ caught | ✅ caught | ✅ caught | ✅ caught |
| `RuntimeError` (no ODBC driver) | indirectly via `Exception` | indirectly via `Exception` | indirectly via `Exception` | ✅ explicitly caught |
| Generic `Exception` | ✅ caught | ✅ caught | ✅ caught | ✅ caught |

**Normalization is the most thorough** — it validates the full configuration structure upfront in `_validate_python_config()` and `_validate_database_config()` before any database operation. Other utilities do partial or deferred validation.

### 7.2 PowerShell Error Handling

| Utility | `try/catch/finally` | `$connection.Dispose()` | `Add-Type -AssemblyName System.Data` |
|---|---|---|---|
| Normalization | ✅ Yes | ✅ Yes | ✅ Yes |
| Object Dependency | ✅ Yes | ❌ No (only `.Close()`) ⚠️ | ❌ No ⚠️ |
| Query Store | ✅ Yes | ❌ No (only `.Close()`) ⚠️ | ❌ No ⚠️ |

**Inconsistencies:**
- Only **Normalization** calls `Add-Type -AssemblyName System.Data` before using `System.Data.SqlClient`. The other two utilities rely on the assembly already being loaded, which may fail in some PowerShell environments.
- Only **Normalization** calls `$connection.Dispose()` in the `finally` block for proper resource cleanup. Object Dependency and Query Store only call `.Close()` (Query Store in the `try` block) or skip cleanup in `finally`.

---

## 8. Logging

### 8.1 Python Logging

All four utilities implement a `setup_logging(script_name)` method that:
1. Creates a timestamped log file in the configured `log_dir`
2. Configures `logging.basicConfig` with both `FileHandler` and `StreamHandler`
3. Uses `force=True` to override any existing configuration

The log file naming convention is consistent across all: `log_<script_name>_<timestamp>.log`

**Inconsistency — Log File Mode:**
- Normalization, Object Dependency, Query Store: No `log_filemode` setting — `logging.basicConfig` defaults to append mode (`'a'`)
- DDL Generator: Explicitly sets `log_filemode: "w"` in config.json, overwriting the log file on each run

This means the DDL Generator clears its logs on each run, while other utilities accumulate log entries.

**Inconsistency — Log Directory Path Resolution:**
- Normalization: Resolved via `config.get('paths', {}).get('log_dir', 'Logs')` — the `log_dir` key is **absent** from its `config.json` paths section, falling back to the default `'Logs'`
- Object Dependency: `"log_dir": "Logs"` explicitly in config.json paths
- Query Store: `"paths.logs.base_dir": "Logs"` — different nesting structure
- DDL Generator: `"log_dir": "Logs"` explicitly in config.json paths

### 8.2 Log Level

All four utilities use `"log_level": "INFO"` with identical format string: `"%(asctime)s - %(levelname)s - %(message)s"`.

---

## 9. Naming Conventions

### 9.1 Python — Consistent

All four utilities consistently use:
- `snake_case` for functions and variables
- `PascalCase` for the `ConfigLoader` class
- `UPPER_CASE` for module-level constants
- Numbered script files: `00_`, `01_`, `02_`, etc.
- Module docstrings on all files

### 9.2 Config Files — Consistent

All utilities use:
- `config.json` — main Python settings
- `database-config.json` — database connection settings
- `cleanup-config.json` — cleanup settings (where applicable)

### 9.3 PowerShell — Mostly Consistent

All three WPF utilities use:
- `PascalCase` for function names (e.g., `Test-DatabaseConnection`, `Save-DatabaseConfiguration`)
- `$script:` scope prefix for shared variables
- `[INFO]`, `[WARN]`, `[ERROR]` prefixes in `Write-Host` output

---

## 10. Code Organization

### 10.1 Python File Structure — Consistent

All four utilities follow the same directory structure:
```
<UtilityName>/
  Config/           — JSON configuration files
  Core/
    Python/         — Python scripts + config_loader.py
    WPF/            — PowerShell/XAML UI (where applicable)
    SQL/            — SQL query files (where applicable)
  Output/           — Generated output files
  Logs/             — Log files
```

### 10.2 `ConfigLoader` Class Design — Mostly Consistent

All four use a `ConfigLoader` class with:
- `__init__()` accepting optional `config_path`
- `get_odbc_driver()` / `_get_available_odbc_driver()` methods
- `get_connection_string()` method
- `get_connection_timeout()` method
- `setup_logging(script_name)` method

**Divergence — DDL Generator `get_connection_string()` signature:**  
The DDL Generator's method requires server/credentials as parameters rather than reading from the loaded config. This makes the interface different from the other three utilities.

**Divergence — Normalization ConfigLoader complexity:**  
The Normalization utility's `ConfigLoader` is the most feature-rich: it merges multiple configs, has full upfront validation, has dedicated `save_database_config()` logic that splits table vs. connection fields, and has more getter methods. The other utilities have simpler `ConfigLoader` implementations.

---

## 11. General Coding Patterns and Best Practices

| Practice | Normalization | Object Dependency | Query Store | DDL Generator |
|---|---|---|---|---|
| Context manager for DB (`with`) | ✅ | ✅ | ✅ | ✅ |
| Parameterized queries | ✅ | ✅ | ✅ | N/A (no inline queries) |
| Type hints in functions | Partial | Partial | Partial | ✅ Most thorough |
| Docstrings on all functions | ✅ | ✅ | ✅ | ✅ |
| `sys.exit(1)` on fatal errors | ✅ | ✅ | ✅ | ✅ |
| Config upfront validation | ✅ Most thorough | Partial | Partial (lazy) | Partial (section-only) |
| `TrustServerCertificate=yes` | ✅ | ✅ | ✅ | ✅ |

---

## 12. Summary of Inconsistencies

The following table consolidates all identified inconsistencies for quick reference:

| # | Category | Issue | Affected Utilities |
|---|---|---|---|
| 1 | ODBC Driver | `odbc_driver` hardcoded to v17 instead of `"auto"` | Normalization, Object Dependency |
| 2 | Connection String (Python) | `get_connection_string()` is parametric vs. parameterless | DDL Generator vs. others |
| 3 | Auth Support | No `windows_auth` flag in config | DDL Generator |
| 4 | Config Structure | Nested `servers[]` array vs. flat connection fields | DDL Generator vs. others |
| 5 | Config Fields | `port`, `parent_name`, `databases_include`, `active` absent | Normalization, Object Dependency, Query Store |
| 6 | Config Validation | Full upfront validation vs. partial/lazy validation | Normalization more thorough; others inconsistent |
| 7 | Config Files Count | 3 vs. 2 vs. 4 vs. 2+N config files | All differ |
| 8 | Log File Mode | `"w"` (overwrite) vs. default append | DDL Generator vs. others |
| 9 | Log Dir Config | Different nesting in `config.json` for log_dir path | Query Store different from others |
| 10 | PS Connection Timeout | Missing `Connection Timeout` in connection string | Object Dependency |
| 11 | PS User Auth Keyword | `User Id=` vs. `User ID=` | Object Dependency vs. others |
| 12 | PS `Add-Type` | Missing `Add-Type -AssemblyName System.Data` | Object Dependency, Query Store |
| 13 | PS Connection Dispose | Missing `$connection.Dispose()` in finally block | Object Dependency, Query Store |
| 14 | PS Server Version | Retrieves and displays `$connection.ServerVersion` | Query Store only |
| 15 | PS Button State | Disables/re-enables test button in finally | Query Store only |
| 16 | DB Default Fallback | Returns `'master'` if database not set | Query Store only |
| 17 | ConfigLoader Caching | Lazy vs. eager loading of database config | Inconsistent across all four |
| 18 | `log_filemode` Setting | Absent vs. explicitly set | DDL Generator has it; others do not |

---

## 13. Recommendations for Standardization

> **Note:** Per the analysis scope, no changes have been made. The following are observations only.

1. **ODBC Driver:** Change Normalization and Object Dependency `odbc_driver` to `"auto"` to match Query Store and DDL Generator, ensuring compatibility with future driver versions.

2. **`get_connection_string()` signature:** The DDL Generator's parametric approach may be intentional for multi-server support, but the naming convention should be documented. Consider a `get_connection_string_for(server_config)` method name to distinguish it.

3. **Windows Auth support in DDL Generator:** Add `windows_auth` to the `servers[]` config structure for consistency.

4. **PowerShell `Add-Type`:** All three WPF utilities should call `Add-Type -AssemblyName System.Data` before using `System.Data.SqlClient` to ensure portability.

5. **PowerShell `$connection.Dispose()`:** All three WPF utilities should call `.Dispose()` in the `finally` block, not just `.Close()`.

6. **PowerShell Connection Timeout:** Add `Connection Timeout=5` to Object Dependency's connection string.

7. **PowerShell `User ID=` keyword:** Standardize to `User ID=` across all utilities.

8. **Config validation depth:** Consider adopting Normalization's upfront validation approach in the other three utilities.

9. **Log file mode:** Add `log_filemode` to `config.json` in Normalization, Object Dependency, and Query Store to make this behavior explicit and configurable.

10. **Log dir config key:** Standardize to a single nesting convention across all `config.json` files.

---

*Analysis performed: 2026-06-25 | Read-only — no files were modified.*

