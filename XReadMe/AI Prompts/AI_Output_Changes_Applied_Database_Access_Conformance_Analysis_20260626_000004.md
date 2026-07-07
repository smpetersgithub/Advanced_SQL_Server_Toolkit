# Changes Applied — Database Access Conformance Analysis
**Date:** 2026-06-26  
**Source analysis:** `AI_Output_Database_Access_Conformance_Analysis_20260626_000000.md`

---

## Change 5 — Add `encoding='utf-8'` to Normalization `_load_json()`

**File modified:**
```
C:\Advanced_SQL_Server_Toolkit\Database_Normalization_Analysis_Utility\Core\Python\config_loader.py
```

**Issue:** The `_load_json()` helper method called `open(file_path, 'r')` without specifying an encoding. On Windows systems where the active code page is not UTF-8 (e.g., CP1252), Python falls back to the system locale encoding, which can silently misread or fail to read JSON config files that contain non-ASCII characters (e.g., server names, passwords, or paths with accented characters). All other utilities in the toolkit (`Database_Object_Dependency_Utility`, `Query_Store_Analysis_Utility`, `DDL_Generator_Utility`) explicitly specify `encoding='utf-8'` in every `open()` call.

**Change:** Added `encoding='utf-8'` to the `open()` call inside `_load_json()`.

**Before:**
```python
with open(file_path, 'r') as f:
    return json.load(f)
```

**After:**
```python
with open(file_path, 'r', encoding='utf-8') as f:
    return json.load(f)
```

Because `_load_json()` is the single shared file-open method called for **all** JSON config files in the Normalization utility (`config.json`, `database-config.json`, `table-config.json`), this single-line change brings all three file reads into alignment with the rest of the toolkit.

---

*No other files were modified.*

