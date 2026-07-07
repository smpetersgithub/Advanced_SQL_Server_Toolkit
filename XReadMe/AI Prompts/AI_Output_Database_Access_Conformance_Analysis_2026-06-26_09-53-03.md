# Database Access Conformance Analysis
**Generated:** 2026-06-26 09:53:03  
**Analysis Type:** Read-Only Conformance Review  
**Scope:** SQL Server database access patterns across four utilities

---

## Utilities Under Review

| # | Utility | Type | Primary Languages |
|---|---------|------|-------------------|
| 1 | `Database_Normalization_Analysis_Utility` | WPF + Python | PowerShell, Python |
| 2 | `Database_Object_Dependency_Utility` | WPF + Python | PowerShell, Python |
| 3 | `Query_Store_Analysis_Utility` | WPF + Python | PowerShell, Python |
| 4 | `DDL_Generator_Utility` | CLI + Python | Python only |

---

## Executive Summary

Three of the four utilities follow a broadly consistent pattern for SQL Server database access using `pyodbc` in Python and `.NET SqlClient` in PowerShell WPF. The fourth utility, `DDL_Generator_Utility`, intentionally deviates because it must connect to **multiple servers**, requiring a parameterized connection model.

Several concrete inconsistencies were identified:

1. **🔴 CRITICAL — Field name mismatch:** `Database_Object_Dependency_Utility` uses `"server"` as the server key in `database-config.json`, while all other utilities (and its own Python `config_loader.py` validation) use `"servername"`. This is a functional defect that will cause a `ValueError` when any Python script in that utility attempts to load a database connection.
2. **🟡 MODERATE — Absolute path in config:** `Database_Object_Dependency_Utility`'s `config.json` contains a hardcoded absolute path (`project_base_dir`), deviating from the relative-path pattern used by all other utilities.
3. **🟡 MODERATE — config.json structure divergence:** The `Query_Store_Analysis_Utility` has a significantly more complex and differently structured `config.json` with nested `paths.logs`, `paths.config`, and additional `processing`/`sql_modifications` sections not found in the others.
4. **🟡 MODERATE — DDL Generator's `get_connection_string()` signature:** Takes explicit parameters (`server`, `user`, `password`, `db_name`, etc.), unlike the zero-argument `get_connection_string()` in all other utilities.
5. **🟢 MINOR — Path separator inconsistency:** `DDL_Generator_Utility` uses Windows backslashes (`\\`) in `config.json` relative paths; all other utilities use forward slashes (`/`).
6. **🟢 MINOR — Logging `log_filemode`:** `DDL_Generator_Utility` has an extra `log_filemode` key in the `logging` section; no other utility includes it.
7. **🟢 MINOR — Root-level `config.json` metadata:** Only `Database_Object_Dependency_Utility` and `Query_Store_Analysis_Utility` include `description` and `version` fields at the root of `config.json`; the other two do not.
8. **🟢 MINOR — PowerShell project-root resolution:** Three different approaches are used to resolve the project root in the PowerShell layer.

---

## Section 1 — Connection Methods

### Python Layer
All four utilities use `pyodbc` as the SQL Server connectivity library. Connections are established using `pyodbc.connect(connection_string, timeout=n)`.

All three utilities that connect to a single database (`Normalization`, `Object Dependency`, `Query Store`) use Python's context manager (`with pyodbc.connect(...) as conn:`) ensuring connections are closed automatically on completion or error.

The `DDL_Generator_Utility` also uses a context manager (`with try_sqlserver_connect(conn_str, ...) as conn:`), with a thin wrapper function `try_sqlserver_connect()` to allow a configurable timeout.

### PowerShell (WPF) Layer
All three WPF-based utilities (`Normalization`, `Object Dependency`, `Query Store`) use `.NET`'s `System.Data.SqlClient.SqlConnection` **only for the interactive "Test Connection" button** in the UI. They do **not** use SqlClient for actual data extraction, which is delegated to the Python layer.

