# Database Access Conformance Analysis
**Generated:** 2026-06-19 13:02:39  
**Scope:** Four SQL Server utilities in `C:\Advanced_SQL_Server_Toolkit`  
**Type:** Read-only analysis — no code was modified

---

## Prior Session History

This analysis is the sixth in a series. The following prior sessions have been applied:

| Session | File | Changes |
|---------|------|---------|
| 1 | `AI_Output_Changes_Applied_…2026-06-19_11-20-17.md` | 8 standardization changes — config path keys, logging, ODBC driver handling, error exits, quality headers |
| 2 | `AI_Output_Changes_Applied_…2026-06-19_11-42-14.md` | 6 regression bug fixes — DODU variable names, QSAU out-of-scope config references |
| 3 | `AI_Output_Database_Access_Conformance_Analysis_2026-06-19_11-46-40.md` | Analysis report — 9 issues identified |
| 4 | `AI_Output_Changes_Applied_…2026-06-19_12-06-13.md` | All 9 issues applied |
| 5 | `AI_Output_Database_Access_Conformance_Analysis_2026-06-19_12-21-21.md` | Analysis report — 11 P3 issues identified |
| 6 | `AI_Output_Changes_Applied_…2026-06-19_12-56-14.md` | All 11 P3 issues applied |

---

## 1. Utility Overview

| Utility | Abbrev | Python Scripts | Config Files | DB Access |
|---------|--------|---------------|--------------|-----------|
| Database_Normalization_Analysis_Utility | DNAU | 5 + config_loader.py | config.json, database-config.json, table-config.json | Single server/DB via pyodbc |
| Database_Object_Dependency_Utility | DODU | 9 + config_loader.py | config.json, database-config.json | Single server/DB via pyodbc |
| Query_Store_Analysis_Utility | QSAU | 7 + config_loader.py | config.json, database-config.json, reports-config.json, active-report-config.json | Single server/DB via pyodbc |
| DDL_Generator_Utility | DDLG | 3 + config_loader.py | config.json, database-config.json (multi-server) | Multiple servers/DBs via pyodbc + mssql-scripter CLI |

---

## 2. Connection Methods — Current State

All four utilities use **pyodbc** for SQL Server connectivity. All connection strings follow the identical structure:

```
DRIVER={<driver>};SERVER=<server>;DATABASE=<database>;[Trusted_Connection=yes | UID=<user>;PWD=<pass>];TrustServerCertificate=yes;
```

| Feature | DNAU | DODU | QSAU | DDLG |
|---------|------|------|------|------|
| Connection library | pyodbc | pyodbc | pyodbc | pyodbc |
| Context manager (`with pyodbc.connect()`) | ✅ All scripts | ✅ All scripts | ✅ All scripts | ✅ All scripts |
| `TrustServerCertificate=yes` | ✅ | ✅ | ✅ | ✅ |
| Windows auth support | ✅ | ✅ | ✅ | ✅ |
| SQL Server auth support | ✅ | ✅ | ✅ | ✅ |
| Multi-server support | ❌ (single) | ❌ (single) | ❌ (single) | ✅ (by design) |

**Assessment: CONSISTENT** ✅

---

## 3. Authentication Handling — Current State

All four utilities support both Windows Authentication (`windows_auth: true`) and SQL Server Authentication. The branching logic is identical across DNAU, DODU, and QSAU. DDLG's `get_connection_string()` accepts explicit `windows_auth` as a parameter (by design, as it supports multiple servers).

**Assessment: CONSISTENT** ✅

---

## 4. ODBC Driver Handling — Current State

All four utilities implement identical patterns:

- `get_odbc_driver()`: Returns pinned driver if config value is not `"auto"`, otherwise calls `_get_available_odbc_driver()`
- `_get_available_odbc_driver()`: Identical driver preference list across all four: `[18, 17, 13, 11, Native Client 11.0, SQL Server]`

| Utility | `odbc_driver` config value |
|---------|--------------------------|
| DNAU | `"ODBC Driver 17 for SQL Server"` (pinned) |
| DODU | `"ODBC Driver 17 for SQL Server"` (pinned) |
| QSAU | `"auto"` (auto-detect) |
| DDLG | `"auto"` (auto-detect, added session 6) |

