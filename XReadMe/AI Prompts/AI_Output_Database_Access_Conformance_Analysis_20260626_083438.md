# Database Access Conformance Analysis

**Generated:** 2026-06-26 08:34:38  
**Scope:** Read-only analysis — no code was modified.

---

## Utilities Analyzed

| Utility | Path |
|---------|------|
| Database Normalization Analysis Utility | `Database_Normalization_Analysis_Utility` |
| Database Object Dependency Utility | `Database_Object_Dependency_Utility` |
| Query Store Analysis Utility | `Query_Store_Analysis_Utility` |
| DDL Generator Utility | `DDL_Generator_Utility` |

---

## Executive Summary

All four utilities share a broadly similar architectural approach: they use Python (`pyodbc`) for SQL Server data access, a centralized `ConfigLoader` class to manage connection settings, JSON configuration files, and `logging` for file+console output. Three of the four also include a WPF/PowerShell UI layer.

However, **significant inconsistencies exist** across the utilities in the following areas:

- Connection string construction (parameterized vs. self-contained)
- Configuration file structure (single-server flat vs. multi-server array)
- Configuration validation rigor
- Error handling specificity
- Cursor usage patterns (explicit `cursor.close()` vs. context manager)
- Log file mode (append vs. overwrite)
- PowerShell WPF connection test implementation quality
- JSON config file formatting (indentation/spacing)

The **DDL Generator Utility** is the most architecturally distinct due to its multi-server design and CLI-only interface. The three WPF utilities (Normalization, Dependency, Query Store) share more in common but still diverge in important details.

---

## 1. Connection Methods

### Python Layer

All four utilities use `pyodbc` as the ODBC bridge to SQL Server.

| Utility | Library | Connection Pattern |
|---------|---------|-------------------|
| Normalization | `pyodbc` | `with pyodbc.connect(conn_str, timeout=...) as conn:` |
| Dependency | `pyodbc` | `with pyodbc.connect(conn_str, timeout=...) as conn:` |
| Query Store | `pyodbc` | `with pyodbc.connect(conn_str, timeout=...) as conn:` |
| DDL Generator | `pyodbc` | `pyodbc.connect(conn_str, timeout=...)` wrapped via `try_sqlserver_connect()` |

**Observation:** The DDL Generator introduces a thin helper function `try_sqlserver_connect()` around `pyodbc.connect()`. The other three utilities call `pyodbc.connect()` directly. This wrapper adds no material behavior but departs from the pattern used by the other utilities.

### PowerShell / WPF Layer

All three WPF utilities (Normalization, Dependency, Query Store) use `System.Data.SqlClient.SqlConnection` for connection testing. The DDL Generator has no WPF layer.

| Utility | .NET Class Used | Retrieves Server Version |
|---------|----------------|--------------------------|
| Normalization | `System.Data.SqlClient.SqlConnection` | No |
| Dependency | `System.Data.SqlClient.SqlConnection` | No |
| Query Store | `System.Data.SqlClient.SqlConnection` | **Yes** (`$connection.ServerVersion`) |
| DDL Generator | N/A — CLI only | N/A |

**Inconsistency:** Query Store's `Test-DatabaseConnection` retrieves and displays the SQL Server version after connecting; the other two WPF utilities do not. This provides a richer connection test result in Query Store but is absent elsewhere.

---

## 2. Authentication Handling

### Python Layer (pyodbc)

All four utilities support both Windows Authentication and SQL Server Authentication. The logic is consistent in structure:

```
if windows_auth:
    connection string includes: Trusted_Connection=yes; TrustServerCertificate=yes;
else:
    connection string includes: UID=...; PWD=...; TrustServerCertificate=yes;
```

`TrustServerCertificate=yes` is present in all four utilities.

### PowerShell WPF Layer

All three WPF utilities use the same conditional logic:

```
if ($useWindowsAuth):
    "Server=...; Database=...; Integrated Security=True; TrustServerCertificate=True; Connection Timeout=5;"
else:
    "Server=...; Database=...; User ID=...; Password=...; TrustServerCertificate=True; Connection Timeout=5;"
```