The PowerShell connection string format used for testing is:
- **Windows Auth:** `"Server=$server;Database=$database;Integrated Security=True;TrustServerCertificate=True;Connection Timeout=5;"`
- **SQL Auth:** `"Server=$server;Database=$database;User ID=$username;Password=$password;TrustServerCertificate=True;Connection Timeout=5;"`

This is **consistent** across all three WPF utilities.

### DDL Generator
Has no WPF layer. It is a CLI-only Python utility. No PowerShell connection testing exists.

---

## Section 2 — Connection String Construction

### Python `get_connection_string()` — Pattern Comparison

All four utilities build ODBC connection strings using the same format:

```
DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;
# OR
DRIVER={driver};SERVER={server};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes;
```

This format is **fully consistent** across all utilities. `TrustServerCertificate=yes` is uniformly present in all connection strings.

### Key Difference — Method Signature

| Utility | `get_connection_string()` Signature | Rationale |
|---------|--------------------------------------|-----------|
| Normalization | `get_connection_string(self)` — no args, reads `self.db_config` | Single server/database |
| Object Dependency | `get_connection_string(self)` — no args, calls `self._load_database_config()` | Single server/database |
| Query Store | `get_connection_string(self)` — no args, calls `self._load_database_config()` | Single server/database |
| **DDL Generator** | `get_connection_string(self, server, user, password, db_name, driver_hint, windows_auth)` — **parameterized** | **Multiple servers** — credentials passed by caller at runtime |

The DDL Generator's method is intentionally different because it must build connection strings for multiple servers dynamically. The docstring explicitly acknowledges this deviation:

> *"This method is intentionally parameterized because the DDL Generator operates against multiple servers. Credentials are supplied by the caller… rather than from a single pre-loaded config, which is why the signature differs from the zero-argument `get_connection_string()` found in the single-server utilities."*

This is a **justified and documented** deviation.

---

## Section 3 — Authentication Handling

### Configuration Key: `windows_auth`
All four utilities support both Windows Authentication and SQL Server Authentication. The boolean key `windows_auth` in `database-config.json` controls which is used.

- **Windows Auth (`true`):** Uses `Trusted_Connection=yes`, ignores `username`/`password`.
- **SQL Auth (`false` or omitted):** Requires `username` and `password`.

This is **consistent** across all utilities.

### Validation When `windows_auth = false`
Three utilities (`Normalization`, `Object Dependency`, `Query Store`) perform explicit validation that `username` and `password` are present when `windows_auth` is not set. DDL Generator does not validate auth fields in the config_loader — validation is implicit (a `KeyError` would occur when reading `server_info['username']` from the servers array during script execution).

### PowerShell UI Auth Toggle
All three WPF utilities include a `chkWindowsAuth` checkbox that enables/disables the `txtUsername` and `txtPassword` fields. The event handler pattern is **identical** across all three:

```powershell
$script:chkWindowsAuth.Add_Checked({
    if ($script:txtUsername) { $script:txtUsername.IsEnabled = $false }
    if ($script:txtPassword) { $script:txtPassword.IsEnabled = $false }
})
$script:chkWindowsAuth.Add_Unchecked({
    if ($script:txtUsername) { $script:txtUsername.IsEnabled = $true }
    if ($script:txtPassword) { $script:txtPassword.IsEnabled = $true }
})
```

This pattern is **consistent**.

---

## Section 4 — Configuration Management

### 4.1 `database-config.json` — Server Key Name

> 🔴 **CRITICAL INCONSISTENCY**

| Utility | JSON Key Used for Server Name |
|---------|-------------------------------|
| Normalization | `"servername"` |
| **Object Dependency** | **`"server"`** ← **DIFFERENT** |
| Query Store | `"servername"` |
| DDL Generator | `"servername"` (inside each server entry in `servers` array) |

The `Database_Object_Dependency_Utility`'s `database-config.json` uses `"server"` as the key, while all other utilities use `"servername"`.

**Additionally**, the `config_loader.py` for `Database_Object_Dependency_Utility` validates for `"servername"`:

```python
required_keys = ['servername', 'database']
missing_keys = [key for key in required_keys if key not in config]
if missing_keys:
    raise ValueError(f"Missing required keys in database config: {', '.join(missing_keys)}")
```

And the `get_connection_string()` method reads `db_config['servername']`. Since the JSON file has `"server"` not `"servername"`, any Python script that attempts to establish a connection will raise a `ValueError: Missing required keys in database config: servername`.

**The PowerShell layer is consistent with the JSON file** (reads/writes `$dbConfig.server` and `server = $server`), but is **inconsistent with the Python config_loader** (which expects `servername`).

### 4.2 `database-config.json` — Structure

| Utility | Structure Type |
|---------|---------------|
| Normalization | Flat object: `{username, servername, database, password, windows_auth}` |
| Object Dependency | Flat object: `{username, windows_auth, server, password, database}` |
| Query Store | Flat object: `{username, servername, database, password, windows_auth}` |
| **DDL Generator** | Nested array: `{servers: [{parent_name, servername, port, username, password, windows_auth, databases_include, active}]}` |

Normalization, Object Dependency, and Query Store all use a flat single-server object. DDL Generator uses a `servers` array to support multiple server connections — this is **intentionally different** due to its multi-server architecture.

### 4.3 `config.json` — Structure Comparison

| Section / Key | Normalization | Object Dependency | Query Store | DDL Generator |
|---------------|:---:|:---:|:---:|:---:|
| `description` (root) | ✗ | ✓ | ✓ | ✗ |
| `version` (root) | ✗ | ✓ | ✓ | ✗ |
| `paths.database_config` | ✓ | ✓ | ✓ | ✗ |
| `paths.log_dir` or `paths.logs.base_dir` | ✗ | ✓ | ✓ (nested) | ✓ |
| `paths.output_directory` or `paths.output_dir` | ✓ | ✓ | ✗ (per-report) | ✓ |
| `database.odbc_driver` | ✓ | ✓ | ✓ | ✓ |
| `database.connection_timeout` | ✓ | ✓ | ✓ | ✓ |
| `database.default_schema` | ✓ | ✗ | ✗ | ✗ |
| `logging.log_level` | ✓ | ✓ | ✓ | ✓ |
| `logging.log_format` | ✓ | ✓ | ✓ | ✓ |
| `logging.timestamp_format` | ✓ | ✓ | ✓ | ✓ |
| `logging.log_filemode` | ✗ | ✗ | ✗ | ✓ |
| `analysis` section | ✓ | ✗ | ✗ | ✗ |
| `excel` section | ✓ | ✗ | ✗ | ✗ |
| `processing` section | ✗ | ✗ | ✓ | ✗ |
| `sql_modifications` section | ✗ | ✗ | ✓ | ✗ |
| `formatting` section | ✗ | ✓ | ✗ | ✗ |
| `mssql_scripter` section | ✗ | ✗ | ✗ | ✓ |
| `files` section | ✗ | ✓ | ✗ | ✓ |
| `paths.java_source_dirs` | ✗ | ✓ | ✗ | ✗ |
| `paths.project_base_dir` (absolute) | ✗ | ✓ | ✗ | ✗ |

Utility-specific sections (`analysis`, `excel`, `mssql_scripter`, `formatting`, `processing`, `sql_modifications`) are expected and appropriate — they reflect each utility's unique functional requirements.

The key structural inconsistencies are:
- **`description`/`version` fields** missing from Normalization and DDL Generator.
- **`paths.project_base_dir`** in Object Dependency is a hardcoded absolute path — deviates from the project's relative-path pattern.
- **`logging.log_filemode`** present only in DDL Generator.
- **Query Store `paths`** is nested differently: `paths.logs.base_dir` vs flat `paths.log_dir`.
- **`paths.output_directory`** vs `paths.output_dir` — key names differ between Normalization and Object Dependency.

### 4.4 Path Separators in `config.json`

> 🟢 **MINOR INCONSISTENCY**