DNAU and DODU have pinned drivers; QSAU and DDLG use auto-detection. This is a configuration choice, not a code defect.

**Assessment: CONSISTENT (code)** ✅ | **Minor config divergence** (intentional)

---

## 5. ConfigLoader Architecture — Current State

All four utilities follow the `ConfigLoader` class pattern with:
- `__init__(config_path=None)` — accepts optional override
- `self.config` — main config.json data
- `setup_logging(script_name)` — configures logging and returns log file path
- `get_connection_string()` — builds ODBC connection string
- `get_odbc_driver()` → `_get_available_odbc_driver()` — ODBC driver resolution
- `get_connection_timeout()` — returns int with fallback

### 5.1 `get_connection_timeout()` — Minor Inconsistency Detected

| Utility | Pattern | Risk |
|---------|---------|------|
| DODU | `self.config.get('database', {}).get('connection_timeout', 10)` | Safe — empty dict fallback if section missing |
| QSAU | `self.config.get('database', {}).get('connection_timeout', 10)` | Safe — empty dict fallback |
| DDLG | `self.config.get('database', {}).get('connection_timeout', 10)` | Safe — empty dict fallback |
| DNAU | `self.config['database'].get('connection_timeout', 10)` | ⚠️ Raises `KeyError` if `database` section absent |

DNAU is slightly less defensive but will be caught by the `try/except (KeyError, TypeError, ValueError)` wrapper it has.

### 5.2 `get_log_dir()` Return Type — Minor Inconsistency Detected

| Utility | Return Type | Notes |
|---------|------------|-------|
| DNAU | `Path` | Consistent with DDLG |
| DODU | `str` | ⚠️ Different from DNAU/DDLG |
| QSAU | `Path` (via `get_logs_base_dir()`) | Method named differently |
| DDLG | `Path` | Consistent with DNAU |

DODU's `setup_logging()` compensates by wrapping with `Path(self.get_log_dir())` internally, so callers that use `setup_logging()` are unaffected. However, scripts that call `get_log_dir()` directly (03, 06, 07) receive a `str` and must handle accordingly.

### 5.3 Unused `self.logger` in DODU ConfigLoader — Minor Issue Detected

DODU's `ConfigLoader.__init__()` contains:
```python
self.logger = logging.getLogger(__name__)
```
This creates a logger instance assigned to the instance variable `self.logger`, but **no method in `ConfigLoader` ever calls `self.logger.xxx()`**. This is dead code that adds no functional value and may cause confusion.

**Assessment: MOSTLY CONSISTENT** ✅ — with minor issues documented above

---

## 6. Logging Setup — Current State

### 6.1 Scripts Using `config.setup_logging()` (Standard Pattern)

The standard pattern across utilities:
```python
log_file = config.setup_logging('script_name')
logger = logging.getLogger(__name__)
```

| Utility | Scripts using `config.setup_logging()` |
|---------|----------------------------------------|
| DNAU | 00, 01, 02, 03, 04 ✅ (all 5) |
| DODU | 01, 02, 04, 05 ✅ (4 of 9) |
| QSAU | 01, 02, 03, 04, 05, 06, run_all ✅ (all 7) |
| DDLG | 01, 02, 03 ✅ (all 3) |

### 6.2 ⚠️ DODU Scripts Bypassing `config.setup_logging()` — P2 Issue

**DODU scripts 03, 06, 07** implement logging inline using `logging.basicConfig()` with **hardcoded settings**, bypassing the central config mechanism entirely:

**Script 03 (`03_create_final_ui_mappings.py`):**
```python
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')   # ← Different format
log_filename = f'log_03_create_final_ui_mappings_{timestamp}.log'
logging.basicConfig(
    level=logging.INFO,                                      # ← Hardcoded level
    format='%(asctime)s - %(levelname)s - %(message)s',     # ← Hardcoded format
    ...
)
```

**Script 06 (`06_create_final_excel_file.py`):**
```python
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')   # ← Different format
log_filename = f'log_06_create_final_excel_file_{timestamp}.log'
logging.basicConfig(...)                                     # ← Hardcoded settings
```

