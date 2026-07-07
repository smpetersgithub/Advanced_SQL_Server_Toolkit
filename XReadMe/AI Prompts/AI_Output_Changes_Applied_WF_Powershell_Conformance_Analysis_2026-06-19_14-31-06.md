# Changes Applied — WPF and PowerShell Conformance
**Date:** 2026-06-19  
**Time:** 14:31:06  
**Based on analysis:** `AI_Output_WPF_Powershell_Conformance_Analysis_2026-06-19_14-25-06.md`

---

## Summary

10 changes applied across 8 files, covering all 4 priority levels.  
All modified PowerShell files pass syntax validation.

---

## Changes Applied

### C1 — EPAU Main.ps1: Replace hardcoded `$ScriptDir` with dynamic path resolution
**File:** `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\Main.ps1`  
**Severity:** Critical  
**Action:** Removed the hardcoded `$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\..."` block and replaced it with the same dynamic resolution pattern used by DNAU and DODU:
- Checks `$PSScriptRoot` first (normal script execution)
- Falls back to `$MyInvocation.MyCommand.Path` (alternative script path)
- Falls back to `[System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName` (compiled EXE)
- Resolves to absolute path via `(Resolve-Path $ScriptDir).Path`

---

### C5 — EPAU Main.ps1: Add missing script pragmas
**File:** `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\Main.ps1`  
**Severity:** High  
**Action:** Added three standard pragmas present in DNAU, DODU, and QSAU:
- `#Requires -Version 5.1` — added at top of file
- `Set-StrictMode -Version Latest` — added after STA check block
- `$ErrorActionPreference = 'Stop'` — added after `Set-StrictMode`

---

### C8 — EPAU: Pass `$ScriptDirectory` to `Initialize-ExecutionPlanAnalysis`
**Files:**
- `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\Main.ps1`
- `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`

**Severity:** Medium  
**Action:**  
- In `Main.ps1`: Changed `Initialize-ExecutionPlanAnalysis -MainWindow $MainWindow` to `Initialize-ExecutionPlanAnalysis -MainWindow $MainWindow -ScriptDirectory $ScriptDir`
- In `ExecutionPlanAnalysisFunctions.ps1`:
  - Added `[Parameter(Mandatory)] [string]$ScriptDirectory` to `Initialize-ExecutionPlanAnalysis` parameters
  - Updated `Initialize-Paths` to accept `[Parameter(Mandatory)] [string]$ScriptDirectory` and compute `$script:ProjectRoot` using `Split-Path -Parent` × 3 from the passed value (matching DNAU/DODU pattern), replacing the `$PSCommandPath` approach

---

### C2 — QSAU MainWindow.xaml: Fix hardcoded absolute window icon path
**File:** `Query_Store_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** Critical  
**Action:** Replaced:
```
Icon="C:/Advanced_SQL_Server_Toolkit/Query_Store_Analysis_Utility/Core/WPF/Assets/icons8-paper-plane-ico.ico"
```
With:
```
Icon="../Assets/icons8-paper-plane-ico.ico"
```

---

### C3 — DNAU MainWindow.xaml: Fix hardcoded absolute toolbar image paths
**File:** `Database_Normalization_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** Critical  
**Action:** Replaced 3 absolute backslash paths with relative `../Assets/` paths:
- `C:\Advanced_SQL_Server_Toolkit\Database_Normalization_Analysis_Utility\Core\WPF\Assets\icons8-play-button-50.png` → `../Assets/icons8-play-button-50.png`
- `C:\Advanced_SQL_Server_Toolkit\Database_Normalization_Analysis_Utility\Core\WPF\Assets\icons8-opened-folder-50.png` → `../Assets/icons8-opened-folder-50.png`
- `C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-delete-50.png` → `../Assets/icons8-delete-50.png`

> Note: The third image source was incorrectly pointing to the EPAU assets directory. It has been corrected to reference DNAU's own `../Assets/` path.

---

### C4 — EPAU MainWindow.xaml: Fix hardcoded absolute toolbar image paths
**File:** `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** Critical  
**Action:** Replaced all 9 absolute backslash image paths in the toolbar with relative `../Assets/` paths:
- `icons8-folder-50.png`, `icons8-refresh-50.png`, `icons8-task-list-50.png`, `icons8-save-50.png`
- `icons8-compare-50.png`, `icons8-analyze-50.png`
- `icons8-opened-folder-50.png`, `icons8-delete-50.png`, `icons8-zip-50.png`

---

### C6 — QSAU MainWindow.xaml: Replace `Name=` with `x:Name=`
**File:** `Query_Store_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** High  
**Action:** Replaced all 57 occurrences of `Name="` (bare attribute) with `x:Name="` (XAML namespace-qualified attribute), matching the convention used by DNAU, DODU, and EPAU.

