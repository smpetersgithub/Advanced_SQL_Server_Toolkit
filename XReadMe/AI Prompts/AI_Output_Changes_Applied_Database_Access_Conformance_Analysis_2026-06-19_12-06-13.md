# Changes Applied — Database Access Conformance Analysis
**Session:** 2026-06-19 12:06:13
**Based on report:** `AI_Output_Database_Access_Conformance_Analysis_2026-06-19_11-46-40.md`
**Prior sessions:** 2026-06-19_11-20-17, 2026-06-19_11-42-14

---

## Summary

This session applied all 9 identified issues from the conformance analysis report (Priority 1, 2, and 3 fixes). One reported issue (Issue 8 — QSAU Main.ps1 missing STA re-launch block) was investigated and confirmed as incorrect in the report; QSAU already has a proper STA re-launch block at lines 66–80 using `Write-Log`. That fix was skipped.

---

## Changes Applied

### P1 — Critical Runtime Bugs

#### Fix 1: QSAU `06_lookup_query_by_id.py` — Out-of-scope `config` reference (C2 bug)
**File:** `Query_Store_Analysis_Utility\Core\Python\06_lookup_query_by_id.py`
**Issue:** `lookup_query_by_id()` called `config.get_connection_timeout()` where `config` was not in scope (it is a local variable in `main()`). This would raise `NameError` at runtime. The same pattern was fixed in scripts 01, 02, 04 in a prior session but script 06 was missed.
**Fix applied:**
- Added `connection_timeout=10` parameter to `lookup_query_by_id()` signature and docstring
- Replaced `timeout=config.get_connection_timeout()` with `timeout=connection_timeout` inside the function
- Updated call site in `main()` to pass `config.get_connection_timeout()` as the 4th positional argument

#### Fix 2: DODU `config_loader.py` — SyntaxError at lines 268 and 293
**File:** `Database_Object_Dependency_Utility\Core\Python\config_loader.py`
**Issue:** Two methods had the closing `"""` of their docstring on the same line as the first code statement, causing a Python `SyntaxError`. This was introduced by a prior session's edit (session 2026-06-19_11-42-14 added the docstrings but mis-placed the line breaks). Confirmed with `python -m py_compile`.
**Fix applied:**
- Line 268: Split `"""        db_config = self._load_database_config()` into two separate lines
- Line 293: Split `"""Get the database name..."""        return self._database_config.get('database', '')` into properly separated lines
- Verified: `python -m py_compile` passes with exit code 0

---

### P2 — Standardization Fixes

#### Fix 3: DNAU — Rename `config_loader` instance to `config` in all 5 scripts
**Files:**
- `Database_Normalization_Analysis_Utility\Core\Python\00_populate_columns_from_database.py`
- `Database_Normalization_Analysis_Utility\Core\Python\01_populate_keys_from_database.py`
- `Database_Normalization_Analysis_Utility\Core\Python\02_analyze_functional_dependencies.py`
- `Database_Normalization_Analysis_Utility\Core\Python\03_classify_dependency_relevance.py`
- `Database_Normalization_Analysis_Utility\Core\Python\04_generate_excel_report.py`

**Issue:** DNAU scripts used `config_loader = ConfigLoader()` (inconsistent with DODU, QSAU which use `config = ConfigLoader()`). DNAU scripts also used a local variable named `config` for the dict returned by `get_database_config()`, creating a naming collision.

**Fix applied (scripts 00, 01, 02):**
- Renamed `config_loader = ConfigLoader()` → `config = ConfigLoader()`
- Renamed `config = config_loader.get_database_config()` → `db_config = config.get_database_config()`
- Updated all dict accesses: `config[...]` → `db_config[...]`, `config.get(...)` → `db_config.get(...)`
- Updated all ConfigLoader method calls: `config_loader.xxx()` → `config.xxx()`
- Updated `save_database_config(config)` → `save_database_config(db_config)`

**Fix applied (scripts 03, 04):**
- Renamed `config_loader = ConfigLoader()` → `config = ConfigLoader()`
- Updated all method calls from `config_loader.xxx()` → `config.xxx()`
- (No dict clash in these scripts — they do not call `get_database_config()`)

