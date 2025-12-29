# Hardcoded Paths Configuration Guide

## ⚠️ Important Notice

The PowerShell scripts and XAML file now use **hardcoded absolute paths** instead of relative paths. This was done to resolve issues when running the application on different machines.

## 📝 Files with Hardcoded Paths

The following files contain hardcoded paths that **MUST be updated** if you move the application to a different location:

### 1. **Main.ps1**
📄 `Core\WPF\Scripts\Main.ps1`

**Line 16:**
```powershell
$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"
```

### 2. **ExecutionPlanAnalysisFunctions.ps1**
📄 `Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1`

**Lines 17-21:**
```powershell
$script:ProjectRoot = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility"
$script:ConfigDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config"
$script:OutputDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Output"
$script:LogsDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Logs"
$script:PythonDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Python"
```

**Line 25:**
```powershell
$ConfigPath = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config\execution_plan_configurations.json"
```

### 3. **MainWindow.xaml**
📄 `Core\WPF\Scripts\MainWindow.xaml`

**All Image Source attributes (Lines 81, 87, 93, 99, 110, 116, 133, 139, 145, 156):**
```xml
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-folder-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-refresh-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-task-list-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-save-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-compare-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-analyze-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-opened-folder-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-delete-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-zip-50.png" Width="32" Height="32"/>
<Image Source="C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Assets\icons8-github-50.png" Width="32" Height="32"/>
```

## 🔧 How to Update Paths for Your Environment

### Step 1: Determine Your Installation Path

Find where you installed the application. For example:
- Current: `C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility`
- New location: `D:\MyTools\Execution_Plan_Analysis_Utility`

### Step 2: Update Main.ps1

Open `Core\WPF\Scripts\Main.ps1` and update line 16:

```powershell
# OLD:
$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"

# NEW (example):
$ScriptDir = "D:\MyTools\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"
```

### Step 3: Update ExecutionPlanAnalysisFunctions.ps1

Open `Core\WPF\Scripts\ExecutionPlanAnalysisFunctions.ps1` and update lines 17-25:

```powershell
# OLD:
$script:ProjectRoot = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility"
$script:ConfigDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config"
$script:OutputDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Output"
$script:LogsDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Logs"
$script:PythonDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Python"

# NEW (example):
$script:ProjectRoot = "D:\MyTools\Execution_Plan_Analysis_Utility"
$script:ConfigDir = "D:\MyTools\Execution_Plan_Analysis_Utility\Config"
$script:OutputDir = "D:\MyTools\Execution_Plan_Analysis_Utility\Output"
$script:LogsDir = "D:\MyTools\Execution_Plan_Analysis_Utility\Core\Logs"
$script:PythonDir = "D:\MyTools\Execution_Plan_Analysis_Utility\Core\Python"
```

And line 25:
```powershell
# OLD:
$ConfigPath = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config\execution_plan_configurations.json"

# NEW (example):
$ConfigPath = "D:\MyTools\Execution_Plan_Analysis_Utility\Config\execution_plan_configurations.json"
```

### Step 4: Update MainWindow.xaml

Open `Core\WPF\Scripts\MainWindow.xaml` and use Find & Replace:

**Find:**
```
C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility
```

**Replace with:**
```
D:\MyTools\Execution_Plan_Analysis_Utility
```

This will update all 10 icon paths at once.

## ✅ Verification

After updating the paths:

1. **Test the Application:**
   - Run `Core\WPF\Scripts\Build\Execution Plan Analysis Utility.exe`
   - Or run `Main.ps1` directly

2. **Check for Errors:**
   - Icons should display correctly
   - All buttons should work
   - Check the console output for path-related errors

3. **Verify Paths:**
   - Load execution plans - should work
   - Save configuration - should work
   - Compare plans - should work

## 📋 Quick Reference: Current Hardcoded Paths

All paths currently point to:
```
C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility
```

**Directory Structure:**
```
C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\
├── Config\
├── Output\
├── Core\
│   ├── Logs\
│   ├── Python\
│   └── WPF\
│       ├── Assets\
│       │   ├── icons8-folder-50.png
│       │   ├── icons8-refresh-50.png
│       │   ├── icons8-task-list-50.png
│       │   ├── icons8-save-50.png
│       │   ├── icons8-compare-50.png
│       │   ├── icons8-analyze-50.png
│       │   ├── icons8-opened-folder-50.png
│       │   ├── icons8-delete-50.png
│       │   ├── icons8-zip-50.png
│       │   └── icons8-github-50.png
│       └── Scripts\
│           ├── Main.ps1
│           ├── MainWindow.xaml
│           └── ExecutionPlanAnalysisFunctions.ps1
```

## 🔄 Reverting to Relative Paths

If you want to revert to relative paths (dynamic path calculation), you can restore the original versions from version control or contact the developer.

---

**Last Updated:** 2025-12-29