**Observation — Field Name Difference Between Layers:**  
The Python ODBC strings use `Trusted_Connection=yes` while the PowerShell .NET strings use `Integrated Security=True`. This is technically correct for the respective APIs, but represents an inconsistency in terminology across the layers that could cause confusion.

Similarly, Python uses `UID` / `PWD` while PowerShell uses `User ID` / `Password`.

---

## 3. Connection String Construction

### Python Layer

| Utility | Method Signature | Reads From |
|---------|-----------------|------------|
| Normalization | `get_connection_string(self)` → `str` | Internal `self.db_config` dict |
| Dependency | `get_connection_string(self)` → `str` | Lazy-loaded `_load_database_config()` |
| Query Store | `get_connection_string(self)` → `str` | Lazy-loaded `_load_database_config()` |
| DDL Generator | `get_connection_string(self, server, user, password, db_name, driver_hint, windows_auth)` → `str` | **Caller-supplied parameters** |

**Major Inconsistency:** The DDL Generator's `get_connection_string()` is a fully parameterized factory method that takes server/credentials as arguments. The other three utilities treat this as a zero-argument method that reads from the loaded configuration. This fundamental API difference means the `ConfigLoader` interface is not interchangeable across the utilities.

The DDL Generator design is intentional due to its multi-server architecture, but the divergence from the established pattern is significant.

### ODBC Connection String Format Comparison

All four utilities produce ODBC strings in the same format:

```
DRIVER={ODBC Driver XX for SQL Server};SERVER=...;DATABASE=...;Trusted_Connection=yes;TrustServerCertificate=yes;
```

or

```
DRIVER={ODBC Driver XX for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...;TrustServerCertificate=yes;
```

This is consistent across all four Python `config_loader.py` files.

---

## 4. Configuration Management

### Config File Structure

| Utility | `database-config.json` Structure | Multi-Server Support |
|---------|----------------------------------|----------------------|
| Normalization | Flat single-server: `{ servername, database, username, password, windows_auth }` | No |
| Dependency | Flat single-server: `{ servername, database, username, password, windows_auth }` | No |
| Query Store | Flat single-server: `{ servername, database, username, password, windows_auth }` | No |
| DDL Generator | Array of servers: `{ "servers": [ { servername, port, username, password, windows_auth, databases_include, active }, ... ] }` | **Yes** |

**Key Difference:** The DDL Generator uses a fundamentally different `database-config.json` schema. This is an intentional architectural choice to support multi-server/multi-database scripting, but it means this file is not compatible with the other three utilities' config loaders.

Additionally, the DDL Generator generates a second layer of configuration in `Config/database_config/database_config_<SERVER>.json` files containing the full server/database inventory, which the other utilities do not have.

### Config File JSON Formatting Inconsistency

| Utility | `database-config.json` Indentation | Produced By |
|---------|------------------------------------|-|
| Normalization | 2-space standard JSON | Python `json.dump(indent=2)` |
| Dependency | 2-space standard JSON | Python `json.dump(indent=2)` |
| Query Store | 4-space with double-space after colon | PowerShell `ConvertTo-Json` |
| DDL Generator | 2-space standard JSON | Python `json.dump(indent=2)` |

**Inconsistency:** The Query Store `database-config.json` uses PowerShell's `ConvertTo-Json` output format, which produces 4-space indentation and a double space after colons (e.g., `"username":  "value"`). The other three files use standard 2-space Python JSON formatting. This suggests the Query Store config was saved from a PowerShell session rather than a Python script.

### `config.json` Structure Comparison