---

### C7 — DNAU MainWindow.xaml: Replace inline button `ControlTemplate` styles
**File:** `Database_Normalization_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** Medium  
**Action:** Replaced 3 Analysis tab buttons (`btnSaveConfig`, `btnPopulateColumns`, `btnRunFullAnalysisConfig`) that each contained a 20-line inline `<Button.Style>` with full `ControlTemplate` definition.  
Each button was simplified to use `Style="{StaticResource ActionButtonStyle}"` — the named style already defined in the file's `Window.Resources` that provides equivalent visual behavior (blue background, rounded corners, hover state).  
Removed per-button inline `Padding`, `FontSize`, `FontWeight`, `Background`, `Foreground`, `BorderThickness`, `Cursor` attribute overrides (now inherited from `ActionButtonStyle`).

---

### C9 — QSAU MainWindow.xaml: Window property cleanup
**File:** `Query_Store_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml`  
**Severity:** Low  
**Action:**
- Added `ResizeMode="CanResize"` (was omitted; all other utilities declare it explicitly)
- Changed `Background="#F5F5F5"` to `Background="#f4f4f4"` (normalizes to the lowercase hex value used by DNAU, DODU, and EPAU)

---

### C10 — Add `FindName()` null-checks to DNAU, EPAU, QSAU Functions
**Files:**
- `Database_Normalization_Analysis_Utility\Core\WPF\Scripts\NormalizationAnalysisFunctions.ps1`
- `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`
- `Query_Store_Analysis_Utility\Core\WPF\Scripts\QueryStoreAnalysisFunctions.ps1`

**Severity:** Low  
**Action:** Added individual `if (-not ...) { Write-Host "[WARN] Could not find '...'." }` checks after all `FindName()` call blocks, matching the defensive pattern established in DODU's `DatabaseObjectDependencyFunctions.ps1`.

- **DNAU**: Added 21 individual `[WARN]` null-checks for all non-critical UI controls (the existing required-element ERROR loop was preserved as-is)
- **EPAU**: Added 18 `[WARN]` null-checks for config tab, output log, and toolbar button controls (the 4 existing critical `[WARN]` + `return` checks were preserved)
- **QSAU**: Added 19 `[WARN]` null-checks covering connection, reports, results, config, output log, toolbar, status bar, and tab control elements

---

## Files Modified

| File | Changes |
|------|---------|
| `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\Main.ps1` | C1 (dynamic path), C5 (pragmas), C8 (pass ScriptDirectory) |
| `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1` | C8 (accept ScriptDirectory param, update Initialize-Paths), C10 (null-checks) |
| `Execution_Plan_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml` | C4 (relative image paths) |
| `Query_Store_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml` | C2 (relative icon path), C6 (x:Name), C9 (ResizeMode, background) |
| `Query_Store_Analysis_Utility\Core\WPF\Scripts\QueryStoreAnalysisFunctions.ps1` | C10 (null-checks) |
| `Database_Normalization_Analysis_Utility\Core\WPF\Scripts\MainWindow.xaml` | C3 (relative image paths), C7 (inline styles → ActionButtonStyle) |
| `Database_Normalization_Analysis_Utility\Core\WPF\Scripts\NormalizationAnalysisFunctions.ps1` | C10 (null-checks) |

**Files not modified:** DODU (most conformant — no changes required)

---

## Validation

All 4 modified PowerShell files passed `[System.Management.Automation.Language.Parser]::ParseFile()` syntax validation with 0 errors.

---

## Remaining Known Differences (Intentional / Out of Scope)

| Item | Details |
|------|---------|
| QSAU has no dedicated toolbar row | Structural design difference — would require significant XAML restructuring |
| QSAU global implicit styles (DataGrid, TextBox, etc.) | Functional feature of QSAU — not a defect |
| EPAU has no Connection tab | Intentional — EPAU operates on XML files, not live DB connections |
| QSAU `Write-Log` in Main.ps1 | Beneficial enhancement not yet adopted by DNAU/DODU/EPAU |
| EPAU Functions decomposed architecture | More modular — a positive pattern divergence |
| EPAU `.SYNOPSIS` docblocks | Beneficial enhancement not yet adopted by others |
| DNAU `ActionButtonStyle` not in DODU/EPAU/QSAU | Could be shared but low impact |
| DNAU/QSAU status bars vs DODU/EPAU without | Different UI design choices per utility purpose |

*End of changes log.*
