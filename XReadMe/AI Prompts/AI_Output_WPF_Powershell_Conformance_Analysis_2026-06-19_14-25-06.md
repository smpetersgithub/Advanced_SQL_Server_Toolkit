# WPF and PowerShell Conformance Analysis
**Date:** 2026-06-19  
**Time:** 14:25:06  
**Scope:** Read-only analysis — no code modifications made.

---

## Utilities Analyzed

| Alias | Utility Name | Directory |
|-------|-------------|-----------|
| DNAU | Database Normalization Analysis Utility | `C:\Advanced_SQL_Server_Toolkit\Database_Normalization_Analysis_Utility` |
| DODU | Database Object Dependency Utility | `C:\Advanced_SQL_Server_Toolkit\Database_Object_Dependency_Utility` |
| QSAU | Query Store Analysis Utility | `C:\Advanced_SQL_Server_Toolkit\Query_Store_Analysis_Utility` |
| EPAU | Execution Plan Analysis Utility | `C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility` |

---

## Executive Summary

The four utilities share a common overall framework — PowerShell-hosted WPF windows backed by a Functions script — but vary significantly in implementation detail. Two utilities stand out as outliers:

- **QSAU** is the primary outlier for **WPF/XAML** design: it uses no dedicated toolbar row, lacks `x:Name` prefixes on controls, hardcodes an absolute path for its window icon, applies broad global implicit styles absent from other utilities, and has the most expansive tab structure (7 tabs vs. 3–4 in others).
- **EPAU** is the primary outlier for **PowerShell** implementation: its `Main.ps1` hardcodes an absolute path instead of computing it dynamically, omits standard script pragmas (`#Requires`, `Set-StrictMode`, `$ErrorActionPreference`), and passes no path context to its initialization function.
- **DNAU** has secondary WPF inconsistencies: an extra `ActionButtonStyle` not present in other utilities, and inline `ControlTemplate`-based button styles within the Analysis tab that diverge from the shared `ModernButton` approach.
- **DODU** is the most conformant utility overall, and the only one using fully portable relative paths for toolbar image sources in XAML.

---

## WPF Architecture — Per-Utility Overview

### DNAU — `Database_Normalization_Analysis_Utility`
- **File:** `Core\WPF\Scripts\MainWindow.xaml`
- 4-row root `Grid`: Header | Toolbar | Content (TabControl) | Status Bar
- Dark status bar (`Background="#2C3E50"`) with spinning progress indicator and status text
- Blue toolbar row (`Background="#4A90E2"`) with icon buttons grouped in `Border` sections
- **3 named styles** in `Window.Resources`: `ToolbarButtonStyle`, `ActionButtonStyle`, `ModernButton`
- `ActionButtonStyle` is unique to DNAU and not present in any other utility
- Several Analysis tab buttons use **inline `<Button.Style>` with full `ControlTemplate`** (`CornerRadius="5"`) rather than referencing a shared named style — inconsistent with the rest of that utility and with all others
- Toolbar image `Source` attributes use **hardcoded absolute backslash paths** (`C:\Advanced_SQL_Server_Toolkit\...`)
- Window icon uses **relative path** (`../Assets/icons8-xxx.ico`)
- Uses `x:Name` consistently for all named controls
- 4 tabs: Analysis, Connection, Configuration, Output Log
- Header includes "Last Updated: 2026-06-17" text on the right

### DODU — `Database_Object_Dependency_Utility`
- **File:** `Core\WPF\Scripts\MainWindow.xaml`
- 3-row root `Grid`: Header | Toolbar | Content (TabControl)
- No status bar, no progress indicator
- Blue toolbar row with icon buttons — identical structural pattern to DNAU toolbar
- **2 named styles**: `ToolbarButtonStyle`, `ModernButton`
- Toolbar image `Source` attributes use **relative `../Assets/` paths** — the only utility to do so consistently
- Window icon uses **relative path** (`../Assets/icons8-xxx.ico`)
- Uses `x:Name` consistently for all named controls
- 4 tabs: Database Objects, Configuration, Connection, Output Log
- Header includes "Last Updated: 2026-04-02" text on the right

