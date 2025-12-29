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
$ScriptDir = if ((Split-Path $BaseDir -Leaf) -eq 'Scripts') { $BaseDir } else { Join-Path $BaseDir 'Scripts' }

Write-Host "[INFO] BaseDir   : $BaseDir"
Write-Host "[INFO] Scripts  : $ScriptDir"

# Import Functions from the Scripts Directory
$FunctionFiles = @(
    "Example1Functions.ps1"
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

# --- Find TabControl in MainWindow ---
$TabControl = $MainWindow.FindName('TabControl')
if (-not $TabControl) { throw "Failed to locate 'TabControl' in MainWindow.xaml" }

# --- Load tab XAMLs (only if present) ---
$tabFiles = @(
    'WelcomeTab.xaml',
    'Example1Tab.xaml',
    'Example2Tab.xaml',
    'Example3Tab.xaml'
)

$tabs = foreach ($f in $tabFiles) {
    $tab = & $loadXaml $f
    if ($tab) {
        # Add without emitting to pipeline
        [void]$TabControl.Items.Add($tab)
        Write-Host "[INFO] Added tab: $($tab.Header)"
    }
}

# --- Optional: load Welcome notes into a TextBox named 'WelcomeNotesBox' ---
try {
    $notesPath = 'C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Welcome_Notes.txt'
    $WelcomeTab = $tabs | Where-Object { $_ -and $_.Name -eq 'WelcomeTab' }  # if you named it in XAML
    if (-not $WelcomeTab) { $WelcomeTab = $TabControl.Items | Where-Object { $_.Header -eq 'Welcome' } }

    if ($WelcomeTab) {
        $notesBox = $WelcomeTab.FindName('WelcomeNotesBox')
        if ($notesBox) {
            if (Test-Path $notesPath) {
                $notesBox.FontFamily = 'Segoe UI Emoji'
                $notesBox.Text = Get-Content -LiteralPath $notesPath -Encoding UTF8 -Raw
                Write-Host "[INFO] Loaded Welcome notes."
            } else {
                $notesBox.Text = "Welcome notes file not found: $notesPath"
                Write-Host "[WARN] Welcome notes file not found: $notesPath"
            }
        } else {
            Write-Host "[WARN] 'WelcomeNotesBox' not found in Welcome tab."
        }
    }
} catch {
    Write-Host "[ERROR] Failed to load Welcome notes: $($_.Exception.Message)"
}

# --- Ensure Example 1 tab content is realized, then init ---
$example1Tab = $TabControl.Items | Where-Object { $_.Header -eq 'Example 1' -or $_.Name -eq 'Example1Tab' }
if ($example1Tab) {
    # Force-load the tab's visual tree so FindName works inside it
    $TabControl.SelectedItem = $welcomeTab
}

try {
    Initialize-Example1 -MainWindow $MainWindow
} catch {
    Write-Host "[ERROR] Initialize-Example1 failed: $($_.Exception.Message)"
}


# --- Show the window (modal) ---
Write-Host "[INFO] Showing window..."
[void]$MainWindow.ShowDialog()
Write-Host "[INFO] UI closed."