| Section Present | Normalization | Dependency | Query Store | DDL Generator |
|----------------|:---:|:---:|:---:|:---:|
| `paths` | ✅ | ✅ | ✅ | ✅ |
| `database` | ✅ | ✅ | ✅ | ✅ |
| `logging` | ✅ | ✅ | ✅ | ✅ |
| `analysis` | ✅ | ❌ | ❌ | ❌ |
| `excel` | ✅ | ❌ | ❌ | ❌ |
| `processing` | ❌ | ❌ | ✅ | ❌ |
| `files` | ❌ | ✅ | ❌ | ✅ |
| `formatting` | ❌ | ✅ | ❌ | ❌ |
| `mssql_scripter` | ❌ | ❌ | ❌ | ✅ |
| `sql_modifications` | ❌ | ❌ | ✅ | ❌ |

The core `paths`, `database`, and `logging` sections are present in all four utilities, providing a baseline of consistency. Utility-specific sections are appropriately different.

### ODBC Driver Discovery

All four utilities implement an identical `_get_available_odbc_driver()` method that tries the following drivers in priority order: 18 → 17 → 13 → 11 → Native Client 11.0 → SQL Server. This is consistent across all four `config_loader.py` files.

All four `config.json` files set `"odbc_driver": "auto"`, enabling the auto-detection path. This is fully consistent.

### Connection Timeout

All four utilities default to a 10-second connection timeout, configured in `config.json` as `"connection_timeout": 10`. This is consistent.

However, the PowerShell WPF connection test strings hardcode `Connection Timeout=5` (5 seconds) in all three WPF utilities, independent of the config file value. **This is an inconsistency between the Python and PowerShell layers** — Python respects the configured timeout; PowerShell uses a hardcoded 5-second value.

### `config.json` `paths.log_dir` Key Naming

| Utility | Log Directory Key in `config.json` |
|---------|-------------------------------------|
| Normalization | `paths.log_dir` (nested under `paths`) |
| Dependency | `paths.log_dir` |
| Query Store | `paths.logs.base_dir` (nested: `paths` → `logs` → `base_dir`) |
| DDL Generator | `paths.log_dir` |

**Inconsistency:** The Query Store uses a different nesting structure for the log directory path: `paths.logs.base_dir` instead of the flat `paths.log_dir` used by the other three utilities. While this is a minor difference, it means the `config.json` schemas are not fully interchangeable between utilities.

---

## 5. Error Handling

### Python Layer

| Utility | Exception Specificity | Uses `exc_info=True` |
|---------|----------------------|----------------------|
| Normalization | Specific: `pyodbc.Error`, `ValueError`, `KeyError`, `FileNotFoundError` | No |
| Dependency | Broad: `Exception` in most cases | No |
| Query Store | Broad: `Exception`, but uses `exc_info=True` for full tracebacks | **Yes** |
| DDL Generator | Most specific: `RuntimeError`, `pyodbc.Error`, `Exception` separately | **Yes** (partial) |

**Inconsistency:** Error handling rigor varies significantly.

- **Normalization** catches specific exception types (e.g., `pyodbc.Error` separately from generic `Exception`) but does not log tracebacks with `exc_info=True`.
- **Dependency** uses broad `except Exception` in its database access function, losing the benefit of specific error type handling.
- **Query Store** uses broad `except Exception` but adds `exc_info=True` to capture the full traceback in the log — the most useful for debugging.
- **DDL Generator** is the most thorough: it separately handles `RuntimeError` (driver not found), `pyodbc.Error` (connection failure), and generic `Exception` in `get_all_databases()`.

**Best practice recommendation for consistency:** Use specific exception types (as DDL Generator does) AND include `exc_info=True` on error logging (as Query Store does).

### PowerShell WPF Layer

All three WPF utilities use `try/catch` blocks in `Test-DatabaseConnection`. Error messages are displayed via `MessageBox` and the status field is updated.

| Utility | `connection.Close()` before `Dispose()` | `connection` null-check |
|---------|:---:|:---:|
| Normalization | **Yes** (checks `State == Open` first) | **Yes** |
| Dependency | No | **Yes** |
| Query Store | No | **Yes** |