### QSAU — `Query_Store_Analysis_Utility`
- **File:** `Core\WPF\Scripts\MainWindow.xaml`
- 3-row root `Grid`: Header | Content (TabControl) | Status Bar — **no dedicated toolbar row**
- Status bar row present (`Background="#2C3E50"`), but no spinning progress indicator
- Header uses a 3-column layout: logo+title | spacer | action buttons (`btnOpenOutputFolder`, `btnDeleteOutput`) — buttons in the header replace the toolbar concept
- **No `ToolbarButtonStyle`** (since there is no toolbar row)
- **1 named button style**: `ModernButton`
- **Additionally defines 7 global implicit styles** in `Window.Resources`: `DataGrid`, `DataGridColumnHeader`, `DataGridRow`, `DataGridCell`, `TextBox`, `ComboBox`, `Label` — not present in any other utility
- Window icon uses an **absolute forward-slash path** (`C:/Advanced_SQL_Server_Toolkit/.../icons8-paper-plane-ico.ico`) — uniquely uses forward slashes; also hardcoded
- All named controls use `Name` (no `x:` prefix) — inconsistent with DNAU, DODU, EPAU
- Background: `#F5F5F5` vs. `#f4f4f4` used by all other utilities (minor hex case and shade difference)
- No `ResizeMode` attribute declared (others all declare `ResizeMode="CanResize"`)
- No "Last Updated" date in the header
- 7 tabs: Connection, Reports, Results, AI Prompts, QueryID, Configuration, Output Log — most feature-rich
- Has a `ProgressBar` + progress panel (`pnlProgress`, `progressBar`, `txtProgressStatus`) inside the Reports tab
- DataGrid on the Results tab uses globally applied styles (not local inline styles)

### EPAU — `Execution_Plan_Analysis_Utility`
- **File:** `Core\WPF\Scripts\MainWindow.xaml`
- 3-row root `Grid`: Header | Toolbar | Content (TabControl)
- No status bar, no progress indicator
- Blue toolbar row with icon buttons — structurally matching DNAU/DODU
- **2 named styles**: `ToolbarButtonStyle`, `ModernButton`
- Toolbar image `Source` attributes use **hardcoded absolute backslash paths** (`C:\Advanced_SQL_Server_Toolkit\...`) — same issue as DNAU
- Window icon uses **relative path** (`../Assets/icons8-xxx.ico`)
- Uses `x:Name` consistently for all named controls
- 3 tabs: Execution Plans, Configuration, Output Log — fewest tabs; no Connection tab
- No Connection tab (EPAU operates on exported execution plan XML files, not live DB connections)
- Has a `GridSplitter` for user-resizable panels — unique feature not in other utilities
- DataGrid has `IsReadOnly="False"` — allows user editing, unlike DODU and QSAU DataGrids
- DataGrid local styles defined inside `DataGrid.Resources` (not globally in `Window.Resources`)
- Header includes "Last Updated: 2026-06-19" text on the right

---

## WPF Comparison Tables

### 1. Window-Level Properties

| Property | DNAU | DODU | QSAU | EPAU |
|----------|------|------|------|------|
| `Height` | 800 | 800 | 800 | 800 ✅ |
| `Width` | 1400 | 1400 | 1400 | 1400 ✅ |
| `WindowStartupLocation` | CenterScreen | CenterScreen | CenterScreen | CenterScreen ✅ |
| `Background` | `#f4f4f4` | `#f4f4f4` | `#F5F5F5` ⚠️ | `#f4f4f4` |
| `ResizeMode` | `CanResize` | `CanResize` | *(omitted)* ⚠️ | `CanResize` |
| Icon path type | Relative | Relative | **Absolute (fwd slash)** ❌ | Relative |

### 2. Named Style Definitions in Window.Resources

| Style Key | DNAU | DODU | QSAU | EPAU |
|-----------|------|------|------|------|
| `ToolbarButtonStyle` | ✅ | ✅ | ❌ | ✅ |
| `ActionButtonStyle` | ✅ (unique) | ❌ | ❌ | ❌ |
| `ModernButton` | ✅ | ✅ | ✅ | ✅ |
| Global `DataGrid` styles | ❌ | ❌ | ✅ (unique) | ❌ |
| Global `TextBox` / `ComboBox` / `Label` styles | ❌ | ❌ | ✅ (unique) | ❌ |

### 3. Layout Structure

| Row | DNAU | DODU | QSAU | EPAU |
|-----|------|------|------|------|
| Row 0 | Header | Header | Header + Toolbar (merged) | Header |
| Row 1 | Toolbar | Toolbar | Content | Toolbar |
| Row 2 | Content | Content | Status Bar | Content |
| Row 3 | Status Bar | — | — | — |
| **Total rows** | **4** | **3** | **3** | **3** |

