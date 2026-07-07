# Changes Applied Log — EPAU Button Fix
**Date:** 2026-06-19 15:12:26  
**Session:** WPF/PowerShell Conformance Standardization — Bug Fix Round

---

## Context

The Execution Plan Analysis Utility (EPAU) buttons stopped working after the prior session added `Set-StrictMode -Version Latest` to `Main.ps1`. Under strict mode, calling `.Add_Click()` on a `$null` variable is a **terminating exception**. If `FindName()` returns `$null` for any one of the 9 local toolbar button variables, the exception terminates `Initialize-ExecutionPlanAnalysis`, which is caught by Main.ps1's outer `try/catch`, and the window renders without any event handlers registered.

DNAU and DODU work correctly because they already wrapped all `.Add_Click()` calls with `if ($btn) { ... }` null guards. EPAU had no null guards on its local toolbar button variables.

---

## Change Applied

**File:** `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`

**Change:** Added null guard (`if ($btnX) { ... }`) wrappers around all 10 local toolbar button `.Add_Click()` handler blocks, matching the DODU defensive programming pattern.

### Buttons guarded:

| Button Variable | Handler Start Line (approx) | Comment |
|---|---|---|
| `$btnLoadConfiguration` | ~425 | Load Configuration handler |
| `$btnLoadSourceTarget` | ~474 | Load Execution Plans handler |
| `$btnCheckForNewPlans` | ~560 | Check for New Plans handler |
| `$btnSaveExecutionPlanConfiguration` | ~723 | Save Configuration handler |
| `$btnCompareExecutionPlans` | ~775 | Compare Execution Plans handler |
| `$btnAnalyzeIndividualPlans` | ~876 | Analyze Individual Plans handler |
| `$btnOpenOutputFolder` | ~1064 | Open Output Folder handler |
| `$btnCleanup` | ~1094 | Cleanup handler |
| `$btnBackupConfigurations` | ~1226 | Backup Configurations handler |
| `$btnGitHub` | ~1311 | GitHub button handler |

### Pattern applied (before → after):

```powershell
# BEFORE
    $btnLoadConfiguration.Add_Click({
        # ... handler body ...
    })

# AFTER
    if ($btnLoadConfiguration) { $btnLoadConfiguration.Add_Click({
        # ... handler body ...
    })
    }
```

---

## Validation

| File | Syntax Check |
|---|---|
| `ExecutionPlanAnalysisFunctions.ps1` | ✅ PASS — 0 errors |
| `Main.ps1` | ✅ PASS — 0 errors |

---

## Root Cause Summary

- Prior session added `Set-StrictMode -Version Latest` to EPAU `Main.ps1` (conformance change C1)
- Under StrictMode, `$null.Add_Click(...)` throws a **terminating exception** (not suppressible by `$ErrorActionPreference`)
- EPAU had 10 local button variables with no null guards — unlike DNAU/DODU which guard all `.Add_Click()` calls
- If any button is `$null`, the exception propagates out of `Initialize-ExecutionPlanAnalysis`, gets caught by Main.ps1's outer `try/catch`, and the window shows with zero event handlers registered
- Fix: wrap all 10 handlers with `if ($btnX) { ... }` null guards, consistent with DODU's existing pattern
