# Changes Applied Log — EPAU Button Fix (Round 2)
**Date:** 2026-06-19 15:30:00  
**Session:** WPF/PowerShell Conformance Standardization — Root Cause Fix

---

## Problem Statement

EPAU toolbar buttons open the UI but clicking them does nothing. Event handlers are not executing.

---

## Root Cause (Revised)

The prior round fixed null-guard syntax but missed the deeper scope issue:

**DNAU and DODU** store button variables in `$script:` scope and call named functions from handlers:
```powershell
$script:btnRunAnalysis = $MainWindow.FindName('btnRunAnalysis')
$script:btnRunAnalysis.Add_Click({ Run-Analysis })
```

**EPAU (original)** stored button variables as LOCAL variables inside `Initialize-ExecutionPlanAnalysis` and used large inline closures:
```powershell
$btnLoadSourceTarget = $MainWindow.FindName('btnLoadSourceTarget')  # LOCAL variable
$btnLoadSourceTarget.Add_Click({
    # ... 50-line closure capturing $btnLoadSourceTarget and $MainWindow from LOCAL scope
})
```

When `Initialize-ExecutionPlanAnalysis` returns, the LOCAL scope frame is no longer active. PowerShell closures in WPF event handlers that capture **local function variables** can lose access to those variables after the defining function returns. `$MainWindow` (a function parameter) and all 10 button variables were captured this way, causing handler bodies to fail silently when invoked after the function returned.

---

## Changes Applied

**File:** `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`

### Change 1: Store `$MainWindow` in `$script:` scope

Added at the top of `Initialize-ExecutionPlanAnalysis` (line 171):
```powershell
$script:MainWindow = $MainWindow
```

All `$MainWindow.` references inside handlers replaced with `$script:MainWindow.`

### Change 2: Promote all 10 local button variables to `$script:` scope

**Before:**
```powershell
$btnLoadSourceTarget = $MainWindow.FindName('btnLoadSourceTarget')
$btnCheckForNewPlans = $MainWindow.FindName('btnCheckForNewPlans')
# ... etc.
```

**After:**
```powershell
$script:btnLoadSourceTarget = $script:MainWindow.FindName('btnLoadSourceTarget')
$script:btnCheckForNewPlans = $script:MainWindow.FindName('btnCheckForNewPlans')
# ... etc.
```

Buttons affected (all 10 toolbar buttons):

| Variable | Handler |
|---|---|
| `$script:btnLoadSourceTarget` | Load Execution Plans |
| `$script:btnCheckForNewPlans` | Check for New Plans / Reload Directory |
| `$script:btnLoadConfiguration` | Load Configuration |
| `$script:btnSaveExecutionPlanConfiguration` | Save Configuration |
| `$script:btnCompareExecutionPlans` | Compare Execution Plans |
| `$script:btnAnalyzeIndividualPlans` | Analyze Individual Plans |
| `$script:btnOpenOutputFolder` | Open Output Folder |
| `$script:btnCleanup` | Cleanup |
| `$script:btnBackupConfigurations` | Backup Configurations |
| `$script:btnGitHub` | GitHub |

All null-guard conditions and fallback FindName assignments also updated to use `$script:` prefix.

---

## Why This Fixes It

PowerShell WPF event handler script blocks that capture **local function variables** lose access to those variables after the defining function returns. By promoting variables to `$script:` scope:
- The script scope persists for the lifetime of the module/dot-sourced file
- Event handlers reliably access `$script:MainWindow` and `$script:btnXxx` at any point after initialization
- This matches the proven pattern used in DNAU and DODU

---

## Validation

| File | Syntax Check |
|---|---|
| `ExecutionPlanAnalysisFunctions.ps1` | ✅ PASS — 0 errors |
| Bare `$MainWindow` references remaining | ✅ 2 (param declaration + assignment only) |
| Bare `$btnXxx` references remaining | ✅ 0 |