### 4. Toolbar Implementation

| Aspect | DNAU | DODU | QSAU | EPAU |
|--------|------|------|------|------|
| Dedicated toolbar row | ✅ | ✅ | ❌ | ✅ |
| Toolbar background | `#4A90E2` | `#4A90E2` | N/A | `#4A90E2` |
| Icon buttons in toolbar | ✅ | ✅ | N/A | ✅ |
| Image path type | **Absolute backslash** ❌ | Relative `../Assets/` ✅ | N/A | **Absolute backslash** ❌ |
| Toolbar button style | `ToolbarButtonStyle` | `ToolbarButtonStyle` | `ModernButton` (in header) | `ToolbarButtonStyle` |

### 5. Control Naming Convention

| Convention | DNAU | DODU | QSAU | EPAU |
|------------|------|------|------|------|
| `x:Name` (standard WPF) | ✅ | ✅ | ❌ | ✅ |
| `Name` (without `x:` prefix) | ❌ | ❌ | ✅ | ❌ |

> **Note:** Both `x:Name` and `Name` are functionally equivalent in WPF code-behind, but `x:Name` is the canonical XAML convention. Consistency requires choosing one across all utilities.

### 6. Tab Inventory

| Tab | DNAU | DODU | QSAU | EPAU |
|-----|------|------|------|------|
| Analysis / Main content | ✅ (Analysis) | ✅ (Database Objects) | ✅ (Reports + Results) | ✅ (Execution Plans) |
| Connection | ✅ | ✅ | ✅ | ❌ |
| Configuration | ✅ | ✅ | ✅ | ✅ |
| Output Log | ✅ | ✅ | ✅ | ✅ |
| AI Prompts | ❌ | ❌ | ✅ | ❌ |
| QueryID | ❌ | ❌ | ✅ | ❌ |
| **Total tabs** | **4** | **4** | **7** | **3** |

### 7. Unique XAML Features per Utility

| Feature | Present In |
|---------|-----------|
| Status bar with spinner | DNAU only |
| `ActionButtonStyle` | DNAU only |
| Inline `ControlTemplate` button styles | DNAU only |
| Relative image paths in toolbar | DODU only |
| `Name` attribute (no `x:` prefix) | QSAU only |
| Global implicit styles (DataGrid, TextBox, ComboBox, Label) | QSAU only |
| ProgressBar inside content tab | QSAU only |
| AI Prompts tab / QueryID tab | QSAU only |
| Absolute icon path with forward slashes | QSAU only |
| Absolute image paths with backslashes in toolbar | DNAU and EPAU |
| `GridSplitter` for resizable panels | EPAU only |
| `IsReadOnly="False"` DataGrid | EPAU only |
| Local DataGrid styles in `DataGrid.Resources` | EPAU only |

### 8. Consistent XAML Areas

| Area | Status |
|------|--------|
| Window dimensions (`Height="800" Width="1400"`) | ✅ All match |
| `WindowStartupLocation="CenterScreen"` | ✅ All match |
| Output Log tab dark console theme (`#1E1E1E` / `#D4D4D4` / Consolas) | ✅ All match |
| Configuration tab layout (ComboBox + GroupBox + TextBlock + 3 buttons) | ✅ All match structurally |
| Connection tab layout (where present) | ✅ DNAU/DODU/QSAU match |
| `ModernButton` style definition | ✅ All define it identically |
| Blue toolbar background `#4A90E2` (where toolbar exists) | ✅ DNAU/DODU/EPAU match |

---

## PowerShell Architecture — Per-Utility Overview

### DNAU — `NormalizationAnalysis` PowerShell
- **Files:** `Core\WPF\Scripts\Main.ps1`, `Core\WPF\Scripts\NormalizationAnalysisFunctions.ps1`
- `Main.ps1`: No file header block. Has `#Requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`
- Path resolution: checks `$PSScriptRoot` → `$MyInvocation.MyCommand.Path` → compiled EXE via `[System.Diagnostics.Process]`
- WPF assemblies loaded via single comma-separated `Add-Type -AssemblyName` call
- XAML loaded via `$loadXaml` scriptblock using `[System.Xml.XmlReader]::Create()` → `[System.Windows.Markup.XamlReader]::Load()`
- Passes `$ScriptDir` to: `Initialize-NormalizationAnalysis -MainWindow $MainWindow -ScriptDirectory $ScriptDir`
- Functions file: monolithic `Initialize-NormalizationAnalysis` function; receives `$ScriptDirectory`; computes `$ProjectRoot` internally with 3× `Split-Path -Parent`; uses `$script:` scope; no section separators
- No explicit null-checks on `FindName()` results; no `.SYNOPSIS` docblocks; `Write-Host "[INFO]..."` logging