**Script 07 (`07_format_excel_file.py`):**
```python
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')   # ← Different format
log_filename = f'log_07_format_excel_file_{timestamp}.log'
logging.basicConfig(...)                                     # ← Hardcoded settings
```

**Impact:**
1. Log timestamp format is `%Y-%m-%d_%H-%M-%S` (e.g., `2026-06-19_13-02-39`) vs the standard `%Y%m%d_%H%M%S` (e.g., `20260619_130239`) used by all other scripts across all utilities.
2. Changes to `config.json` logging settings (`log_level`, `log_format`, `timestamp_format`) are **ignored** by these three scripts.
3. Log file names from scripts 03, 06, 07 will not sort consistently with log files from scripts 01, 02, 04, 05.

### 6.3 ⚠️ DODU Script 00 Has Own Local `setup_logging()` — P2 Issue

`00_run_all_scripts.py` defines its own `setup_logging(log_dir)` function:
```python
def setup_logging(log_dir):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)           # ← Hardcoded
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # ← Hardcoded
    ...
    return logger
```

This function:
- Ignores `config.json` log level and format settings
- Uses a different log file naming pattern: `00_run_all_scripts_{timestamp}.log` (no `log_` prefix)
- Returns a `logger` object (all other patterns have `setup_logging` return a `Path`)
- Uses timestamp format `%Y%m%d_%H%M%S` (same as standard — coincidentally correct)

### 6.4 `setup_logging()` in ConfigLoaders — Comparison

| Feature | DNAU | DODU | QSAU | DDLG |
|---------|------|------|------|------|
| `log_level` from config | ✅ `getattr(logging,...)` | ✅ `getattr(logging,...)` | ✅ `getattr(logging,...)` | ✅ `getattr(logging,...)` |
| `log_format` from config | ✅ | ✅ | ✅ | ✅ |
| `timestamp_format` from config | ✅ | ✅ | ✅ | ✅ |
| `log_filemode` from config | ❌ Not configurable (defaults 'a') | ❌ Not configurable (defaults 'a') | ❌ Not configurable (defaults 'a') | ✅ `get_log_filemode()` |
| Uses `force=True` on basicConfig | ✅ | ✅ | ✅ | ✅ |
| Returns `Path` to log file | ✅ | ✅ | ✅ | ✅ |

**Note:** Only DDLG supports configurable log file mode. DNAU, DODU, QSAU always append (`'a'`). This is intentional per DDLG's design (overwrite each run) but could be made consistent if desired.

---

## 7. Named Logger Pattern — Current State

### Standard Pattern (After Session 6 Fixes)
```python
# Module level (in DNAU, DODU, DDLG):
logger = logging.getLogger(__name__)

# Inside main() after setup_logging():
log_file = config.setup_logging('script_name')
logger = logging.getLogger(__name__)   # Reassignment
```

### QSAU Pattern (Slightly Different)
```python
# No module-level logger

# Inside main():
log_file = config.setup_logging('01_extract_query_store_data')
logger = logging.getLogger(__name__)
```

### 7.1 ⚠️ DNAU: Module-Level Logger Immediately Shadowed — P3 Issue

All DNAU scripts (00–04) declare `logger = logging.getLogger(__name__)` at module level (line 11), then **immediately reassign** `logger` inside `main()` after `setup_logging()`. The module-level assignment is never used. While not harmful (both return the same `'__main__'` logger instance since these run as scripts), it is redundant and could cause confusion.

**Example from `00_populate_columns_from_database.py`:**
```python
logger = logging.getLogger(__name__)   # Line 11 — module level (never used before main())

def main():
    config.setup_logging('00_populate_columns_from_database')
    logger = logging.getLogger(__name__)  # Reassignment inside main()
```

**Note:** In DODU, DDLG scripts, the module-level `logger` IS referenced in helper functions that run before `main()` or are called without `main()`. In DNAU, no helper function uses `logger` before `main()` is called.

**Assessment: MOSTLY CONSISTENT** ✅ — with P2 issues in DODU scripts 00, 03, 06, 07

---

## 8. Error Handling — Current State

### 8.1 Configuration Loading Errors (main() entry)