**Verification:** All 5 scripts pass `python -m py_compile` with exit code 0.

#### Fix 4: DDLG `config_loader.py` — `get_odbc_driver()` ignores configured value
**File:** `DDL_Generator_Utility\Core\Python\config_loader.py`
**Issue:** `get_odbc_driver()` always called `_get_available_odbc_driver()` (auto-detect), ignoring any value set in `config.json`. DODU and QSAU check the config first and only fall back to auto-detect if the value is `'auto'` or absent.
**Fix applied:**
- Added config-read logic: reads `config['database']['odbc_driver']`
- If the value is set and is not `'auto'`, returns the configured value directly
- Falls back to `_get_available_odbc_driver()` only if value is `'auto'` or not set
- Updated docstring accordingly

---

### P3 — Low-Priority Fixes

#### Fix 5: DDLG `config_loader.py` — Missing `int()` cast in `get_connection_timeout()`
**File:** `DDL_Generator_Utility\Core\Python\config_loader.py`
**Issue:** `get_connection_timeout()` returned whatever type was in the JSON (could be a string if user types `"10"` instead of `10`), while DODU and QSAU cast to `int()`. This could cause `pyodbc.connect(timeout=...)` to fail with a type error.
**Fix applied:** Wrapped return value with `int(...)`:
```python
return int(self.config.get('database', {}).get('connection_timeout', 10))
```

#### Fix 6: DODU `database-config-demo.json` — Missing `database` and `windows_auth` fields
**File:** `Database_Object_Dependency_Utility\Config\database-config-demo.json`
**Issue:** The demo config was missing the `database` key (which `config_loader.py` reads and validates) and the `windows_auth` key (which controls authentication mode). All other utilities include both fields in their demo configs.
**Fix applied:** Added `"database": "database"` and `"windows_auth": false` to the JSON.

#### Fix 7: DNAU `database-config-demo.json` — Missing `windows_auth` field
**File:** `Database_Normalization_Analysis_Utility\Config\database-config-demo.json`
**Issue:** The demo config had `servername`, `database`, `username`, `password` but was missing `windows_auth`. All other utilities include this field.
**Fix applied:** Added `"windows_auth": false` to the JSON.

#### Fix 8: QSAU `config_loader.py` — Deprecated `logging.getLevelName()` usage
**File:** `Query_Store_Analysis_Utility\Core\Python\config_loader.py`
**Issue:** `setup_logging()` used `logging.getLevelName(self.get_log_level())` which is deprecated since Python 3.4 and removed in 3.12. It also returned a string like `"Level 20"` when passed a string, which could cause `basicConfig()` to default to WARNING unexpectedly.
**Fix applied:** Replaced with:
```python
level=getattr(logging, self.get_log_level().upper(), logging.INFO),
```
This is the idiomatic, forward-compatible approach used by DODU and DNAU.

#### Fix 9: DODU `DatabaseObjectDependencyFunctions.ps1` — `$PSScriptRoot` unreliable when dot-sourced
**Files:**
- `Database_Object_Dependency_Utility\Core\WPF\Scripts\DatabaseObjectDependencyFunctions.ps1`
- `Database_Object_Dependency_Utility\Core\WPF\Scripts\Main.ps1`

**Issue:** `Initialize-DatabaseObjectDependency` used `$PSScriptRoot` (with a `$MyInvocation.MyCommand.Path` fallback) to locate the Scripts directory. When a script is dot-sourced, `$PSScriptRoot` resolves to the caller's directory, not the file's own directory. `Main.ps1` already correctly computes `$ScriptDir` (the Scripts folder) and should pass it explicitly. DNAU and QSAU pass `$ScriptDir` explicitly to their respective init functions.

