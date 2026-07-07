# Changes Applied — Database Access Conformance Analysis
**Date:** 2026-06-26  
**Source analysis:** `AI_Output_Database_Access_Conformance_Analysis_20260626_000000.md`

---

## Change 1 — Fix missing `json.JSONDecodeError` handling in Query Store ConfigLoader

**File modified:**
```
C:\Advanced_SQL_Server_Toolkit\Query_Store_Analysis_Utility\Core\Python\config_loader.py
```

**Issue:** The `_load_reports_config()` and `_load_active_report_config()` methods called `json.load()` without a try/except block. If either `reports-config.json` or `active-report-config.json` contained malformed JSON, an unhandled `json.JSONDecodeError` would propagate past the `main()` guard in consumer scripts, bypassing the standard error-handling pattern used by every other config loader in the toolkit.

**Methods changed:** `_load_reports_config()`, `_load_active_report_config()`

**Before:**
```python
def _load_reports_config(self):
    """Load reports configuration."""
    reports_config_path = self.project_root / self.config['paths']['config']['reports_config']
    if not reports_config_path.exists():
        raise FileNotFoundError(f"Reports config not found: {reports_config_path}")

    with open(reports_config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _load_active_report_config(self):
    """Load active report configuration."""
    active_report_path = self.project_root / self.config['paths']['config']['active_report_config']
    if not active_report_path.exists():
        raise FileNotFoundError(f"Active report config not found: {active_report_path}")

    with open(active_report_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

**After:**
```python
def _load_reports_config(self):
    """Load reports configuration."""
    reports_config_path = self.project_root / self.config['paths']['config']['reports_config']
    if not reports_config_path.exists():
        raise FileNotFoundError(f"Reports config not found: {reports_config_path}")

    try:
        with open(reports_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in reports config file: {e.msg}", e.doc, e.pos
        )

def _load_active_report_config(self):
    """Load active report configuration."""
    active_report_path = self.project_root / self.config['paths']['config']['active_report_config']
    if not active_report_path.exists():
        raise FileNotFoundError(f"Active report config not found: {active_report_path}")

    try:
        with open(active_report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in active report config file: {e.msg}", e.doc, e.pos
        )
```

**Behaviour after fix:** A malformed JSON file now raises a `json.JSONDecodeError` with a clear contextual message (e.g., `"Invalid JSON in reports config file: ..."`). This exception is caught by the `except (FileNotFoundError, ValueError, KeyError) as e` guard in each script's `main()` function — consistent with how all other config loaders in the toolkit handle JSON parse errors.

---

*No other files were modified.*