**Inconsistency:** Normalization's `Test-DatabaseConnection` explicitly checks `$connection.State -eq [System.Data.ConnectionState]::Open` before calling `$connection.Close()`, then calls `$connection.Dispose()`. The Dependency and Query Store utilities skip the explicit `Close()` call and go directly to `Dispose()`. While `Dispose()` alone should handle cleanup for `SqlConnection`, the explicit close-before-dispose pattern in Normalization is more defensive and explicit.

### WPF UI Element Null-Safety

| Utility | Null-checks UI elements before use | Checks `$txtConnectionStatus` before use |
|---------|:---:|:---:|
| Normalization | **Yes** (`if ($script:txtConnectionStatus) {...}`) | **Yes** |
| Dependency | No — direct property access | No — direct property access |
| Query Store | No — direct property access | No — direct property access (partial) |

**Inconsistency:** Normalization's `Test-DatabaseConnection` wraps all UI element accesses in null-checks, making it defensive against missing UI controls. Dependency and Query Store directly access `$script:txtConnectionStatus.Text` and similar properties without null-checks, which could cause runtime errors if the XAML element is missing or renamed.

---

## 6. Logging

### Log File Naming Pattern

All four utilities follow the same naming convention: `log_{script_name}_{timestamp}.log`

However, Query Store has a slight variation in its `setup_logging()` implementation:

```python
# Query Store only:
log_base_name = log_filename if log_filename.startswith('log_') else f'log_{log_filename}'
```

This adds a guard against double-prefixing (e.g., if `log_filename` is already `log_something`). The other three utilities assume the caller never passes a pre-prefixed name and always prepend `log_`.

### Log File Mode

| Utility | Log File Mode | Configured Via |
|---------|--------------|----------------|
| Normalization | Default (append) | Not explicitly set |
| Dependency | Default (append) | Not explicitly set |
| Query Store | Default (append) | Not explicitly set |
| DDL Generator | **Overwrite (`"w"`)** | `config.json`: `"log_filemode": "w"` |

**Inconsistency:** The DDL Generator explicitly configures overwrite mode for log files, meaning each run overwrites the previous log. The other three utilities use the Python `logging` default (append mode), accumulating logs across runs. The DDL Generator is the only utility that exposes this option in config.

### Log Handler Setup

All four utilities use identical `logging.basicConfig()` configuration with both a `FileHandler` (file output) and `StreamHandler` (console output), and all use `force=True` to reconfigure logging. This is consistent.

### Log Format and Timestamp

All four utilities use identical defaults:
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Timestamp: `%Y%m%d_%H%M%S`
- Level: `INFO`

This is fully consistent.

---

## 7. Naming Conventions

### Python

| Convention | Assessment |
|-----------|------------|
| Class names | `PascalCase` — consistent across all utilities (`ConfigLoader`) |
| Function/method names | `snake_case` — consistent |
| Constants | `UPPER_CASE` — consistent (`SYSTEM_DATABASES`, `SQL_GET_DATABASES`, `DEFAULT_COMMAND_TIMEOUT`) |
| Config loader class name | `ConfigLoader` — consistent in all four `config_loader.py` files |
| Module name | `config_loader.py` — consistent in all four utilities |
| Script numbering | `00_`, `01_`, `02_`, ... — consistent |

### PowerShell

| Convention | Assessment |
|-----------|------------|
| Function names | `Verb-Noun` (PowerShell standard) — consistent |
| Script-level variable names | `$script:camelCase` (e.g., `$script:txtServer`) — consistent |
| Status update helper | `Update-Status` — consistent across all three WPF utilities |
| Log output helper | `Log-Output` — consistent |
| Progress update helper | `Update-Progress` — consistent |
| Python runner helper | `Run-PythonScript` — consistent |

### Naming Inconsistency — `project_base_dir` vs. `project_root`

| Utility | ConfigLoader attribute for project root |
|---------|----------------------------------------|
| Normalization | `self.project_root` |
| Dependency | `self.project_root` (Python) but `project_base_dir` key in `config.json` |
| Query Store | `self.project_root` |
| DDL Generator | `self.project_root` |