| Utility | Path Separator Used in Relative Paths |
|---------|--------------------------------------|
| Normalization | Forward slash `/` (e.g., `"Config/database-config.json"`) |
| Object Dependency | Forward slash `/` (e.g., `"Config/database-config.json"`) but also backslash in absolute path |
| Query Store | Forward slash `/` |
| **DDL Generator** | **Backslash `\\`** (e.g., `"Config\\database_config"`) |

Python's `pathlib.Path` normalizes slashes on all platforms, so this does not cause runtime failures, but it is an inconsistency in style.

---

## Section 5 — ODBC Driver Detection

All four utilities implement a `_get_available_odbc_driver()` private method with **identical logic**:

```python
drivers_to_try = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server"
]
available_drivers = pyodbc.drivers()
for driver in drivers_to_try:
    if driver in available_drivers:
        return driver

raise RuntimeError(
    f"No compatible ODBC driver found for SQL Server.\n"
    f"Available drivers: {', '.join(available_drivers)}\n"
    f"Please install 'ODBC Driver 17 for SQL Server' or newer.\n"
    f"Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
)
```

The driver preference order, error message, and download URL are **identical** across all four utilities. The public `get_odbc_driver()` method also follows the same pattern: return the explicitly configured driver if not `"auto"`, otherwise auto-detect.

This is one of the most **consistently implemented** aspects across all utilities.

---

## Section 6 — Error Handling

### Python Layer

| Aspect | Normalization | Object Dependency | Query Store | DDL Generator |
|--------|:---:|:---:|:---:|:---:|
| Config errors: `(FileNotFoundError, ValueError, KeyError)` in `main()` | ✓ | ✓ | ✓ | ✓ |
| `sys.exit(1)` on fatal error | ✓ | ✓ | ✓ | ✓ |
| `pyodbc.Error` caught separately | ✓ | — (not in shown scripts) | ✓ | ✓ |
| `exc_info=True` on logger.error | ✓ | ✓ | ✓ | ✓ |
| Broad `except Exception` in main | ✓ | — | ✓ | ✓ |
| Helper functions return `None`/`False` on non-fatal error | ✗ | — | ✗ | ✓ |

**Normalization** and **Query Store** use a common `except Exception as e: logger.error(...); sys.exit(1)` outer catch in `main()`.

**DDL Generator** uses a hybrid approach: helper functions like `get_all_databases()` and `load_json_config()` return `None`/empty list on error (allowing the script to skip failed servers), while `main()` catches exceptions for termination. This is appropriate for a multi-server utility where one server failure should not stop all others.

**Object Dependency** does not connect to SQL Server in `01_extract_complete_ui_mapping.py` (Java file scanning only); database-accessing scripts were not included in the review, but the `config_loader.py` validation and connection string patterns are available.

### PowerShell Layer

All three WPF utilities use `try/catch` blocks around connection testing, database config loading, and config file saving. Error messages are shown via `[System.Windows.MessageBox]::Show(...)`. Error details are logged to `Write-Host "[ERROR] ..."`. This pattern is **consistent** across all three WPF utilities.

---

## Section 7 — Logging

### Python Logging Setup

All four utilities implement a `setup_logging(script_name)` method in `ConfigLoader`. The method:
1. Creates the `Logs` directory if it does not exist
2. Generates a timestamped log filename (`log_{script_name}_{timestamp}.log`)
3. Calls `logging.basicConfig()` with both `FileHandler` and `StreamHandler`
4. Returns the `Path` to the created log file

This pattern is **consistent** across all four utilities.

#### Minor Differences in `setup_logging()`

| Utility | Log Filename Prefix | `force=True` in basicConfig |
|---------|--------------------|-----------------------------|
| Normalization | `log_{script_name}_{timestamp}.log` | ✓ |
| Object Dependency | `log_{script_name}_{timestamp}.log` | ✓ |
| Query Store | If `log_filename` already starts with `log_`, uses as-is; otherwise prepends `log_`. Adds `_{timestamp}` suffix. | ✓ |
| DDL Generator | `log_{script_name}_{timestamp}.log` | ✓ |