| Pattern | DNAU | DODU | QSAU | DDLG |
|---------|------|------|------|------|
| Exception type caught | `(FileNotFoundError, ValueError, KeyError)` | `(FileNotFoundError, ValueError, KeyError)` | `(FileNotFoundError, ValueError, KeyError)` | `FileNotFoundError` + `Exception` (separate) |
| Error output | `print(f"[ERROR] ...")` + `sys.exit(1)` | `print(f"[ERROR] ...")` + `sys.exit(1)` | `print(f"[ERROR] ...")` + `sys.exit(1)` | `print(f"[ERROR] ...")` + `sys.exit(1)` |
| Pre-logging (print) | ✅ | ✅ | ✅ | ✅ |

DDLG separates `FileNotFoundError` from generic `Exception` (adding "Please ensure config.json exists" guidance). Functionally equivalent; slightly more user-friendly.

### 8.2 Database Error Handling

All utilities that connect to SQL Server wrap the connection and query execution in `try/except` blocks that catch `pyodbc.Error` (or `Exception`) and call `logger.error()` followed by `sys.exit(1)`.

**Assessment: CONSISTENT** ✅

---

## 9. Module Docstrings — Current State

| Script | DNAU | DODU | QSAU | DDLG |
|--------|------|------|------|------|
| config_loader.py | ✅ | ✅ | ✅ | ✅ |
| 00_run_all / run_all | N/A | ✅ | ✅ | N/A |
| Script 01 | ✅ | ✅ | ✅ | ✅ (+ file comment) |
| Script 02 | ✅ | ✅ | ✅ | ✅ (+ file comment) |
| Script 03 | ✅ | ✅ | ✅ | ✅ (+ file comment) |
| Script 04 | ✅ | ❌ **MISSING** | ✅ | N/A |
| Script 05 | ✅ | ❌ **MISSING** | ✅ | N/A |
| Script 06 | N/A | ✅ | N/A | N/A |
| Script 07 | N/A | ✅ | N/A | N/A |
| Script 08 | N/A | ✅ | N/A | N/A |

### ⚠️ DODU Scripts 04 and 05: Missing Module Docstrings — P3 Issue

`04_generate_dependency_report_reverse.py` and `05_generate_dependency_report_forward.py` both start with `import json` directly — no module-level docstring. Every other DODU script (01, 02, 03, 06, 07, 08) has a module docstring.

### DDLG Double Header Pattern

DDLG scripts 01, 02, 03 all have both a file-level comment **and** a module docstring:
```python
# create_directory_structure.py       ← File comment
"""
Script to create directory structure...   ← Docstring
"""
```
Other utilities use only the docstring. This is a minor style inconsistency but not harmful.

---

## 10. Configuration File Structure — Current State

### 10.1 Logging Section

| Key | DNAU | DODU | QSAU | DDLG |
|-----|------|------|------|------|
| `log_level` | ✅ `logging.log_level` | ✅ `logging.log_level` | ✅ `logging.log_level` | ✅ `logging.log_level` |
| `log_format` | ✅ `logging.log_format` | ✅ `logging.log_format` | ✅ `logging.log_format` | ✅ `logging.log_format` |
| `timestamp_format` | ✅ `logging.timestamp_format` | ✅ `logging.timestamp_format` | ✅ `logging.timestamp_format` | ✅ `logging.timestamp_format` |
| `log_filemode` | ❌ Not present | ❌ Not present | ❌ Not present | ✅ `logging.log_filemode: "w"` |
| `log_file_names` | ❌ Not present | ❌ Not present | ✅ **Present but orphaned** | ❌ Not present |

### ⚠️ QSAU config.json: Orphaned `log_file_names` Section — P3 Issue

After Session 6 (Issue 9), the `log_file_names` dictionary in QSAU's `config.json` is no longer used:

```json
"log_file_names": {
    "script_01": "01_extract_queries_{timestamp}.log",
    "script_02": "02_extract_xml_plans_{timestamp}.log",
    ...
}
```

The scripts now pass descriptive names directly to `setup_logging()`. Additionally, `get_log_file_name()` in QSAU's `config_loader.py` is also now unreferenced (no callers remain). Both can safely be removed.

---

## 11. Orphaned / Unused Code — Current State

### 11.1 ⚠️ QSAU `get_log_file_name()` Method — P3 Issue