### DODU — `DatabaseObjectDependency` PowerShell
- **Files:** `Core\WPF\Scripts\Main.ps1`, `Core\WPF\Scripts\DatabaseObjectDependencyFunctions.ps1`
- `Main.ps1`: No file header block. Has `#Requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`
- Path resolution: slightly different calculation than DNAU — uses `$BaseDir` and `$ScriptDir` as separate variables, resolves via `$PSScriptRoot` → `$MyInvocation.MyCommand.Path` → `$env:EXEPATH` → `Get-Location`
- WPF assemblies loaded identically to DNAU (single comma-separated `Add-Type`)
- XAML loaded via same `$loadXaml` scriptblock pattern as DNAU
- Passes `$ScriptDir` to: `Initialize-DatabaseObjectDependency -MainWindow $MainWindow -ScriptDirectory $ScriptDir`
- Functions file: monolithic `Initialize-DatabaseObjectDependency` function; receives `$ScriptDirectory`; computes `$ProjectRoot` identically to DNAU; uses `$script:` scope
- **Has explicit null-checks after every `FindName()` call** with `[WARN]` message — more defensive than other utilities
- No section separators; `Write-Host "[INFO]..."` logging

### QSAU — `QueryStoreAnalysis` PowerShell
- **Files:** `Core\WPF\Scripts\Main.ps1`, `Core\WPF\Scripts\QueryStoreAnalysisFunctions.ps1`
- `Main.ps1`: **Has a formal file header block** — Title, Description, Author, Last Modified (unique to QSAU)
- Has `#Requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`
- **Has a `Write-Log` function** with `$Level` parameter (INFO/WARN/ERROR/DEBUG/START), color-coded console output, and file-based error logging to `$env:TEMP` — the most sophisticated logging in Main.ps1 of any utility
- Uses `$script:ErrorLogPath` for persistent error log path
- WPF assemblies loaded with **individual `Add-Type` calls per assembly** (not comma-separated) + adds `System.Windows.Forms` assembly not loaded by others
- Assembly loading wrapped in `try/catch` with `[System.Windows.MessageBox]::Show()` on failure — more robust error handling
- XAML loading: uses **`Get-Content -Raw` → `[xml]$xaml` → `New-Object System.Xml.XmlNodeReader`** — different from DNAU/DODU/EPAU
- Checks XAML and Functions paths with explicit `if (-not (Test-Path))` → MessageBox on failure (DNAU/DODU do not show MessageBox)
- Path resolution: `[string]::IsNullOrEmpty($PSScriptRoot)` check → EXE vs. script detection; computes `$ProjectRoot` directly (3× Split-Path)
- Passes `$ProjectRoot` to: `Initialize-QueryStoreAnalysis -MainWindow $MainWindow -ProjectRoot $ProjectRoot`
- Functions file: monolithic `Initialize-QueryStoreAnalysis` function; receives `$ProjectRoot` directly (no internal path computation needed); `# ====` section separators; uses `[DEBUG]` log prefix in some areas vs. `[INFO]` in others

### EPAU — `ExecutionPlanAnalysis` PowerShell
- **Files:** `Core\WPF\Scripts\Main.ps1`, `Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`
- `Main.ps1`: No file header block. **Missing `#Requires -Version 5.1`**; **Missing `Set-StrictMode -Version Latest`**; **Missing `$ErrorActionPreference = 'Stop'`**
- **CRITICAL — Hardcoded path**: `$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"` — not portable; breaks if moved to any other location
- WPF assemblies loaded identically to DNAU/DODU (single comma-separated `Add-Type`)
- XAML loaded via same `$loadXaml` scriptblock pattern as DNAU/DODU (consistent)
- Passes only `$MainWindow` to: `Initialize-ExecutionPlanAnalysis -MainWindow $MainWindow` — **no path context passed**
- **Functions file is architecturally most different**:
  - Has a **module-level CONSTANTS section** at the top (`$script:COMPLETION_CHECK_INTERVAL_SECONDS`, `$script:PYTHON_EXECUTABLE`, `$script:DEFAULT_CONFIG_FILENAME`)
  - Has a **separate `Initialize-Paths` function** that calls `$PSCommandPath` internally — this is intended to resolve paths relative to the running script, but since `Main.ps1` calls it with the hardcoded path, there is a conceptual tension
  - Has separate helper functions: `Test-PythonInstallation`, `Test-Prerequisites`, `Invoke-PythonScripts`
  - All functions have **`.SYNOPSIS` XML doc-comment blocks** — no other utility does this
  - `Initialize-ExecutionPlanAnalysis` receives only `$MainWindow` + optional `$ConfigPath` — relies on `Initialize-Paths` for all path resolution
  - Uses `UPPER_SNAKE_CASE` for constant variable names — no other utility uses this convention