**Fix applied:**
- `DatabaseObjectDependencyFunctions.ps1`: Added `[Parameter(Mandatory)] [string]$ScriptDirectory` parameter to `Initialize-DatabaseObjectDependency`; replaced `$ScriptRoot = $PSScriptRoot; if (-not $ScriptRoot) { ... }` with `$ScriptRoot = $ScriptDirectory`
- `Main.ps1` line 83: Updated call to `Initialize-DatabaseObjectDependency -MainWindow $MainWindow -ScriptDirectory $ScriptDir`
- Both files re-signed with certificate `CN=PowerShell Code Signing - Advanced SQL Server Toolkit` (thumbprint `98E50BCC472EA19F2E935023EF73CA8DFACF8D66`) using `Sign-PowerShellScripts.ps1`
- Signing result: 3 scripts signed successfully (includes `Verify-Signatures.ps1`), 0 failures

---

## Skipped Fix

**Issue 8 (from report): QSAU `Main.ps1` missing STA re-launch block**
**Status: SKIPPED — report finding was incorrect**

Investigation confirmed QSAU `Main.ps1` already has a proper STA re-launch block at lines 66–80. The block uses `Write-Log` (defined at lines 18–56) rather than bare `Write-Host`, which is why it was initially overlooked. No change needed.

---

## Verification Summary

| File | Check | Result |
|---|---|---|
| QSAU `06_lookup_query_by_id.py` | `py_compile` | PASS |
| DODU `config_loader.py` | `py_compile` | PASS |
| DNAU `00_populate_columns_from_database.py` | `py_compile` | PASS |
| DNAU `01_populate_keys_from_database.py` | `py_compile` | PASS |
| DNAU `02_analyze_functional_dependencies.py` | `py_compile` | PASS |
| DNAU `03_classify_dependency_relevance.py` | `py_compile` | PASS |
| DNAU `04_generate_excel_report.py` | `py_compile` | PASS |
| DDLG `config_loader.py` | `py_compile` | PASS |
| QSAU `config_loader.py` | `py_compile` | PASS |
| DODU `DatabaseObjectDependencyFunctions.ps1` | Re-signed | SUCCESS |
| DODU `Main.ps1` | Re-signed | SUCCESS |

---

## Files Modified

| File | Change |
|---|---|
| `Query_Store_Analysis_Utility\Core\Python\06_lookup_query_by_id.py` | P1: Added `connection_timeout` param, fixed out-of-scope reference |
| `Database_Object_Dependency_Utility\Core\Python\config_loader.py` | P1: Fixed SyntaxError at lines 268 and 293 |
| `Database_Normalization_Analysis_Utility\Core\Python\00_populate_columns_from_database.py` | P2: Renamed `config_loader` → `config`, dict → `db_config` |
| `Database_Normalization_Analysis_Utility\Core\Python\01_populate_keys_from_database.py` | P2: Renamed `config_loader` → `config`, dict → `db_config` |
| `Database_Normalization_Analysis_Utility\Core\Python\02_analyze_functional_dependencies.py` | P2: Renamed `config_loader` → `config`, dict → `db_config` |
| `Database_Normalization_Analysis_Utility\Core\Python\03_classify_dependency_relevance.py` | P2: Renamed `config_loader` → `config` |
| `Database_Normalization_Analysis_Utility\Core\Python\04_generate_excel_report.py` | P2: Renamed `config_loader` → `config` |
| `DDL_Generator_Utility\Core\Python\config_loader.py` | P2+P3: `get_odbc_driver()` reads config first; `int()` cast on timeout |
| `Query_Store_Analysis_Utility\Core\Python\config_loader.py` | P3: Replaced deprecated `getLevelName()` with `getattr(logging, ...)` |
| `Database_Object_Dependency_Utility\Config\database-config-demo.json` | P3: Added `database` and `windows_auth` fields |
| `Database_Normalization_Analysis_Utility\Config\database-config-demo.json` | P3: Added `windows_auth` field |
| `Database_Object_Dependency_Utility\Core\WPF\Scripts\DatabaseObjectDependencyFunctions.ps1` | P3: Added `$ScriptDirectory` param, replaced `$PSScriptRoot` usage; re-signed |
| `Database_Object_Dependency_Utility\Core\WPF\Scripts\Main.ps1` | P3: Passed `-ScriptDirectory $ScriptDir` to init call; re-signed |