The **Query Store** has a slightly different prefix check: `log_base_name = log_filename if log_filename.startswith('log_') else f'log_{log_filename}'`. The other three utilities unconditionally prepend `log_`. This is a minor behavioral difference but produces the same output when callers pass consistent script names (which they all do).

#### `log_filemode` (DDL Generator only)
The `DDL_Generator_Utility` is the only utility with a `log_filemode` setting in `config.json` (currently `"a"` for append). The other three utilities hardcode `logging.basicConfig()` without an explicit filemode (defaulting to `"a"` append). Functionally equivalent, but only DDL Generator exposes this as a configurable setting.

### PowerShell Logging
All three WPF utilities log to the UI's `txtOutputLog` text box via a `Log-Output` function. Normalization and Object Dependency have a local `Log-Output` function with a timestamped message format `[$timestamp] $Message`. Query Store follows the same approach. All three write to `Write-Host` in parallel for console visibility.

---

## Section 8 — Naming Conventions

### Python Classes and Methods

All four utilities define a class named `ConfigLoader` in `config_loader.py`. Method names follow the same `get_*()` / `_get_*()` (private) / `setup_*()` pattern across all utilities. This is **consistent**.

### Python Script Naming

All scripts use a numeric prefix ordering pattern (`00_`, `01_`, `02_`, etc.) with descriptive snake_case names. This is **consistent** across all three utilities that have numbered scripts.

### PowerShell Function Naming

| Category | Normalization | Object Dependency | Query Store |
|----------|---------------|-------------------|-------------|
| Init function | `Initialize-NormalizationAnalysis` | `Initialize-DatabaseObjectDependency` | `Initialize-QueryStoreAnalysis` |
| Load DB config | `Load-DatabaseConfig` | `Load-DatabaseConfiguration` | `Load-DatabaseConfiguration` |
| Save DB config | `Save-DatabaseConfiguration` | `Save-DatabaseConfiguration` | `Save-DatabaseConfiguration` |
| Test connection | `Test-DatabaseConnection` | `Test-DatabaseConnection` | `Test-DatabaseConnection` |
| Log message | `Log-Output` | `Log-Output` | `Log-Output` |
| Update status | `Update-Status` | — (direct assignment) | — (direct assignment) |
| Update progress | `Update-Progress` | — | — |

**Minor inconsistency:** `Load-DatabaseConfig` (Normalization) vs `Load-DatabaseConfiguration` (Object Dependency, Query Store).

### Config File Key Names (PowerShell `Save-DatabaseConfiguration`)

| Utility | Key Written for Server Name |
|---------|-----------------------------|
| Normalization | `servername` |
| **Object Dependency** | **`server`** ← DIFFERENT |
| Query Store | `servername` |

Object Dependency's `Save-DatabaseConfiguration` writes `server = $server` to the JSON file. This is consistent with its `database-config.json` file but inconsistent with the Python config_loader, which expects `servername`.

---

## Section 9 — Code Organization

### Project Structure Consistency

All four utilities follow the same directory layout:

```
<UtilityName>/
├── Config/
│   ├── config.json
│   ├── database-config.json
│   ├── database-config-demo.json
│   └── cleanup-config.json
├── Core/
│   └── Python/
│       ├── config_loader.py
│       ├── 00_*.py  (or 01_*.py)
│       ├── ...
│       └── __pycache__/
│   └── WPF/           (not DDL Generator)
│       ├── Scripts/
│       └── Assets/
├── Output/
└── Logs/              (Object Dependency, Query Store, DDL Generator)
```

This structure is **consistent** across all utilities.

### Python Root Determination

All four utilities use the same approach to determine the project root from `config_loader.py`:

```python
project_root = Path(__file__).parent.parent.parent
```

This navigates up: `Core/Python/` → `Core/` → `ProjectRoot`. The pattern is **identical** across all four.

### PowerShell Project Root Determination

> 🟡 **Three different approaches**

