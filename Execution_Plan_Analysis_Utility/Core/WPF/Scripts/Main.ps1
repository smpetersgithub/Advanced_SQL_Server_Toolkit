# --- Ensure STA (WPF requires it) ---
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    $self = $MyInvocation.MyCommand.Path
    if (-not $self) { $self = $PSCommandPath }  # fallback
    Start-Process powershell -ArgumentList @(
        '-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',"`"$self`""
    )
    exit
}

# --- Load WPF Assemblies ---
Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase, System.Xaml | Out-Null

# ============================================================================
# HARDCODED PATHS - Update these paths for your environment
# ============================================================================
$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"

Write-Host "[INFO] Scripts  : $ScriptDir"

# Import Functions from the Scripts Directory
$FunctionFiles = @(
    "ExecutionPlanAnalysisFunctions.ps1"
)

foreach ($File in $FunctionFiles) {
    $FilePath = Join-Path -Path $ScriptDir -ChildPath $File
    if (Test-Path $FilePath) {
        . $FilePath
        Write-Host "[INFO] Loaded functions from $File"
    } else {
        Write-Host "[ERROR] Missing function file: $FilePath"
    }
}

# --- Helperless XAML loader (inline) ---
$loadXaml = {
    param([string]$relativePath)
    $full = Join-Path $ScriptDir $relativePath
    if (-not (Test-Path $full)) {
        Write-Host "[ERROR] XAML not found: $full"
        return $null
    }
    try {
        $xr = [System.Xml.XmlReader]::Create($full)
        [System.Windows.Markup.XamlReader]::Load($xr)
    } catch {
        Write-Host "[ERROR] Failed to load $full : $($_.Exception.Message)"
        $null
    }
}

# --- Load Main Window ---
Write-Host "[INFO] Loading MainWindow.xaml..."
$MainWindow = & $loadXaml 'MainWindow.xaml'
if (-not $MainWindow) { throw "Failed to load MainWindow.xaml" }

# --- Initialize the main window (no tabs) ---
try {
    Initialize-ExecutionPlanAnalysis -MainWindow $MainWindow
    Write-Host "[INFO] Main window initialized successfully"
} catch {
    Write-Host "[ERROR] Initialize-ExecutionPlanAnalysis failed: $($_.Exception.Message)"
}


# --- Show the window (modal) ---
Write-Host "[INFO] Showing window..."
[void]$MainWindow.ShowDialog()
Write-Host "[INFO] UI closed."