The Database Object Dependency Utility's `config.json` uses the key `paths.project_base_dir` while the `ConfigLoader` class stores the resolved path as `self.project_root`. The other utilities do not store an absolute project path in `config.json` at all (they compute it dynamically). This is a minor naming inconsistency.

---

## 8. Code Organization

### Directory Structure

All four utilities follow the same layout:

```
<Utility_Name>/
    Config/            # JSON configuration files
    Core/
        Python/        # Python scripts
        SQL/           # SQL files (Normalization, Dependency, Query Store)
        WPF/           # PowerShell WPF UI (Normalization, Dependency, Query Store)
    Logs/              # Runtime log files
    Output/            # Generated output files
```

The DDL Generator deviates in two ways:
1. No `Core/WPF/` directory (CLI only)
2. Adds a `Config/database_config/` subdirectory for per-server generated config files

### Python Script Orchestration

| Utility | Orchestration Method |
|---------|----------------------|
| Normalization | Python scripts run individually or chained via WPF buttons |
| Dependency | Has `00_run_all_scripts.py` runner that executes scripts in order via `subprocess` |
| Query Store | Has `run_all_scripts.py` runner; also uses WPF buttons |
| DDL Generator | CLI `CLI - DDL Generator Utility.py` calls scripts via `subprocess` |

**Inconsistency:** The Normalization utility does not have a dedicated run-all orchestration script. Users must run scripts individually or via the WPF interface. All other utilities have some form of batch orchestration.

### `config_loader.py` Scope and Responsibility

| Utility | `ConfigLoader` Responsibilities |
|---------|--------------------------------|
| Normalization | Config loading, validation, connection string, logging setup, output paths, save config |
| Dependency | Config loading, connection string, logging setup, file path getters, formatting getters, database name getter |
| Query Store | Config loading, connection string, logging setup, report config management, SQL file paths, output directories |
| DDL Generator | Config loading, validation, path getters, logging setup, connection string (parameterized) |

**Observation:** The `ConfigLoader` class in Normalization is the only one that includes a `save_database_config()` method (to persist UI changes back to JSON). The others are read-only config loaders. This is appropriate to the Normalization utility's WPF configuration workflow, but it represents a divergence in the class's scope.

---

## 9. General Patterns and Best Practices

### Consistent Patterns (Good)

| Pattern | All Utilities |
|---------|:---:|
| `pyodbc` for SQL Server access | ✅ |
| Centralized `ConfigLoader` class | ✅ |
| JSON configuration files | ✅ |
| File + console logging | ✅ |
| Auto-detect ODBC driver | ✅ |
| `TrustServerCertificate` in connection strings | ✅ |
| Support Windows and SQL Server authentication | ✅ |
| 10-second default connection timeout | ✅ |
| Context manager for database connections (`with pyodbc.connect(...) as conn:`) | ✅ (DDL Generator uses wrapper) |

### Cursor Handling Inconsistency

| Utility | Cursor Context Manager Pattern |
|---------|-------------------------------|
| Normalization | Explicit `cursor = connection.cursor()` + `cursor.close()` in `finally` |
| Dependency | Explicit `cursor = connection.cursor()` + `cursor.close()` in `finally` |
| Query Store (scripts 01, 04) | `with conn.cursor() as cursor:` — context manager |
| DDL Generator | Implicit via `conn.cursor()` in `get_all_databases()`, no explicit close |

**Inconsistency:** Query Store uses the preferred `with conn.cursor() as cursor:` pattern (context manager) while Normalization and Dependency use explicit cursor creation and manual close in `finally`. The DDL Generator creates a cursor without explicit cleanup. The context manager pattern is more robust and consistent with Python best practices.

### Config Loading Strategy

| Utility | Config Loading Strategy |
|---------|------------------------|
| Normalization | All config eagerly loaded in `__init__` |
| Dependency | Main config eager; `database-config.json` lazy-loaded + cached |
| Query Store | Main config + report configs eager; `database-config.json` lazy-loaded |
| DDL Generator | Main config eager; `database-config.json` loaded by individual scripts |