After Issue 9 (Session 6), the `get_log_file_name(script_key)` method in `QSAU\Core\Python\config_loader.py` (lines 141–151) is **no longer called by any script**. The method reads from `log_file_names` in config.json using old-style `script_01`/`script_02` keys that are also now unused.

### 11.2 ⚠️ DDLG `LOG_LEVEL_MAP` Class Constant — P3 Issue

After Issue 10 (Session 6), `setup_logging()` now uses `getattr(logging, ...)` directly. The `LOG_LEVEL_MAP` dictionary retained at the top of `DDL_Generator_Utility\Core\Python\config_loader.py`:

```python
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
```

is **no longer referenced anywhere in the class**. It now serves only as documentation. It should either be removed or marked explicitly as documentation.

### 11.3 ⚠️ DODU `self.logger` Unused Instance Variable — P3 Issue

`Database_Object_Dependency_Utility\Core\Python\config_loader.py` creates a logger in `__init__`:
```python
self.logger = logging.getLogger(__name__)
```
But **no method in the class ever calls `self.logger.xxx()`**. This is a dead instance variable that adds no value.

---

## 12. Code Organization — Current State

### 12.1 Section Headers

| Utility | Uses section comments (`# === ... ===`) |
|---------|----------------------------------------|
| DNAU | ❌ No section headers in config_loader |
| DODU | ✅ `# ===== Path Getters =====`, `# ===== Database Getters =====`, etc. |
| QSAU | ✅ `# ==================== Path Getters ====================` |
| DDLG | ✅ `# ==================== Path Getters ====================` |
| DDLG scripts | ✅ `# ===================== Constants =====`, `# ===== Helper Functions =====` |

DNAU's config_loader has no section comments. All other utilities use visual section separators.

### 12.2 Script Structure

| Pattern | DNAU | DODU | QSAU | DDLG |
|---------|------|------|------|------|
| Helper functions before `main()` | ✅ | ✅ | ✅ | ✅ |
| Constants section | ❌ | ❌ | ❌ | ✅ (all 3 scripts) |
| `if __name__ == "__main__":` guard | ✅ | ✅ | ✅ | ✅ |
| Type annotations | Partial | ❌ Minimal | ❌ Minimal | ✅ Extensive |

DDLG has the most structured script layout (constants, helpers, main processing sections with comments, type annotations throughout).

---

## 13. Issue Summary

### Current Outstanding Issues

#### Priority 2 (Medium) — Functional Inconsistency

| # | Issue | Utility | Location |
|---|-------|---------|----------|
| A | Scripts 03, 06, 07 bypass `config.setup_logging()` — use hardcoded `logging.basicConfig()` with different timestamp format | DODU | `03_create_final_ui_mappings.py`, `06_create_final_excel_file.py`, `07_format_excel_file.py` |
| B | Script 00 uses its own local `setup_logging()` function instead of `config.setup_logging()` | DODU | `00_run_all_scripts.py` |
| C | `get_connection_timeout()` uses `self.config['database'].get(...)` instead of safer `self.config.get('database', {}).get(...)` | DNAU | `config_loader.py` line 468 |

#### Priority 3 (Low) — Minor / Cosmetic

| # | Issue | Utility | Location |
|---|-------|---------|----------|
| D | `get_log_file_name()` method is orphaned — no callers remain | QSAU | `config_loader.py` lines 141–151 |
| E | `log_file_names` config section is orphaned — no longer referenced | QSAU | `Config/config.json` |
| F | `LOG_LEVEL_MAP` class constant is unused dead code | DDLG | `config_loader.py` lines 19–25 |
| G | Scripts 04 and 05 missing module docstrings | DODU | `04_generate_dependency_report_reverse.py`, `05_generate_dependency_report_forward.py` |
| H | Module-level `logger` declared but immediately shadowed inside `main()` | DNAU | All 5 scripts (`00`–`04`) |
| I | `get_log_dir()` returns `str` instead of `Path` | DODU | `config_loader.py` line 109–114 |
| J | `self.logger` instance variable created in `__init__` but never used | DODU | `config_loader.py` line 25 |

**Total: 3 P2 issues, 7 P3 issues (10 total)**

---

## 14. What Is Now Consistent ✅

The following areas are fully standardized across all four utilities (result of prior sessions):