| Utility | How Project Root Is Determined in PS1 |
|---------|---------------------------------------|
| Normalization | Uses a passed `$ScriptDirectory` parameter, then navigates up 3 levels: `Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptRoot))` |
| Object Dependency | Uses `$PSScriptRoot` (or `$MyInvocation.MyCommand.Path` as fallback), then navigates up 3 levels |
| Query Store | Receives `$ProjectRoot` directly as a parameter from `Main.ps1` (no navigation needed) |

These approaches all result in the same project root path, but the mechanisms differ. The Query Store's approach is the most direct (the caller resolves the path before passing it in), while Normalization and Object Dependency compute it internally.

---

## Section 10 — General Coding Patterns and Best Practices

### Consistent Practices (All Four Utilities)

| Practice | Status |
|----------|--------|
| Centralized `ConfigLoader` class in `config_loader.py` | ✓ All four |
| `pyodbc` used for SQL Server connections in Python | ✓ All four |
| `TrustServerCertificate=yes` in all connection strings | ✓ All four |
| `with` context manager for `pyodbc` connections | ✓ All four |
| Parameterized queries (no string concatenation for SQL) | ✓ Normalization (uses `?` placeholders) |
| `sys.exit(1)` on fatal errors | ✓ All four |
| `logging.basicConfig(force=True)` to allow re-initialization | ✓ All four |
| `encoding='utf-8'` when opening JSON files | ✓ All four |
| UTF-8 without BOM for saving files from PowerShell | ✓ All three WPF utilities |
| Unique temp file GUIDs to prevent conflicts (PowerShell) | ✓ Normalization, Query Store |
| `if __name__ == "__main__": main()` | ✓ All Python scripts |

### Deviations and Areas for Improvement

| # | Utility | Issue | Severity |
|---|---------|-------|----------|
| 1 | Object Dependency | `database-config.json` uses `"server"` but `config_loader.py` validates/reads `"servername"` | 🔴 Critical |
| 2 | Object Dependency | PowerShell saves `server = $server` but Python expects `servername` | 🔴 Critical |
| 3 | Object Dependency | `config.json` contains a hardcoded absolute path (`project_base_dir`) | 🟡 Moderate |
| 4 | DDL Generator | `get_connection_string()` has a different method signature (parameterized) | 🟡 Moderate (justified) |
| 5 | Query Store | `config.json` `paths` structure is nested differently from other utilities | 🟡 Moderate |
| 6 | DDL Generator | Relative paths in `config.json` use backslash `\\` instead of forward slash `/` | 🟢 Minor |
| 7 | DDL Generator | `logging.log_filemode` present; not present in other utilities | 🟢 Minor |
| 8 | Normalization, DDL Generator | Missing `description` and `version` metadata in `config.json` | 🟢 Minor |
| 9 | Normalization | `Load-DatabaseConfig` function name vs `Load-DatabaseConfiguration` in other two | 🟢 Minor |
| 10 | Query Store | `setup_logging()` has a `startswith('log_')` check; others do not | 🟢 Minor |
| 11 | Normalization | `ConfigLoader.__init__` loads both `db_config` and `table_config` eagerly; others are lazy | 🟢 Minor |
| 12 | Object Dependency | Missing `Update-Status` / `Update-Progress` helper functions; uses direct property assignment | 🟢 Minor |

---

## Section 11 — Detailed Inconsistency: `database-config.json` Key Name (Object Dependency)

This is the most significant finding and warrants additional detail.

**File:** `Config/database-config.json`  
**Current Content:**
```json
{
    "username":  "developer",
    "windows_auth":  true,
    "server":  "WIN29LYC64\\MSSQLSERVER01",
    "password":  "developer",
    "database":  "foo"
}
```

**Python `config_loader.py` (`_load_database_config`):**
```python
required_keys = ['servername', 'database']
missing_keys = [key for key in required_keys if key not in config]
if missing_keys:
    raise ValueError(f"Missing required keys in database config: {', '.join(missing_keys)}")
# ...
server = db_config['servername']   # KeyError if key is 'server'
```

