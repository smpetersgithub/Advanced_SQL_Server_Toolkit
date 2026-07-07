# Changes Applied — Database Access Conformance Analysis
**Date:** 2026-06-19 11:42:14  
**Session:** Bug Fix — Regression Bugs C1 and C2 (introduced by prior session 2026-06-19 11:20:17)  
**Type:** Bug fixes only (read-only analysis — no refactoring)  
**Signing required:** No (Python files only — no `.ps1` files modified)

---

## Summary

Two categories of regression bugs were introduced by the prior session's standardization changes. Both categories caused `NameError` at runtime due to incorrect variable names or out-of-scope references. This session applied the remaining fixes to complete the remediation.

---

## Bug Categories

### C1 — Wrong Variable Name (DODU)

**Root Cause:** The prior session applied `config_loader.get_connection_timeout()` in DODU scripts, but the ConfigLoader instance in those scripts is named `config` (not `config_loader`). DNAU is the only utility that names its instance `config_loader`.

**Fix Pattern:** `config_loader.get_connection_timeout()` → `config.get_connection_timeout()` at the `pyodbc.connect()` call site.

**Status after this session:** ✅ All 3 DODU scripts fixed.

---

### C2 — Out-of-Scope Config Reference (QSAU)

**Root Cause:** The prior session placed `config.get_connection_timeout()` inside QSAU helper functions (`execute_sql_query`, `download_execution_plans_batch`, `execute_sql_query_with_filter`). In these scripts, `config` is a local variable in `main()` and is not accessible inside those helper functions.

**Fix Pattern:** Add `connection_timeout=10` as a parameter to each helper function, use `connection_timeout` inside the function at `pyodbc.connect()`, and pass `config.get_connection_timeout()` from `main()` at each call site.

**Status after this session:** ✅ All 3 QSAU scripts fixed.

---

## Files Modified

### DODU — C1 Fixes (applied in prior session, documented here for completeness)

| # | File | Change | Line |
|---|------|---------|------|
| 1 | `Database_Object_Dependency_Utility\Core\Python\02_generate_dependency_report_reverse_ui_lookup.py` | `config_loader.get_connection_timeout()` → `config.get_connection_timeout()` | ~129 |
| 2 | `Database_Object_Dependency_Utility\Core\Python\04_generate_dependency_report_reverse.py` | `config_loader.get_connection_timeout()` → `config.get_connection_timeout()` | ~129 |
| 3 | `Database_Object_Dependency_Utility\Core\Python\05_generate_dependency_report_forward.py` | `config_loader.get_connection_timeout()` → `config.get_connection_timeout()` | ~129 |

### QSAU — C2 Fix for Script 01 (applied in prior session, documented here for completeness)

| # | File | Change | Location |
|---|------|---------|----------|
| 4 | `Query_Store_Analysis_Utility\Core\Python\01_extract_query_store_data.py` | Added `connection_timeout=10` param to `execute_sql_query()` | Function signature |
| 4 | `Query_Store_Analysis_Utility\Core\Python\01_extract_query_store_data.py` | Updated docstring Args to include `connection_timeout` | Docstring |
| 4 | `Query_Store_Analysis_Utility\Core\Python\01_extract_query_store_data.py` | `timeout=config.get_connection_timeout()` → `timeout=connection_timeout` in `pyodbc.connect()` | Inside helper function |
| 4 | `Query_Store_Analysis_Utility\Core\Python\01_extract_query_store_data.py` | Added `config.get_connection_timeout()` as 5th arg at call site in `main()` | `main()` call site |

### QSAU — C2 Fix for Script 02 (applied this session)

| # | File | Change | Location |
|---|------|---------|----------|
| 5 | `Query_Store_Analysis_Utility\Core\Python\02_extract_xml_execution_plans.py` | Added `connection_timeout=10` param to `download_execution_plans_batch()` | Function signature (~line 79) |
| 5 | `Query_Store_Analysis_Utility\Core\Python\02_extract_xml_execution_plans.py` | Updated docstring Args to include `connection_timeout` | Docstring |
| 5 | `Query_Store_Analysis_Utility\Core\Python\02_extract_xml_execution_plans.py` | `timeout=config.get_connection_timeout()` → `timeout=connection_timeout` in `pyodbc.connect()` | Inside helper function (~line 131) |
| 5 | `Query_Store_Analysis_Utility\Core\Python\02_extract_xml_execution_plans.py` | Added `connection_timeout=config.get_connection_timeout()` as keyword arg at call site in `main()` | `main()` call site (~line 256) |

### QSAU — C2 Fix for Script 04 (applied this session)

| # | File | Change | Location |
|---|------|---------|----------|
| 6 | `Query_Store_Analysis_Utility\Core\Python\04_extract_index_and_statistics_for_tables.py` | Added `connection_timeout=10` param to `execute_sql_query_with_filter()` | Function signature (~line 104) |
| 6 | `Query_Store_Analysis_Utility\Core\Python\04_extract_index_and_statistics_for_tables.py` | Updated docstring Args to include `connection_timeout` | Docstring |
| 6 | `Query_Store_Analysis_Utility\Core\Python\04_extract_index_and_statistics_for_tables.py` | `timeout=config.get_connection_timeout()` → `timeout=connection_timeout` in `pyodbc.connect()` | Inside helper function (~line 174) |
| 6 | `Query_Store_Analysis_Utility\Core\Python\04_extract_index_and_statistics_for_tables.py` | Added `config.get_connection_timeout()` as 6th positional arg at call site in `main()` for-loop | `main()` call site (~lines 312–318) |

---

## Verification

All 6 modified files passed `python -m py_compile` syntax validation:

```
PASS: 02_generate_dependency_report_reverse_ui_lookup.py
PASS: 04_generate_dependency_report_reverse.py
PASS: 05_generate_dependency_report_forward.py
PASS: 01_extract_query_store_data.py
PASS: 02_extract_xml_execution_plans.py
PASS: 04_extract_index_and_statistics_for_tables.py
```

---

## Utilities Not Modified

- `Database_Normalization_Analysis_Utility` — No bugs introduced; already uses `config_loader` consistently
- `DDL_Generator_Utility` — Excluded from standardization by design (different architecture)

---

## Related Files

| File | Purpose |
|------|---------|
| `AI_Output_Database_Access_Conformance_Analysis.md` | Full conformance analysis report (updated this session to document C1/C2 bugs) |
| `AI_Output_Changes_Applied_Database_Access_Conformance_Analysis_2026-06-19_11-20-17.md` | Prior session's change log (8 standardization changes — origin of the regression bugs) |