**Inconsistency:** Lazy vs. eager loading is inconsistent. Normalization loads everything up front (simple but risks failing early). Dependency and Query Store defer `database-config.json` to first use (avoids unnecessary reads for utility paths/logging setup). The DDL Generator doesn't load `database-config.json` in `ConfigLoader` at all — individual scripts load it themselves via `load_json_config()`.

### `default_schema` Field

Only the Normalization utility has `default_schema` in its `config.json` and `ConfigLoader`. The other utilities do not expose or use this concept. This is appropriate to Normalization's domain (analyzing table normalization within a schema), but represents a feature unique to one utility.

### Dead Code — DDL Generator

The DDL Generator's `ConfigLoader` defines:

```python
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
```

A comment explicitly notes: *"retained for reference only (getattr() is used in setup_logging)"*. This is unused dead code. The other utilities do not define this constant.

---

## 10. Detailed Inconsistency Matrix

| Dimension | Normalization | Dependency | Query Store | DDL Generator | Consistent? |
|-----------|:---:|:---:|:---:|:---:|:---:|
| `pyodbc` for SQL Server | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| `get_connection_string()` zero-argument | ✅ | ✅ | ✅ | ❌ (parameterized) | ❌ No |
| Single-server `database-config.json` schema | ✅ | ✅ | ✅ | ❌ (multi-server array) | ❌ No |
| `_validate_python_config()` in ConfigLoader | ✅ (full) | ❌ | ❌ | ✅ (partial) | ❌ No |
| `_validate_database_config()` in ConfigLoader | ✅ | ✅ | ❌ | ❌ | ❌ No |
| Cursor context manager | ❌ | ❌ | ✅ | ❌ | ❌ No |
| `exc_info=True` in error logging | ❌ | ❌ | ✅ | ✅ (partial) | ❌ No |
| Log file mode configurable | ❌ | ❌ | ❌ | ✅ | ❌ No |
| WPF interface present | ✅ | ✅ | ✅ | ❌ | — |
| WPF null-checks UI elements | ✅ | ❌ | ❌ | N/A | ❌ No |
| WPF `Close()` before `Dispose()` | ✅ | ❌ | ❌ | N/A | ❌ No |
| WPF shows server version on connect | ❌ | ❌ | ✅ | N/A | ❌ No |
| Run-all orchestration script | ❌ | ✅ | ✅ | ✅ (CLI) | ❌ No |
| `database-config.json` indent format | 2-space | 2-space | 4-space (PS) | 2-space | ❌ No |
| `paths.log_dir` vs `paths.logs.base_dir` | `log_dir` | `log_dir` | `logs.base_dir` | `log_dir` | ❌ No |
| ODBC driver auto-detect | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| `TrustServerCertificate=yes` | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| File + console logging | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| Log format `%Y%m%d_%H%M%S` | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| Connection timeout 10s (Python) | ✅ | ✅ | ✅ | ✅ | ✅ Yes |
| Connection timeout hardcoded 5s (WPF) | ✅ | ✅ | ✅ | N/A | ✅ Yes (but inconsistent with Python) |

---

## 11. Findings by Utility

### Database Normalization Analysis Utility

**Strengths:**
- Most thorough `ConfigLoader` validation (`_validate_python_config()` + `_validate_database_config()`)
- PowerShell `Test-DatabaseConnection` properly null-checks UI elements and explicitly closes connection before disposing
- Clear separation of `database-config.json` and `table-config.json`
- `save_database_config()` method supports UI round-trip

**Deviations:**
- Does not use cursor context manager (`with conn.cursor()`)
- Does not use `exc_info=True` in error logging
- No run-all orchestration Python script

---

### Database Object Dependency Utility

**Strengths:**
- `database-config.json` lazy-loading with caching avoids redundant file reads
- Broad file getter methods on `ConfigLoader` for all output files
- `formatting` section in config supports naming convention customization