---

## PowerShell Comparison Tables

### 1. Main.ps1 Script Pragmas and Header

| Feature | DNAU | DODU | QSAU | EPAU |
|---------|------|------|------|------|
| File header comment block | ❌ | ❌ | ✅ (Author/Description/Last Modified) | ❌ |
| `#Requires -Version 5.1` | ✅ | ✅ | ✅ | ❌ |
| `Set-StrictMode -Version Latest` | ✅ | ✅ | ✅ | ❌ |
| `$ErrorActionPreference = 'Stop'` | ✅ | ✅ | ✅ | ❌ |

### 2. Path Resolution in Main.ps1

| Approach | DNAU | DODU | QSAU | EPAU |
|----------|------|------|------|------|
| Dynamic path resolution | ✅ | ✅ | ✅ | ❌ |
| Hardcoded absolute path | ❌ | ❌ | ❌ | **YES** ❌ |
| EXE/script detection | ✅ | ✅ | ✅ | N/A |
| `$PSScriptRoot` used | ✅ | ✅ | ✅ | N/A |
| What is resolved | `$ScriptDir` | `$ScriptDir` | `$ProjectRoot` | *(static string)* |

### 3. WPF Assembly Loading in Main.ps1

| Aspect | DNAU | DODU | QSAU | EPAU |
|--------|------|------|------|------|
| Load method | Single `Add-Type` (comma-sep) | Single `Add-Type` (comma-sep) | Individual `Add-Type` per assembly | Single `Add-Type` (comma-sep) |
| Wrapped in `try/catch` | ❌ | ❌ | ✅ | ❌ |
| `System.Windows.Forms` loaded | ❌ | ❌ | ✅ | ❌ |
| Loads PresentationCore/Framework/WindowsBase/System.Xaml | ✅ | ✅ | ✅ | ✅ |

### 4. XAML Loading Approach

| Aspect | DNAU | DODU | QSAU | EPAU |
|--------|------|------|------|------|
| Read method | `[System.Xml.XmlReader]::Create()` | `[System.Xml.XmlReader]::Create()` | `Get-Content -Raw` → `[xml]` cast | `[System.Xml.XmlReader]::Create()` |
| WPF loader | `[System.Windows.Markup.XamlReader]::Load()` | same | same | same |
| Path existence check before loading | ❌ | ❌ | ✅ (with MessageBox) | ✅ (with `throw`) |
| Error handling on load failure | `Write-Host "[ERROR]"` | `Write-Host "[ERROR]"` | MessageBox + `exit 1` | `throw` |

### 5. Logging in Main.ps1

| Approach | DNAU | DODU | QSAU | EPAU |
|----------|------|------|------|------|
| Structured `Write-Log` function | ❌ | ❌ | ✅ | ❌ |
| `Write-Host "[INFO]..."` | ✅ | ✅ | Via `Write-Log` | ✅ |
| File-based error log | ❌ | ❌ | ✅ (`$env:TEMP`) | ❌ |
| Log levels supported | Informal prefix only | Informal prefix only | INFO/WARN/ERROR/DEBUG/START | Informal prefix only |

### 6. Initialize Function Call Signature

| Parameter passed | DNAU | DODU | QSAU | EPAU |
|-----------------|------|------|------|------|
| `$MainWindow` | ✅ | ✅ | ✅ | ✅ |
| `-ScriptDirectory $ScriptDir` | ✅ | ✅ | ❌ | ❌ |
| `-ProjectRoot $ProjectRoot` | ❌ | ❌ | ✅ | ❌ |
| *(no path parameter)* | ❌ | ❌ | ❌ | **YES** |

### 7. Functions File Architecture