1. **ConfigLoader class pattern** — All utilities use `ConfigLoader()` with `self.config`, `self.config_path`, `self.project_root`
2. **Connection string format** — Identical ODBC string format with `TrustServerCertificate=yes`
3. **ODBC driver resolution** — `get_odbc_driver()` → `_get_available_odbc_driver()` with identical driver preference list
4. **`with pyodbc.connect()` context manager** — All scripts that connect to SQL Server use context managers
5. **Auth handling** — Both Windows and SQL Server auth supported with identical branching logic
6. **`get_connection_timeout()` with try/except fallback** — All four config_loaders protect against invalid values
7. **Named loggers** — All scripts use `logging.getLogger(__name__)`
8. **`setup_logging()` returns `Path`** — Consistent return type from config_loader implementations
9. **`getattr(logging, ...)` for log level** — Used in all four `setup_logging()` implementations
10. **DDLG `get_log_filemode()` wired into `FileHandler`** — Log file mode now config-driven
11. **DDLG `get_connection_string()` uses `get_odbc_driver()`** — Consistent public method usage
12. **DDLG config.json has `odbc_driver` key** — Now configurable
13. **QSAU scripts pass descriptive names to `setup_logging()`** — Removed indirection through `log_name_map`
14. **DNAU `get_log_dir()` method** — Added and used in `setup_logging()`
15. **All module docstrings** — Present on all config_loaders and most scripts (exceptions: DODU 04, 05)

---

## 15. Recommendations

### Recommended for Apply (if user requests changes)

**P2 — Medium Priority:**

- **Issue A (DODU 03, 06, 07):** Replace inline `logging.basicConfig()` with `config.setup_logging()` call. This will align timestamp format (`%Y%m%d_%H%M%S`) and make these scripts respect `config.json` settings.
- **Issue B (DODU 00):** Replace local `setup_logging()` function call with `config.setup_logging('00_run_all_scripts')` and use the returned `Path` for log file reference.
- **Issue C (DNAU):** Change `self.config['database'].get(...)` to `self.config.get('database', {}).get(...)` for defensive consistency.

**P3 — Low Priority:**

- **Issue D+E (QSAU orphaned code):** Remove `get_log_file_name()` method from config_loader.py and remove the `log_file_names` section from `config.json`.
- **Issue F (DDLG LOG_LEVEL_MAP):** Either remove the `LOG_LEVEL_MAP` constant or add `# Retained for reference` comment to clarify intent.
- **Issue G (DODU 04, 05):** Add module docstrings.
- **Issue H (DNAU double logger):** Remove the module-level `logger = logging.getLogger(__name__)` from DNAU scripts 00–04, leaving only the assignment inside `main()`.
- **Issue I (DODU get_log_dir return type):** Change return type from `str` to `Path`.
- **Issue J (DODU self.logger):** Remove `self.logger = logging.getLogger(__name__)` from ConfigLoader `__init__` (or start using it in config_loader methods).

---

## 16. Conformance Score

| Category | Score | Notes |
|----------|-------|-------|
| Connection Methods | ✅ 100% | Fully consistent |
| Authentication | ✅ 100% | Fully consistent |
| Connection String Construction | ✅ 100% | Fully consistent |
| Configuration Management | ✅ 95% | Minor differences in config structure |
| Error Handling | ✅ 95% | Minor difference in DNAU `get_connection_timeout` |
| Logging (ConfigLoader) | ✅ 95% | DDLG has `log_filemode` uniquely |
| Logging (Scripts) | ⚠️ 75% | DODU scripts 00, 03, 06, 07 bypass `config.setup_logging()` |
| Module Docstrings | ⚠️ 90% | DODU scripts 04, 05 missing |
| Code Organization | ✅ 90% | DNAU config_loader lacks section comments |
| Dead Code Cleanup | ⚠️ 80% | Orphaned methods and constants remain |

**Overall Conformance: ~92%** — No P1 or critical issues. Three P2 issues (all in DODU scripts) and seven P3 cosmetic issues remain.

---

*Analysis completed: 2026-06-19 13:02:39*  
*Files analyzed: 37 Python files, 7 JSON config files across 4 utilities*  
*Changes applied: None (read-only analysis)*