**Result:** Any Python script that calls `config.get_connection_string()` will raise:
```
ValueError: Missing required keys in database config: servername
```

**PowerShell `Load-DatabaseConfiguration`:**
```powershell
if ($dbConfig.server) {
    $script:txtServer.Text = $dbConfig.server    # Reads 'server' - correct for JSON
}
```

**PowerShell `Save-DatabaseConfiguration`:**
```powershell
$dbConfig = @{
    server       = $server                       # Writes 'server' - correct for JSON
    database     = $database
    ...
}
```

The PowerShell layer is internally consistent with the JSON file, but the Python layer expects `servername`. One of the two must be corrected for the utility to function:
- Either rename the key in `database-config.json` from `"server"` to `"servername"` **and** update the PowerShell `Load-DatabaseConfiguration`/`Save-DatabaseConfiguration` to use `servername`
- Or update the Python `config_loader.py` to accept `"server"` as the key.

The standard established by the other two single-server utilities (Normalization, Query Store) is `"servername"`.

---

## Section 12 — Summary Conformance Scorecard

| Category | Normalization | Object Dependency | Query Store | DDL Generator |
|----------|:---:|:---:|:---:|:---:|
| Connection method (pyodbc) | ✅ | ✅ | ✅ | ✅ |
| Connection string format | ✅ | ✅ | ✅ | ✅ |
| Authentication support (Windows + SQL) | ✅ | ✅ | ✅ | ✅ |
| ODBC driver auto-detection | ✅ | ✅ | ✅ | ✅ |
| `TrustServerCertificate=yes` | ✅ | ✅ | ✅ | ✅ |
| `database-config.json` key: `servername` | ✅ | ❌ | ✅ | ✅ |
| Python ConfigLoader expects `servername` | ✅ | ❌ (mismatch) | ✅ | N/A |
| PowerShell saves `servername` | ✅ | ❌ | ✅ | N/A |
| Relative paths in config.json | ✅ | ⚠️ (1 abs path) | ✅ | ⚠️ (backslash) |
| Consistent config.json root metadata | ❌ | ✅ | ✅ | ❌ |
| Logging pattern | ✅ | ✅ | ✅ | ✅ |
| Python project root detection | ✅ | ✅ | ✅ | ✅ |
| Error handling pattern | ✅ | ✅ | ✅ | ✅ |
| `setup_logging()` method | ✅ | ✅ | ✅ | ✅ |
| UTF-8 without BOM for file saves | ✅ | ✅ | ✅ | N/A |

**Legend:** ✅ Conformant | ❌ Non-conformant | ⚠️ Partial | N/A Not applicable

---

## Section 13 — Recommendations (Informational — No Code Changes Made)

The following are observations for consideration. **No code was modified as part of this analysis.**

1. **Resolve the `server` vs `servername` key conflict** in `Database_Object_Dependency_Utility`. Standardizing on `"servername"` would align with all other utilities and fix the Python connection path.

2. **Replace the hardcoded absolute `project_base_dir` path** in `Database_Object_Dependency_Utility`'s `config.json` with a relative path or remove it, as all other utilities derive the project root dynamically from `__file__`.

3. **Standardize `config.json` root-level metadata** (`description`, `version`) — either add to all utilities or remove from the two that have them, for consistency.

4. **Standardize `logging.log_filemode`** — either add to all utilities (making log file behavior configurable) or keep hardcoded in all and remove from DDL Generator.

5. **Standardize path separators** in `config.json` relative paths — forward slashes are more portable and used by three of the four utilities.

6. **Rename `Load-DatabaseConfig`** in Normalization to `Load-DatabaseConfiguration` to match the naming used in Object Dependency and Query Store.

7. **Consider a shared base ConfigLoader** — The `_get_available_odbc_driver()`, `get_odbc_driver()`, `get_connection_timeout()`, and `setup_logging()` implementations are nearly identical across all four utilities. A shared base class or common module could reduce duplication.

---

*Report generated by GitHub Copilot — Read-only analysis. No files were modified.*