| Aspect | DNAU | DODU | QSAU | EPAU |
|--------|------|------|------|------|
| Single monolithic Init function | ✅ | ✅ | ✅ | ✅ (but also helper fns) |
| Separate helper functions | ❌ | ❌ | ❌ | ✅ (`Initialize-Paths`, `Test-PythonInstallation`, `Test-Prerequisites`, `Invoke-PythonScripts`) |
| Module-level CONSTANTS block | ❌ | ❌ | ❌ | ✅ |
| `$ProjectRoot` computed internally | ✅ (from `$ScriptDirectory`) | ✅ (from `$ScriptDirectory`) | ❌ (passed in directly) | ✅ (via `Initialize-Paths`) |
| Path resolution inside Functions | via 3× `Split-Path -Parent` | via 3× `Split-Path -Parent` | N/A (received as param) | via `$PSCommandPath` |
| `.SYNOPSIS` docblocks | ❌ | ❌ | ❌ | ✅ |
| Section separators (`# ====`) | ❌ | ❌ | ✅ | ✅ |
| Null-checks after `FindName()` | ❌ | ✅ (`[WARN]`) | Inconsistent | ❌ |
| Log prefix for UI control wire-up | `[INFO]` | `[INFO]` with null-check | `[DEBUG]` | `[INFO]` |
| Variable naming for constants | N/A | N/A | N/A | `UPPER_SNAKE_CASE` |

### 8. Code Signing

| Aspect | DNAU | DODU | QSAU | EPAU |
|--------|------|------|------|------|
| Main.ps1 code-signed | ✅ DigiCert | ✅ DigiCert | ✅ DigiCert | ✅ DigiCert |
| Functions.ps1 code-signed | ✅ DigiCert | ✅ DigiCert | ✅ DigiCert | ✅ DigiCert |

---

## Consolidated Inconsistency Lists

### WPF / XAML Inconsistencies

| # | Severity | Inconsistency | Utility |
|---|----------|--------------|---------|
| W1 | **High** | Hardcoded absolute window icon path (forward-slash `C:/...`) | QSAU |
| W2 | **High** | Hardcoded absolute toolbar image paths (backslash `C:\...`) | DNAU, EPAU |
| W3 | **High** | `Name` used instead of `x:Name` for all named controls | QSAU |
| W4 | **Medium** | No dedicated toolbar row; toolbar buttons placed in header | QSAU |
| W5 | **Medium** | No `ToolbarButtonStyle` defined | QSAU |
| W6 | **Medium** | `ActionButtonStyle` defined but not shared with other utilities | DNAU |
| W7 | **Medium** | Inline `<Button.Style>` with full `ControlTemplate` in Analysis tab (bypasses shared styles) | DNAU |
| W8 | **Medium** | Global implicit styles for `DataGrid`, `TextBox`, `ComboBox`, `Label` — scope not aligned with others | QSAU |
| W9 | **Medium** | No status bar row | DODU, EPAU |
| W10 | **Low** | `ResizeMode="CanResize"` omitted (implicit default, but not declared) | QSAU |
| W11 | **Low** | Background color `#F5F5F5` (vs. `#f4f4f4` used elsewhere) | QSAU |
| W12 | **Low** | No "Last Updated" date in header | QSAU |
| W13 | **Low** | `ProgressBar` inside content tab (not in status bar) | QSAU |
| W14 | **Low** | `IsReadOnly="False"` on DataGrid | EPAU |
| W15 | **Low** | Local `DataGrid.Resources` styles instead of `Window.Resources` | EPAU |
| W16 | **Informational** | `GridSplitter` for resizable panels | EPAU |

### PowerShell Inconsistencies