**Deviations:**
- Config validation is weaker — no `_validate_python_config()` equivalent
- Uses broad `except Exception` rather than specific exception types
- PowerShell `Test-DatabaseConnection` lacks null-checks for UI elements and does not call `Close()` before `Dispose()`
- Does not use cursor context manager
- `config.json` uses `project_base_dir` absolute path (hardcoded local path) in `paths` section

---

### Query Store Analysis Utility

**Strengths:**
- Uses cursor context manager (`with conn.cursor() as cursor:`) — best pattern
- Uses `exc_info=True` for full tracebacks in error logs — best for debugging
- Most sophisticated configuration: `reports-config.json` + `active-report-config.json` enable multi-report switching
- PowerShell `Test-DatabaseConnection` shows server version and properly disables the test button during operation
- Has `reload_configs()` method for hot-reload support

**Deviations:**
- `_load_database_config()` performs no validation of the loaded config
- PowerShell `Test-DatabaseConnection` does not null-check `txtConnectionStatus`
- `config.json` log path uses non-standard nesting: `paths.logs.base_dir` vs. `paths.log_dir`
- `database-config.json` file was saved with PowerShell `ConvertTo-Json` formatting (4-space, double-space after colon) instead of Python `json.dump` standard 2-space format
- `get_database()` defaults to `"master"` if not specified (potentially risky default)

---

### DDL Generator Utility

**Strengths:**
- Multi-server architecture is well-designed and documented
- Two-phase config generation (enumerate → script) is clean
- Most specific error handling in `get_all_databases()` (separate `RuntimeError`, `pyodbc.Error`, `Exception`)
- `log_filemode` is configurable (unique feature)
- `sanitize_filename()` and `sanitize_dirname()` protect against path injection

**Deviations:**
- `get_connection_string()` API is fundamentally different from all other utilities (parameterized vs. zero-argument)
- `LOG_LEVEL_MAP` constant is dead code
- No WPF UI (CLI only) — by design, but users cannot test connections interactively
- `database-config.json` structure (`servers[]` array) is incompatible with all other utilities
- Config validation in `_validate_config()` only checks `paths` and `logging` sections; `database` section is not validated in `ConfigLoader`
- `config.json` uses absolute path for `workspace_dir` (hardcoded: `"C:\\Advanced_SQL_Server_Toolkit\\DDL_Generator_Utility"`) — not portable

---

## 12. Opportunities for Standardization

The following areas represent the highest-value opportunities for future standardization (analysis only — no changes made):

1. **Cursor context manager**: Adopt `with conn.cursor() as cursor:` uniformly across all utilities (currently only Query Store uses it).

2. **Error logging with `exc_info=True`**: Use `logger.error(..., exc_info=True)` uniformly to capture full tracebacks (currently only Query Store and partial DDL Generator).

3. **PowerShell `Test-DatabaseConnection`**: Normalize to include null-checks on all UI elements and explicit `Close()` before `Dispose()` (currently only Normalization does both).

4. **`config.json` log path key**: Standardize on `paths.log_dir` (currently Query Store uses `paths.logs.base_dir`).

5. **`database-config.json` JSON formatting**: Ensure all config files use consistent 2-space indentation (Query Store's file uses PowerShell formatting).

6. **Config validation**: Add `_validate_database_config()` to all `ConfigLoader` implementations that perform database access.

7. **Orchestration script**: Add a `run_all_scripts.py` to Normalization for consistency with the other utilities.

8. **Remove `LOG_LEVEL_MAP` dead code** from DDL Generator's `ConfigLoader`.

9. **WPF connection test timeout**: Align the hardcoded 5-second timeout in PowerShell with the configurable value from `config.json`.

10. **WPF server version display**: Decide whether to standardize the server version display in `Test-DatabaseConnection` across all three WPF utilities (currently only Query Store shows it).

---

*End of Analysis — Read-only. No files were modified.*

