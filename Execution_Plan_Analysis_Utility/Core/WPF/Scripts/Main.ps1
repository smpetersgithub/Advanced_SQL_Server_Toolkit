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

# --- Resolve BaseDir (root project folder) ---
if ($PSScriptRoot -and (Test-Path $PSScriptRoot)) {
    $BaseDir = Split-Path -Parent $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path -and (Test-Path $MyInvocation.MyCommand.Path)) {
    $BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} elseif ($env:EXEPATH) {
    $BaseDir = Split-Path -Parent $env:EXEPATH
} else {
    $BaseDir = (Get-Location).Path
}

# --- Scripts folder path ---
# Check if we're in the Build folder, if so go up one level to Scripts
$currentFolder = Split-Path $BaseDir -Leaf
if ($currentFolder -eq 'Build') {
    $ScriptDir = Split-Path -Parent $BaseDir
} elseif ($currentFolder -eq 'Scripts') {
    $ScriptDir = $BaseDir
} else {
    $ScriptDir = Join-Path $BaseDir 'Scripts'
}

Write-Host "[INFO] BaseDir   : $BaseDir"
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