| # | Severity | Inconsistency | Utility |
|---|----------|--------------|---------|
| P1 | **Critical** | Hardcoded absolute `$ScriptDir` path — not portable | EPAU |
| P2 | **High** | Missing `#Requires -Version 5.1` | EPAU |
| P3 | **High** | Missing `Set-StrictMode -Version Latest` | EPAU |
| P4 | **High** | Missing `$ErrorActionPreference = 'Stop'` | EPAU |
| P5 | **High** | No path context passed to Initialize function | EPAU |
| P6 | **Medium** | `Initialize-Paths` uses `$PSCommandPath` — conflicts with hardcoded path in Main.ps1 context | EPAU |
| P7 | **Medium** | Different XAML loading method (`Get-Content -Raw` vs `XmlReader::Create`) | QSAU |
| P8 | **Medium** | Assembly loading uses individual `Add-Type` calls instead of comma-separated; loads extra `System.Windows.Forms` | QSAU |
| P9 | **Medium** | No structured `Write-Log` function in Main.ps1 | DNAU, DODU, EPAU |
| P10 | **Medium** | File header comment block absent | DNAU, DODU, EPAU |
| P11 | **Medium** | Assembly loading not wrapped in `try/catch` | DNAU, DODU, EPAU |
| P12 | **Medium** | XAML/Functions load failure shows no user-facing MessageBox | DNAU, DODU |
| P13 | **Low** | Inconsistent parameter name passed to Initialize (`-ScriptDirectory` vs `-ProjectRoot`) | DNAU/DODU vs QSAU |
| P14 | **Low** | `FindName()` results not null-checked in all utilities | DNAU, QSAU, EPAU |
| P15 | **Low** | Module-level CONSTANTS block not used in other utilities | EPAU |
| P16 | **Low** | `.SYNOPSIS` docblocks on functions not used in other utilities | EPAU |
| P17 | **Low** | `UPPER_SNAKE_CASE` constant naming not used in other utilities | EPAU |
| P18 | **Low** | `[DEBUG]` log prefix in FindName section (others use `[INFO]`) | QSAU |
| P19 | **Low** | `$BaseDir` / `$ScriptDir` as separate variables (DODU) vs single `$ScriptDir` (DNAU) | DODU |

---

## Outlier Identification

### Primary XAML Outlier: QSAU
QSAU deviates from the DNAU/DODU/EPAU pattern in the most structural ways:
- Uses `Name` instead of `x:Name` throughout (affects all ~25+ named controls)
- Has no dedicated toolbar row — a fundamental layout difference
- Has no `ToolbarButtonStyle` (because there is no toolbar)
- Has global implicit styles that could unintentionally affect all controls of those types
- Has the hardcoded forward-slash absolute icon path
- Lacks the standard header "Last Updated" date
- Has 7 tabs vs. 3–4 in others

### Primary PowerShell Outlier: EPAU
EPAU deviates from the DNAU/DODU/QSAU pattern most severely:
- The hardcoded `$ScriptDir` is a functional defect — moving the utility to any other path breaks startup
- The missing pragmas mean errors may go undetected or behave unexpectedly
- The Functions file architecture (CONSTANTS block, helper functions, `$PSCommandPath`) is a different design philosophy not shared by others — it is better-structured in some ways, but creates inconsistency

### Secondary WPF Outlier: DNAU
DNAU has the `ActionButtonStyle` (not shared) and inline `ControlTemplate` button definitions that bypass the shared style system — smaller concerns but they create internal DNAU inconsistency as well as inconsistency with other utilities.

### Most Conformant: DODU
DODU is the most conformant overall — it follows the standard pragma/path/assembly pattern in PowerShell, uses `x:Name` and `ToolbarButtonStyle` in XAML, uses fully portable relative image paths (the only utility to do so), and its Functions file is the most defensively coded (`FindName()` null-checks).

---

## Detailed Observations by Category

### Connection and Configuration Tabs (High Consistency Area)
The Configuration tab is highly consistent across all four utilities: a `ComboBox` for file selection at the top, a `GroupBox` containing an editable `TextBox` with `Consolas` font, a `TextBlock` path display below, and three buttons (Refresh, Copy Path, Save Config) using `ModernButton` style. This is the strongest area of alignment.

The Connection tab (DNAU/DODU/QSAU) also follows a consistent layout: Server/Database/Auth/Username/Password with a Test + Save button pair.

### Output Log Tab (High Consistency Area)
All four utilities have an identical Output Log tab: dark console theme (`Background="#1E1E1E"`, `Foreground="#D4D4D4"`, `FontFamily="Consolas"`, `FontSize="11"`), a "Clear Log" red button, and an "Open Logs Folder" blue button. This is the most consistently implemented tab across all four utilities.

### Image Asset Path Strategy (Inconsistent)
There is no consistent approach to image source paths:
- **DODU**: fully relative `../Assets/filename.png` — portable ✅
- **QSAU icon**: absolute forward-slash `C:/Advanced_SQL_Server_Toolkit/...` — breaks on relocation ❌
- **DNAU/EPAU toolbar images**: absolute backslash `C:\Advanced_SQL_Server_Toolkit\...` — breaks on relocation ❌
- **DNAU/DODU/EPAU window icons**: relative `../Assets/...` — portable ✅

The inconsistency means DODU is portable, DNAU/EPAU are partially portable (icon loads but toolbar images don't), and QSAU would fail on both icon and other paths.

### Status Bar Presence (Inconsistent)
DNAU and QSAU have status bars. DODU and EPAU do not. Given that all utilities run Python scripts in the background and report progress, the absence of a status bar in DODU and EPAU is a usability inconsistency.

### Threading and Dispatcher Pattern
All four utilities use `[System.Windows.Application]::Current.Dispatcher.InvokeAsync` (or similar Dispatcher calls) for UI updates from background jobs or runspaces. This is consistent where implemented, though the specifics of how background execution is initiated vary across utilities based on their feature sets.

### Function File Monolithic vs Decomposed Architecture
DNAU, DODU, and QSAU all follow a monolithic approach — one large `Initialize-*` function containing all event handler wiring. EPAU decomposes the initialization into helper functions (`Initialize-Paths`, `Test-Prerequisites`, `Test-PythonInstallation`, `Invoke-PythonScripts`). EPAU's approach is architecturally cleaner but diverges from the established pattern. If the team adopts EPAU's decomposed model, the other utilities would need equivalent refactoring.

---

## Similarities Summary

| Area | Alignment |
|------|-----------|
| Window dimensions (800×1400, CenterScreen) | ✅ All four |
| `ModernButton` style defined | ✅ All four |
| Blue toolbar color `#4A90E2` | ✅ DNAU, DODU, EPAU (where toolbar present) |
| Output Log tab dark console theme | ✅ All four |
| Configuration tab layout | ✅ All four |
| Connection tab layout | ✅ DNAU, DODU, QSAU |
| XAML loaded via `XamlReader::Load()` | ✅ All four |
| `$script:` scope for shared state in Functions | ✅ All four |
| `Write-Host "[INFO]..."` logging prefix style | ✅ All four |
| Code-signed with DigiCert | ✅ All four |
| STA thread enforcement in Main.ps1 | ✅ All four |
| Single Functions.ps1 dot-sourced from Main.ps1 | ✅ All four |

---

## Standardization Priorities

> This section describes differences and their relative importance for future standardization planning. **No code has been modified as part of this analysis.**

### Priority 1 — Critical (Functional/Portability Defects)
1. **EPAU hardcoded `$ScriptDir`** (P1): Replace with dynamic path resolution matching DNAU/DODU pattern. This is the most important fix; the utility currently cannot be relocated.
2. **QSAU/DNAU/EPAU absolute image asset paths** (W1, W2): Replace with relative `../Assets/` paths matching DODU's approach to ensure portability.

### Priority 2 — High (Safety / Reliability)
3. **EPAU missing `#Requires`, `Set-StrictMode`, `$ErrorActionPreference`** (P2, P3, P4): These should be present in all Main.ps1 files for consistent error behavior.
4. **QSAU `Name` → `x:Name`** (W3): All named controls should use `x:Name` for XAML consistency.

### Priority 3 — Medium (Structural Standardization)
5. **DNAU inline button styles** (W7): Replace inline `ControlTemplate` definitions with references to the shared `ModernButton` or `ActionButtonStyle`.
6. **DNAU unique `ActionButtonStyle`** (W6): Either adopt in all utilities or replace with `ModernButton`.
7. **Unified Initialize function signature** (P13): Standardize on either `-ScriptDirectory` or `-ProjectRoot` as the path parameter passed from Main.ps1 to Functions.
8. **QSAU `Write-Log` adoption** (P9, P10): QSAU's `Write-Log` function with level filtering and file logging is the most mature pattern; other utilities could benefit from its adoption.
9. **EPAU `Initialize-Paths` `$PSCommandPath` tension** (P6): Once the hardcoded path is fixed, verify `Initialize-Paths` resolves paths correctly in the Main.ps1 invocation context.

### Priority 4 — Low (Cosmetic / Conventions)
10. **QSAU `ResizeMode` and background color** (W10, W11): Minor — declare `ResizeMode="CanResize"` explicitly and align background to `#f4f4f4`.
11. **Null-checks on `FindName()` results** (P14): Adopt DODU's defensive pattern of checking all `FindName()` results across all utilities.
12. **`.SYNOPSIS` docblocks** (P16): Consider adopting EPAU's practice of documenting functions with `.SYNOPSIS` blocks across all utilities.
13. **QSAU header `Last Updated` date** (W12): Minor presentational consistency.

---

*End of Report — Read-only analysis. No files were modified.*
