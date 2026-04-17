# NormalizationAnalysisFunctions.ps1

function Initialize-NormalizationAnalysis {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow,

        [Parameter(Mandatory)]
        [string]$ScriptDirectory
    )

    Write-Host "[INFO] Normalization Analysis init starting..."

    # ============================================================================
    # CALCULATE PROJECT ROOT DIRECTORY (RELATIVE PATHS)
    # ============================================================================

    # Use the passed ScriptDirectory (works for both .ps1 and .exe)
    $ScriptRoot = $ScriptDirectory

    # Navigate up from Scripts folder to project root
    # Current structure: ProjectRoot\Core\WPF\Scripts\NormalizationAnalysisFunctions.ps1
    # So we need to go up 3 levels: Scripts -> WPF -> Core -> ProjectRoot
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptRoot))

    Write-Host "[INFO] Script Root  : $ScriptRoot"
    Write-Host "[INFO] Project Root : $ProjectRoot"

    # Define all paths relative to project root
    $script:ProjectRoot = $ProjectRoot
    $script:ConfigDir = Join-Path $ProjectRoot "Config"
    $script:OutputDir = Join-Path $ProjectRoot "Output"
    $script:PythonDir = Join-Path $ProjectRoot "Core\Python"
    $script:DatabaseConfigPath = Join-Path $script:ConfigDir "database-config.json"
    $script:TableConfigPath = Join-Path $script:ConfigDir "table-config.json"
    $script:PythonConfigPath = Join-Path $script:ConfigDir "config.json"

    # Create Config directory if it doesn't exist
    if (-not (Test-Path $script:ConfigDir)) {
        Write-Host "[INFO] Creating Config directory: $script:ConfigDir"
        New-Item -Path $script:ConfigDir -ItemType Directory -Force | Out-Null
    }

    # Create Output directory if it doesn't exist
    if (-not (Test-Path $script:OutputDir)) {
        Write-Host "[INFO] Creating Output directory: $script:OutputDir"
        New-Item -Path $script:OutputDir -ItemType Directory -Force | Out-Null
    }

    Write-Host "[INFO] Database Config: $script:DatabaseConfigPath"
    Write-Host "[INFO] Table Config   : $script:TableConfigPath"
    Write-Host "[INFO] Python Config  : $script:PythonConfigPath"
    Write-Host "[INFO] Output Dir     : $script:OutputDir"
    Write-Host "[INFO] Python Dir     : $script:PythonDir"

    # Check Python availability
    if (-not (Test-PythonAvailability)) {
        Write-Host "[ERROR] Python is not available. Please install Python and ensure it's in your PATH."
        [System.Windows.MessageBox]::Show(
            "Python is not installed or not found in PATH.`n`nPlease install Python 3.x and ensure it's added to your system PATH.",
            "Python Not Found",
            "OK",
            "Error"
        )
        return $false
    }

    # Find UI elements - Analysis Tab
    $script:txtTableName = $MainWindow.FindName('txtTableName')
    $script:txtColumns = $MainWindow.FindName('txtColumns')
    $script:txtPrimaryKey = $MainWindow.FindName('txtPrimaryKey')
    $script:txtUniqueKey = $MainWindow.FindName('txtUniqueKey')
    $script:btnSaveConfig = $MainWindow.FindName('btnSaveConfig')
    $script:btnPopulateColumns = $MainWindow.FindName('btnPopulateColumns')

    # Find UI elements - Connection Tab
    $script:txtServer = $MainWindow.FindName('txtServer')
    $script:txtDatabase = $MainWindow.FindName('txtDatabase')
    $script:txtUsername = $MainWindow.FindName('txtUsername')
    $script:txtPassword = $MainWindow.FindName('txtPassword')
    $script:btnTestConnection = $MainWindow.FindName('btnTestConnection')
    $script:btnSaveConnection = $MainWindow.FindName('btnSaveConnection')
    $script:txtConnectionStatus = $MainWindow.FindName('txtConnectionStatus')

    # Find UI elements - Config Tab
    $script:cmbConfigFiles = $MainWindow.FindName('cmbConfigFiles')
    $script:txtConfigContent = $MainWindow.FindName('txtConfigContent')
    $script:txtConfigFilePath = $MainWindow.FindName('txtConfigFilePath')
    $script:btnRefreshConfig = $MainWindow.FindName('btnRefreshConfig')
    $script:btnSaveConfigFile = $MainWindow.FindName('btnSaveConfigFile')
    $script:btnCopyConfigPath = $MainWindow.FindName('btnCopyConfigPath')

    # Find UI elements - Other
    $script:txtOutputLog = $MainWindow.FindName('txtOutputLog')
    $script:txtStatus = $MainWindow.FindName('txtStatus')
    $script:txtProgress = $MainWindow.FindName('txtProgress')
    $script:progressSpinner = $MainWindow.FindName('progressSpinner')

    $script:btnRunFullAnalysis = $MainWindow.FindName('btnRunFullAnalysis')
    $script:btnRunFullAnalysisConfig = $MainWindow.FindName('btnRunFullAnalysisConfig')
    $script:btnOpenOutputFolder = $MainWindow.FindName('btnOpenOutputFolder')
    $script:btnClearOutputFolder = $MainWindow.FindName('btnClearOutputFolder')
    $script:btnClearLog = $MainWindow.FindName('btnClearLog')
    $script:btnOpenLogsFolder = $MainWindow.FindName('btnOpenLogsFolder')

    # Validate that all required UI elements were found
    $requiredElements = @(
        @{Name='txtTableName'; Element=$script:txtTableName},
        @{Name='txtColumns'; Element=$script:txtColumns},
        @{Name='txtOutputLog'; Element=$script:txtOutputLog},
        @{Name='txtStatus'; Element=$script:txtStatus},
        @{Name='txtProgress'; Element=$script:txtProgress}
    )

    $missingElements = @()
    foreach ($item in $requiredElements) {
        if ($null -eq $item.Element) {
            $missingElements += $item.Name
            Write-Host "[ERROR] Required UI element not found: $($item.Name)"
        }
    }

    if ($missingElements.Count -gt 0) {
        Write-Host "[ERROR] Missing UI elements: $($missingElements -join ', ')"
        [System.Windows.MessageBox]::Show(
            "Failed to initialize UI. Missing elements: $($missingElements -join ', ')",
            "Initialization Error",
            "OK",
            "Error"
        )
        return $false
    }

    # Load configurations
    Load-DatabaseConfig
    Load-ConfigFiles

    # Wire up event handlers
    if ($script:btnSaveConfig) { $script:btnSaveConfig.Add_Click({ Save-ConfigurationFromForm }) }
    if ($script:btnPopulateColumns) { $script:btnPopulateColumns.Add_Click({ Run-Step0FromConfigTab }) }
    if ($script:btnRunFullAnalysis) { $script:btnRunFullAnalysis.Add_Click({ Run-FullAnalysis }) }
    if ($script:btnRunFullAnalysisConfig) { $script:btnRunFullAnalysisConfig.Add_Click({ Run-FullAnalysis }) }
    if ($script:btnOpenOutputFolder) { $script:btnOpenOutputFolder.Add_Click({ Open-OutputFolder }) }
    if ($script:btnClearOutputFolder) { $script:btnClearOutputFolder.Add_Click({ Clear-OutputFolder }) }
    if ($script:btnClearLog) { $script:btnClearLog.Add_Click({ Clear-OutputLog }) }
    if ($script:btnOpenLogsFolder) { $script:btnOpenLogsFolder.Add_Click({ Open-LogsFolder }) }

    # Connection Tab event handlers
    if ($script:btnTestConnection) { $script:btnTestConnection.Add_Click({ Test-DatabaseConnection }) }
    if ($script:btnSaveConnection) { $script:btnSaveConnection.Add_Click({ Save-DatabaseConfiguration }) }

    # Config Tab event handlers
    if ($script:cmbConfigFiles) { $script:cmbConfigFiles.Add_SelectionChanged({ On-ConfigFileSelected }) }
    if ($script:btnRefreshConfig) { $script:btnRefreshConfig.Add_Click({ Refresh-ConfigFile }) }
    if ($script:btnSaveConfigFile) { $script:btnSaveConfigFile.Add_Click({ Save-ConfigFile }) }
    if ($script:btnCopyConfigPath) { $script:btnCopyConfigPath.Add_Click({ Copy-ConfigPath }) }

    Update-Status "Ready" "Cyan"
    Write-Host "[INFO] Normalization Analysis initialized successfully"
    return $true
}

function Test-PythonAvailability {
    <#
    .SYNOPSIS
    Check if Python is installed and available in PATH.

    .DESCRIPTION
    Attempts to run 'python --version' to verify Python is installed and accessible.

    .OUTPUTS
    Boolean indicating whether Python is available
    #>
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Python found: $pythonVersion"
            return $true
        } else {
            Write-Host "[WARNING] Python command failed with exit code: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Host "[WARNING] Python not found in PATH: $($_.Exception.Message)"
        return $false
    }
}

function Load-DatabaseConfig {
    <#
    .SYNOPSIS
    Load database and table configuration from JSON files.

    .DESCRIPTION
    Loads database connection settings and table configuration, populating UI elements.
    Handles missing files and invalid JSON gracefully.
    #>
    Write-Host "[INFO] Loading database configuration..."

    # Load database connection config
    if (Test-Path $script:DatabaseConfigPath) {
        try {
            $dbConfig = Get-Content -Path $script:DatabaseConfigPath -Raw | ConvertFrom-Json

            # Validate that dbConfig is an object
            if ($null -eq $dbConfig) {
                throw "Database configuration is empty or null"
            }

            # Populate the form fields with null checks
            if ($script:txtServer -and $dbConfig.PSObject.Properties['servername']) {
                $script:txtServer.Text = $dbConfig.servername
            }
            if ($script:txtDatabase -and $dbConfig.PSObject.Properties['database']) {
                $script:txtDatabase.Text = $dbConfig.database
            }
            if ($script:txtUsername -and $dbConfig.PSObject.Properties['username']) {
                $script:txtUsername.Text = $dbConfig.username
            }
            if ($script:txtPassword -and $dbConfig.PSObject.Properties['password']) {
                $script:txtPassword.Text = $dbConfig.password
            }

            if ($script:txtConnectionStatus) {
                $script:txtConnectionStatus.Text = "Configuration loaded"
                $script:txtConnectionStatus.Foreground = "Green"
            }

            Write-Host "[INFO] Database configuration loaded successfully"

        } catch {
            Write-Host "[ERROR] Failed to load database configuration: $($_.Exception.Message)"
            if ($script:txtConnectionStatus) {
                $script:txtConnectionStatus.Text = "Failed to load configuration"
                $script:txtConnectionStatus.Foreground = "Red"
            }
        }
    } else {
        Write-Host "[WARNING] Database config file not found at $script:DatabaseConfigPath"
        if ($script:txtConnectionStatus) {
            $script:txtConnectionStatus.Text = "No configuration file found"
            $script:txtConnectionStatus.Foreground = "Orange"
        }
    }

    # Load table config
    if (Test-Path $script:TableConfigPath) {
        try {
            $tableConfigContent = Get-Content $script:TableConfigPath -Raw
            $tableConfig = $tableConfigContent | ConvertFrom-Json

            # Validate that tableConfig is an object
            if ($null -eq $tableConfig) {
                throw "Table configuration is empty or null"
            }

            # Populate table fields with null checks
            if ($script:txtTableName) {
                $script:txtTableName.Text = if ($tableConfig.PSObject.Properties['table']) { $tableConfig.table } else { "" }
            }

            # Populate columns (array to multi-line text)
            if ($script:txtColumns) {
                if ($tableConfig.PSObject.Properties['columns'] -and $tableConfig.columns -and $tableConfig.columns.Count -gt 0) {
                    $script:txtColumns.Text = ($tableConfig.columns -join "`r`n")
                } else {
                    $script:txtColumns.Text = ""
                }
            }

            # Populate keys (read-only) - clear first, then populate if exists
            if ($script:txtPrimaryKey) { $script:txtPrimaryKey.Text = "" }
            if ($script:txtUniqueKey) { $script:txtUniqueKey.Text = "" }

            if ($script:txtPrimaryKey -and $tableConfig.PSObject.Properties['primarykey'] -and $tableConfig.primarykey) {
                if ($tableConfig.primarykey -is [array] -and $tableConfig.primarykey.Count -gt 0) {
                    # Compound primary key - wrap in curly braces
                    $script:txtPrimaryKey.Text = "{" + ($tableConfig.primarykey -join ", ") + "}"
                } elseif ($tableConfig.primarykey -is [string] -and $tableConfig.primarykey -ne "") {
                    # Check if it's a comma-separated string (compound key)
                    if ($tableConfig.primarykey -match ",") {
                        $script:txtPrimaryKey.Text = "{" + $tableConfig.primarykey + "}"
                    } else {
                        # Single column key
                        $script:txtPrimaryKey.Text = "{" + $tableConfig.primarykey + "}"
                    }
                }
            }

            if ($script:txtUniqueKey -and $tableConfig.PSObject.Properties['uniquekey'] -and $tableConfig.uniquekey) {
                if ($tableConfig.uniquekey -is [array] -and $tableConfig.uniquekey.Count -gt 0) {
                    # Process each unique key (can be string or array)
                    $uniqueKeyParts = @()
                    foreach ($key in $tableConfig.uniquekey) {
                        if ($key -is [array]) {
                            # Compound unique key
                            $uniqueKeyParts += "{" + ($key -join ", ") + "}"
                        } elseif ($key -is [string] -and $key -ne "") {
                            # Single column unique key
                            $uniqueKeyParts += "{" + $key + "}"
                        }
                    }
                    $script:txtUniqueKey.Text = ($uniqueKeyParts -join ", ")
                } elseif ($tableConfig.uniquekey -is [string] -and $tableConfig.uniquekey -ne "") {
                    # Single unique key as string
                    $script:txtUniqueKey.Text = "{" + $tableConfig.uniquekey + "}"
                }
            }

            Log-Output "Loaded table configuration from: $script:TableConfigPath"

        } catch {
            Write-Host "[ERROR] Failed to load table configuration: $($_.Exception.Message)"
            Log-Output "ERROR: Failed to load table configuration: $($_.Exception.Message)" "Red"
        }
    } else {
        Log-Output "WARNING: Table config file not found at $script:TableConfigPath" "Yellow"
    }
}

# ============================================================================
# CONFIG TAB FUNCTIONS
# ============================================================================

function Load-ConfigFiles {
    Write-Host "[INFO] Loading config files..."

    try {
        # Get all JSON files from the Config directory
        $configFiles = Get-ChildItem -Path $script:ConfigDir -Filter "*.json" | Sort-Object Name

        # Clear and populate the combo box
        $script:cmbConfigFiles.Items.Clear()

        foreach ($file in $configFiles) {
            $script:cmbConfigFiles.Items.Add($file.Name) | Out-Null
        }

        # Select the first item by default
        if ($script:cmbConfigFiles.Items.Count -gt 0) {
            $script:cmbConfigFiles.SelectedIndex = 0
            # Manually trigger the selection changed event to load the content
            On-ConfigFileSelected
        }

        Write-Host "[INFO] Loaded $($configFiles.Count) config files"

    } catch {
        Write-Host "[ERROR] Failed to load config files: $($_.Exception.Message)"
        $script:txtConfigContent.Text = "Error loading configuration files: $($_.Exception.Message)"
    }
}

function On-ConfigFileSelected {
    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        $script:txtConfigFilePath.Text = ""
        return
    }

    Write-Host "[INFO] Loading config file: $selectedFile"

    try {
        $configPath = Join-Path $script:ConfigDir $selectedFile

        if (-not (Test-Path $configPath)) {
            $script:txtConfigContent.Text = "Configuration file not found: $configPath"
            $script:txtConfigFilePath.Text = ""
            Update-Status "Config file not found" "Red"
            return
        }

        # Read the config file
        $configContent = Get-Content $configPath -Raw -Encoding UTF8

        # Display in the text box
        $script:txtConfigContent.Text = $configContent

        # Update the path display to show the selected file path
        $script:txtConfigFilePath.Text = $configPath

        Write-Host "[INFO] Config file loaded: $selectedFile"
        Update-Status "Loaded: $selectedFile" "Cyan"

    } catch {
        Write-Host "[ERROR] Failed to load config: $($_.Exception.Message)"
        $script:txtConfigContent.Text = "Error loading configuration: $($_.Exception.Message)"
        $script:txtConfigFilePath.Text = ""
        Update-Status "Error loading config" "Red"
    }
}

function Save-ConfigFile {
    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        [System.Windows.MessageBox]::Show("No configuration file selected", "Info", "OK", "Information")
        return
    }

    Write-Host "[INFO] Saving config file: $selectedFile"

    try {
        $configPath = Join-Path $script:ConfigDir $selectedFile
        $configContent = $script:txtConfigContent.Text

        # Validate JSON before saving
        try {
            $null = $configContent | ConvertFrom-Json
        } catch {
            $result = [System.Windows.MessageBox]::Show(
                "The configuration content is not valid JSON!`n`nError: $($_.Exception.Message)`n`nDo you want to save anyway?",
                "Invalid JSON",
                "YesNo",
                "Warning"
            )

            if ($result -ne "Yes") {
                Write-Host "[WARN] Save cancelled - invalid JSON"
                return
            }
        }

        # Save the file with UTF8 encoding (no BOM)
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($configPath, $configContent, $utf8NoBom)

        Write-Host "[INFO] Config file saved: $selectedFile"
        Update-Status "Saved: $selectedFile" "Cyan"

        [System.Windows.MessageBox]::Show("Configuration file saved successfully!`n`n$selectedFile", "Success", "OK", "Information")

        # Reload database config if it was changed
        if ($selectedFile -eq "database-config.json") {
            Load-DatabaseConfig
        }

    } catch {
        Write-Host "[ERROR] Failed to save config: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to save configuration file:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

function Refresh-ConfigFile {
    Write-Host "[INFO] Refreshing config file..."

    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        [System.Windows.MessageBox]::Show("No configuration file selected", "Info", "OK", "Information")
        return
    }

    try {
        # Reload the selected config file
        On-ConfigFileSelected

        Write-Host "[INFO] Config file refreshed: $selectedFile"
        Update-Status "Config file refreshed" "Cyan"

        [System.Windows.MessageBox]::Show(
            "Configuration file refreshed successfully!`n`nFile: $selectedFile",
            "Refresh Successful",
            "OK",
            "Information"
        )

    } catch {
        Write-Host "[ERROR] Failed to refresh config file: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to refresh configuration file:`n`n$($_.Exception.Message)",
            "Refresh Failed",
            "OK",
            "Error"
        )
    }
}

function Copy-ConfigPath {
    Write-Host "[INFO] Copying config file path to clipboard..."

    try {
        $path = $script:txtConfigFilePath.Text

        if ([string]::IsNullOrWhiteSpace($path)) {
            [System.Windows.MessageBox]::Show("No file path available", "Info", "OK", "Information")
            return
        }

        # Copy to clipboard
        Set-Clipboard -Value $path

        Write-Host "[INFO] Copied to clipboard: $path"
        Update-Status "Config file path copied to clipboard" "Cyan"

        [System.Windows.MessageBox]::Show("Config file path copied to clipboard!`n`n$path", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to copy path: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to copy path to clipboard:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}


function Save-ConfigurationFromForm {
    try {
        # Show progress
        Update-Progress "Saving..."
        Update-Status "Saving configuration..." "Yellow"

        # Load existing table config to preserve keys
        $existingTableConfig = @{}
        if (Test-Path $script:TableConfigPath) {
            $tableConfigContent = Get-Content $script:TableConfigPath -Raw
            $existingTableConfig = $tableConfigContent | ConvertFrom-Json
        }

        # Parse columns from multi-line text
        $columnsText = $script:txtColumns.Text
        $columnsArray = @()
        if ($columnsText) {
            $columnsArray = $columnsText -split "`r?`n" | Where-Object { $_.Trim() -ne "" } | ForEach-Object { $_.Trim() }
        }

        # Build database connection configuration
        $dbConfig = @{
            servername = $script:txtServer.Text
            database = $script:txtDatabase.Text
            username = $script:txtUsername.Text
            password = $script:txtPassword.Text
        }

        # Build table configuration - preserve existing keys from config file
        $tableConfig = @{
            table = $script:txtTableName.Text
            columns = $columnsArray
            primarykey = if ($existingTableConfig.primarykey) { $existingTableConfig.primarykey } else { "" }
            uniquekey = if ($existingTableConfig.uniquekey) { $existingTableConfig.uniquekey } else { @() }
        }

        # Convert to JSON with proper formatting
        $dbJsonContent = $dbConfig | ConvertTo-Json -Depth 10
        $tableJsonContent = $tableConfig | ConvertTo-Json -Depth 10

        # Save to files
        Set-Content -Path $script:DatabaseConfigPath -Value $dbJsonContent -Force
        Set-Content -Path $script:TableConfigPath -Value $tableJsonContent -Force

        Log-Output "Database configuration saved to: $script:DatabaseConfigPath" "Cyan"
        Log-Output "Table configuration saved to: $script:TableConfigPath" "Cyan"
        Update-Status "Configuration saved successfully" "Cyan"
        Update-Progress ""

        return $true
    } catch {
        Log-Output "ERROR: Failed to save configuration: $($_.Exception.Message)" "Red"
        Update-Status "Failed to save configuration" "Red"
        Update-Progress ""

        [System.Windows.MessageBox]::Show(
            "Failed to save configuration:`n`n$($_.Exception.Message)",
            "Error",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::None
        )

        return $false
    }
}

function Log-Output {
    <#
    .SYNOPSIS
    Log a message to the output log with timestamp.

    .DESCRIPTION
    Appends a timestamped message to the UI output log and console.
    Thread-safe using Dispatcher.

    .PARAMETER Message
    The message to log

    .PARAMETER Color
    Color for console output (not used in UI)
    #>
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message`r`n"

    if ($script:txtOutputLog) {
        $script:txtOutputLog.Dispatcher.Invoke([Action]{
            $script:txtOutputLog.AppendText($logMessage)
            $script:txtOutputLog.ScrollToEnd()
        })
    }

    Write-Host $Message
}

function Update-Status {
    <#
    .SYNOPSIS
    Update the status bar message.

    .DESCRIPTION
    Updates the status text and color in the UI status bar.
    Thread-safe using Dispatcher.

    .PARAMETER Message
    Status message to display

    .PARAMETER Color
    Color for the status text
    #>
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    if ($script:txtStatus) {
        $script:txtStatus.Dispatcher.Invoke([Action]{
            $script:txtStatus.Text = $Message

            # Use custom blue color (#3498DB) instead of Cyan
            if ($Color -eq "Cyan") {
                $brush = New-Object System.Windows.Media.SolidColorBrush
                $brush.Color = [System.Windows.Media.Color]::FromRgb(52, 152, 219)  # #3498DB
            } else {
                $brush = [System.Windows.Media.Brushes]::$Color
            }

            $script:txtStatus.Foreground = $brush
        })
    }
}

function Update-Progress {
    <#
    .SYNOPSIS
    Update the progress indicator.

    .DESCRIPTION
    Updates the progress text and shows/hides the progress spinner.
    Thread-safe using Dispatcher.

    .PARAMETER Message
    Progress message to display (empty string hides spinner)
    #>
    param([string]$Message)

    if ($script:txtProgress) {
        $script:txtProgress.Dispatcher.Invoke([Action]{
            $script:txtProgress.Text = $Message

            # Show/hide spinner based on whether we're running
            if ($script:progressSpinner) {
                if ($Message -ne "") {
                    $script:progressSpinner.Visibility = [System.Windows.Visibility]::Visible
                } else {
                    $script:progressSpinner.Visibility = [System.Windows.Visibility]::Collapsed
                }
            }
        })
    }
}

function Clear-OutputLog {
    $script:txtOutputLog.Clear()
    Log-Output "Log cleared"
}

function Open-LogsFolder {
    <#
    .SYNOPSIS
    Open the Logs folder in Windows Explorer.

    .DESCRIPTION
    Opens the Logs folder in Windows Explorer. Creates the folder if it doesn't exist.
    Uses a default "Logs" path since this utility doesn't have logs configured in config.json.
    #>

    Write-Host "[INFO] Opening Logs folder..."
    Log-Output "Opening Logs folder..."

    try {
        # Use default Logs directory (this utility doesn't have logs in config.json)
        $logsDir = Join-Path $script:ProjectRoot "Logs"
        Write-Host "[INFO] Logs directory: $logsDir"

        # Create the directory if it doesn't exist
        if (-not (Test-Path $logsDir)) {
            Write-Host "[INFO] Creating Logs directory: $logsDir"
            New-Item -Path $logsDir -ItemType Directory -Force | Out-Null
            Log-Output "Created Logs directory: $logsDir"
        }

        # Open in Windows Explorer
        Start-Process explorer.exe -ArgumentList $logsDir
        Log-Output "Opened Logs folder: $logsDir"

    } catch {
        Write-Host "[ERROR] Failed to open Logs folder: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to open Logs folder - $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to open Logs folder:`n`n$($_.Exception.Message)",
            "Error",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Error
        )
    }
}

function Show-ProgressWindow {
    param([string]$Title = "Analysis in Progress")

    [xml]$progressXaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="$Title"
        Height="180"
        Width="450"
        WindowStartupLocation="CenterOwner"
        ResizeMode="NoResize"
        WindowStyle="ToolWindow"
        Background="#f4f4f4">
    <Grid Margin="20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <TextBlock Grid.Row="0"
                   Text="$Title"
                   FontSize="16"
                   FontWeight="Bold"
                   Foreground="#3498DB"
                   Margin="0,0,0,10"/>

        <TextBlock Grid.Row="1"
                   Text="Please wait while the analysis is being performed..."
                   FontSize="12"
                   Margin="0,0,0,15"/>

        <ProgressBar Grid.Row="2"
                     Height="25"
                     IsIndeterminate="True"
                     Foreground="#3498DB"/>
    </Grid>
</Window>
"@

    $progressReader = New-Object System.Xml.XmlNodeReader $progressXaml
    $progressWindow = [Windows.Markup.XamlReader]::Load($progressReader)
    $progressWindow.Owner = $script:MainWindow

    return $progressWindow
}

function Run-PythonScript {
    <#
    .SYNOPSIS
    Execute a Python script and capture its output.

    .DESCRIPTION
    Runs a Python script with optional progress window, captures stdout/stderr,
    and returns success/failure status. Uses unique temp files to avoid conflicts.

    .PARAMETER ScriptName
    Name of the Python script to run

    .PARAMETER StepDescription
    Description of the step for logging and UI

    .PARAMETER ShowProgress
    Whether to show a progress window during execution

    .PARAMETER TimeoutMinutes
    Maximum time to wait for script completion (default: 30 minutes)

    .OUTPUTS
    Boolean indicating success or failure
    #>
    param(
        [string]$ScriptName,
        [string]$StepDescription,
        [switch]$ShowProgress,
        [int]$TimeoutMinutes = 30
    )

    $scriptPath = Join-Path $script:PythonDir $ScriptName

    if (-not (Test-Path $scriptPath)) {
        Log-Output "ERROR: Python script not found: $scriptPath" "Red"
        Update-Status "Error: Script not found" "Red"
        return $false
    }

    Log-Output "========================================" "Cyan"
    Log-Output "Starting: $StepDescription" "Cyan"
    Log-Output "Script: $ScriptName" "Cyan"
    Log-Output "========================================" "Cyan"

    Update-Status "Running: $StepDescription..." "Yellow"

    # Set cursor to wait
    $script:MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

    # Create unique temp files to avoid conflicts
    $uniqueId = [Guid]::NewGuid().ToString()
    $stdoutFile = Join-Path $env:TEMP "py_stdout_$uniqueId.txt"
    $stderrFile = Join-Path $env:TEMP "py_stderr_$uniqueId.txt"

    $progressWindow = $null
    $checkTimer = $null
    $process = $null

    try {
        if ($ShowProgress) {
            # Create progress window
            $progressWindow = Show-ProgressWindow -Title $StepDescription

            # Start Python process without waiting
            $process = Start-Process -FilePath "python" `
                                      -ArgumentList "`"$scriptPath`"" `
                                      -WorkingDirectory $script:ProjectRoot `
                                      -WindowStyle Hidden `
                                      -PassThru `
                                      -RedirectStandardOutput $stdoutFile `
                                      -RedirectStandardError $stderrFile

            # Create timer to check if process has finished
            $checkTimer = New-Object System.Windows.Threading.DispatcherTimer
            $checkTimer.Interval = [TimeSpan]::FromMilliseconds(500)
            $timeoutTime = (Get-Date).AddMinutes($TimeoutMinutes)

            $checkTimer.Add_Tick({
                try {
                    if ($process.HasExited) {
                        $checkTimer.Stop()
                        $progressWindow.Close()
                    } elseif ((Get-Date) -gt $timeoutTime) {
                        # Timeout reached
                        $checkTimer.Stop()
                        Write-Host "[WARNING] Process timeout reached, killing process"
                        if (-not $process.HasExited) {
                            $process.Kill()
                        }
                        $progressWindow.Close()
                    }
                } catch {
                    Write-Host "[ERROR] Timer tick error: $($_.Exception.Message)"
                    $checkTimer.Stop()
                    if ($progressWindow) { $progressWindow.Close() }
                }
            }.GetNewClosure())

            $checkTimer.Start()

            # Show progress window (blocks until closed)
            $progressWindow.ShowDialog() | Out-Null

            # Process has finished, read output
            Start-Sleep -Milliseconds 200

        } else {
            # Run synchronously without progress window
            $process = Start-Process -FilePath "python" `
                                      -ArgumentList "`"$scriptPath`"" `
                                      -WorkingDirectory $script:ProjectRoot `
                                      -WindowStyle Hidden `
                                      -Wait `
                                      -PassThru `
                                      -RedirectStandardOutput $stdoutFile `
                                      -RedirectStandardError $stderrFile
        }

        # Read output
        if (Test-Path $stdoutFile) {
            $stdout = Get-Content $stdoutFile -Raw -ErrorAction SilentlyContinue
            if ($stdout) {
                Log-Output $stdout
            }
        }

        # Read errors
        if (Test-Path $stderrFile) {
            $stderr = Get-Content $stderrFile -Raw -ErrorAction SilentlyContinue
            if ($stderr) {
                Log-Output "STDERR: $stderr" "Red"
            }
        }

        # Check exit code
        $exitCode = $process.ExitCode
        if ($null -eq $exitCode) {
            Log-Output "WARNING: Exit code is null, treating as success" "Yellow"
            $exitCode = 0
        }

        Log-Output "Process exit code: $exitCode"

        if ($exitCode -eq 0) {
            Log-Output "SUCCESS: $StepDescription completed successfully" "Cyan"
            Update-Status "$StepDescription completed" "Cyan"
            return $true
        } else {
            Log-Output "FAILED: $StepDescription failed with exit code: $exitCode" "Red"
            Update-Status "$StepDescription failed" "Red"
            return $false
        }

    } catch {
        Log-Output "ERROR: $($_.Exception.Message)" "Red"
        Update-Status "Error running script" "Red"
        return $false
    } finally {
        # Reset cursor
        if ($script:MainWindow) {
            $script:MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
        }

        # Cleanup
        if ($checkTimer) { $checkTimer.Stop() }
        if ($progressWindow) { $progressWindow.Close() }

        # Kill process if still running
        if ($process -and -not $process.HasExited) {
            Write-Host "[WARNING] Killing process that didn't exit cleanly"
            $process.Kill()
        }

        # Cleanup temp files
        Remove-Item $stdoutFile -ErrorAction SilentlyContinue
        Remove-Item $stderrFile -ErrorAction SilentlyContinue
    }
}

function Run-Step0FromConfigTab {
    # Save configuration first
    if (-not (Save-ConfigurationFromForm)) {
        Log-Output "Aborting: Failed to save configuration" "Red"
        return
    }

    Update-Progress ""
    Update-Status "Retrieving columns from database..." "Yellow"

    # Step 1: Populate columns
    $result = Run-PythonScript "00_populate_columns_from_database.py" "Populate Columns from Database" -ShowProgress
    Update-Progress ""

    if (-not $result) {
        Update-Status "Failed to populate columns" "Red"
        return
    }

    # Wait a moment for file to be written
    Start-Sleep -Milliseconds 500

    # Step 2: Populate keys
    Update-Progress ""
    Update-Status "Retrieving keys from database..." "Yellow"

    $result = Run-PythonScript "01_populate_keys_from_database.py" "Populate Keys from Database" -ShowProgress
    Update-Progress ""

    if ($result) {
        # Wait a moment for file to be written
        Start-Sleep -Milliseconds 500

        # Reload config after both columns and keys are populated
        $script:txtColumns.Dispatcher.Invoke([Action]{
            Load-DatabaseConfig
        })

        Log-Output "Columns and keys have been updated in the Analysis tab" "Cyan"
        Update-Status "Columns and keys populated successfully - Check the sections above" "Cyan"
    } else {
        Update-Status "Failed to populate keys" "Red"
    }
}

function Run-FullAnalysis {
    Log-Output "`n`n"
    Log-Output "======================================================" "Cyan"
    Log-Output "  FULL NORMALIZATION ANALYSIS - ALL STEPS" "Cyan"
    Log-Output "======================================================" "Cyan"
    Log-Output ""

    # Save config first
    if (-not (Save-ConfigurationFromForm)) {
        Log-Output "Aborting: Failed to save configuration" "Red"
        return
    }

    # Run all steps in sequence
    $step1Success = $false
    $step2Success = $false
    $step3Success = $false
    $step4Success = $false

    Update-Progress "Step 1/4"
    $step1Success = Run-PythonScript "01_populate_keys_from_database.py" "Step 1: Populate Keys" -ShowProgress
    Load-DatabaseConfig  # Reload after step 1

    if ($step1Success) {
        Update-Progress "Step 2/4"
        $step2Success = Run-PythonScript "02_analyze_functional_dependencies.py" "Step 2: Analyze Dependencies" -ShowProgress
    }

    if ($step2Success) {
        Update-Progress "Step 3/4"
        $step3Success = Run-PythonScript "03_classify_dependency_relevance.py" "Step 3: Classify Relevance" -ShowProgress
    }

    if ($step3Success) {
        Update-Progress "Step 4/4"
        $step4Success = Run-PythonScript "04_generate_excel_report.py" "Step 4: Generate Report" -ShowProgress
    }

    Update-Progress ""

    # Final summary
    Log-Output ""
    Log-Output "======================================================" "Cyan"
    Log-Output "            ANALYSIS COMPLETE" "Cyan"
    Log-Output "======================================================" "Cyan"

    if ($step1Success -and $step2Success -and $step3Success -and $step4Success) {
        Log-Output "SUCCESS: All steps completed successfully!" "Cyan"
        Update-Status "Analysis complete - All steps successful" "Cyan"

        # Automatically open the latest Excel report
        Open-LatestExcelReport
    } else {
        Log-Output "FAILED: Some steps failed. Please review the log above." "Red"
        Update-Status "Analysis incomplete - Some steps failed" "Red"
    }
}

function Open-OutputFolder {
    if (Test-Path $script:OutputDir) {
        Start-Process explorer.exe $script:OutputDir
        Log-Output "Opened output folder: $script:OutputDir"
    } else {
        Log-Output "Output folder not found: $script:OutputDir" "Yellow"
        [System.Windows.MessageBox]::Show(
            "Output folder does not exist yet.`n`nRun the analysis first to generate output files.",
            "Folder Not Found",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::None
        )
    }
}

function Open-LatestExcelReport {
    if (-not (Test-Path $script:OutputDir)) {
        Log-Output "Output folder not found" "Yellow"
        return
    }

    # Find the latest Excel file
    $excelFiles = Get-ChildItem -Path $script:OutputDir -Filter "*.xlsx" | Sort-Object LastWriteTime -Descending

    if ($excelFiles.Count -eq 0) {
        Log-Output "No Excel reports found in output folder" "Yellow"
        return
    }

    $latestFile = $excelFiles[0].FullName

    # Start Excel without waiting (non-blocking)
    Start-Process -FilePath $latestFile

    Log-Output "Opened Excel report: $($excelFiles[0].Name)" "Cyan"
}

function Clear-OutputFolder {
    # Load cleanup configuration from cleanup-config.json
    $cleanupConfigPath = Join-Path $script:ProjectRoot "Config\cleanup-config.json"

    if (-not (Test-Path $cleanupConfigPath)) {
        Log-Output "ERROR: Cleanup configuration file not found: $cleanupConfigPath" "Red"
        Update-Status "Cleanup configuration not found" "Red"
        return
    }

    try {
        $cleanupConfig = Get-Content $cleanupConfigPath -Raw | ConvertFrom-Json
    } catch {
        Log-Output "ERROR: Failed to read cleanup configuration: $($_.Exception.Message)" "Red"
        Update-Status "Failed to read cleanup configuration" "Red"
        return
    }

    # Get only delete operations (ignore copy_file operations)
    $deleteOperations = $cleanupConfig.cleanup_operations | Where-Object { $_.action -eq "delete_folder" -or $_.action -eq "delete_contents" }

    if ($deleteOperations.Count -eq 0) {
        Log-Output "No delete operations configured in cleanup-config.json" "Yellow"
        return
    }

    # Build confirmation message
    $confirmMessage = "The following folders will be deleted:`n`n"
    foreach ($operation in $deleteOperations) {
        $confirmMessage += "$($operation.path)`n  ($($operation.description))`n`n"
    }
    $confirmMessage += "This action cannot be undone. Continue?"

    # Confirm deletion - SILENT (no sound)
    Add-Type -AssemblyName System.Windows.Forms
    $result = [System.Windows.Forms.MessageBox]::Show(
        $confirmMessage,
        "Confirm Cleanup",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )

    if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
        $totalDeleted = 0
        $totalErrors = 0

        foreach ($operation in $deleteOperations) {
            $path = $operation.path
            $action = $operation.action

            if (-not (Test-Path $path)) {
                Log-Output "Folder does not exist (already deleted): $path" "Yellow"
                continue
            }

            try {
                if ($action -eq "delete_folder") {
                    # Delete entire folder
                    Remove-Item -Path $path -Recurse -Force
                    Log-Output "Deleted folder: $path" "Cyan"
                    $totalDeleted++
                } elseif ($action -eq "delete_contents") {
                    # Delete only contents
                    $items = Get-ChildItem -Path $path -Force
                    foreach ($item in $items) {
                        Remove-Item -Path $item.FullName -Recurse -Force
                    }
                    Log-Output "Deleted contents of: $path" "Cyan"
                    $totalDeleted += $items.Count
                }
            } catch {
                Log-Output "ERROR: Failed to delete $path - $($_.Exception.Message)" "Red"
                $totalErrors++
            }
        }

        if ($totalErrors -eq 0) {
            Log-Output "Cleanup completed successfully - $totalDeleted item(s) deleted" "Cyan"
            Update-Status "Cleanup completed" "Cyan"

            [System.Windows.MessageBox]::Show(
                "Cleanup completed successfully!`n`n$totalDeleted item(s) deleted",
                "Cleanup Complete",
                "OK",
                "Information"
            )
        } else {
            Log-Output "Cleanup completed with $totalErrors error(s)" "Yellow"
            Update-Status "Cleanup completed with errors" "Yellow"

            [System.Windows.MessageBox]::Show(
                "Cleanup completed with errors.`n`n$totalDeleted item(s) deleted`n$totalErrors error(s) occurred",
                "Cleanup Complete",
                "OK",
                "Warning"
            )
        }
    } else {
        Log-Output "Cleanup cancelled by user" "Yellow"
    }
}

function Test-DatabaseConnection {
    <#
    .SYNOPSIS
    Test database connection with current settings.

    .DESCRIPTION
    Attempts to connect to SQL Server using the configured connection settings.
    Properly disposes of connection resources.
    #>
    Write-Host "[INFO] Testing database connection..."

    if ($script:txtConnectionStatus) {
        $script:txtConnectionStatus.Text = "Testing connection..."
        $script:txtConnectionStatus.Foreground = "Orange"
    }

    $connection = $null

    try {
        $server = if ($script:txtServer) { $script:txtServer.Text } else { "" }
        $database = if ($script:txtDatabase) { $script:txtDatabase.Text } else { "" }
        $username = if ($script:txtUsername) { $script:txtUsername.Text } else { "" }
        $password = if ($script:txtPassword) { $script:txtPassword.Text } else { "" }

        if ([string]::IsNullOrWhiteSpace($server) -or [string]::IsNullOrWhiteSpace($database)) {
            [System.Windows.MessageBox]::Show("Server and Database are required fields", "Validation Error", "OK", "Warning")
            if ($script:txtConnectionStatus) {
                $script:txtConnectionStatus.Text = "Validation failed"
                $script:txtConnectionStatus.Foreground = "Red"
            }
            return
        }

        # Build connection string
        if ([string]::IsNullOrWhiteSpace($username)) {
            # Windows Authentication
            $connectionString = "Server=$server;Database=$database;Integrated Security=True;TrustServerCertificate=True;Connection Timeout=15;"
        } else {
            # SQL Server Authentication
            $connectionString = "Server=$server;Database=$database;User Id=$username;Password=$password;TrustServerCertificate=True;Connection Timeout=15;"
        }

        # Test connection
        $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
        $connection.Open()

        if ($script:txtConnectionStatus) {
            $script:txtConnectionStatus.Text = "Connection successful!"
            $script:txtConnectionStatus.Foreground = "Green"
        }

        [System.Windows.MessageBox]::Show(
            "Successfully connected to:`n`nServer: $server`nDatabase: $database",
            "Connection Successful",
            "OK",
            "Information"
        )

        Write-Host "[INFO] Database connection test successful"

    } catch {
        Write-Host "[ERROR] Connection test failed: $($_.Exception.Message)"
        if ($script:txtConnectionStatus) {
            $script:txtConnectionStatus.Text = "Connection failed"
            $script:txtConnectionStatus.Foreground = "Red"
        }

        [System.Windows.MessageBox]::Show(
            "Failed to connect to database:`n`n$($_.Exception.Message)",
            "Connection Failed",
            "OK",
            "Error"
        )
    } finally {
        # Ensure connection is properly disposed
        if ($null -ne $connection) {
            if ($connection.State -eq [System.Data.ConnectionState]::Open) {
                $connection.Close()
            }
            $connection.Dispose()
        }
    }
}

function Save-DatabaseConfiguration {
    Write-Host "[INFO] Saving database configuration..."

    try {
        $server = $script:txtServer.Text
        $database = $script:txtDatabase.Text
        $username = $script:txtUsername.Text
        $password = $script:txtPassword.Text

        if ([string]::IsNullOrWhiteSpace($server) -or [string]::IsNullOrWhiteSpace($database)) {
            [System.Windows.MessageBox]::Show("Server and Database are required fields", "Validation Error", "OK", "Warning")
            return
        }

        # Create configuration object
        $dbConfig = @{
            servername = $server
            database = $database
            username = $username
            password = $password
        }

        # Convert to JSON
        $jsonContent = $dbConfig | ConvertTo-Json -Depth 10

        # Save to file
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($script:DatabaseConfigPath, $jsonContent, $utf8NoBom)

        $script:txtConnectionStatus.Text = "Configuration saved"
        $script:txtConnectionStatus.Foreground = "Green"

        [System.Windows.MessageBox]::Show(
            "Database configuration saved successfully!`n`nFile: $($script:DatabaseConfigPath)",
            "Save Successful",
            "OK",
            "Information"
        )

        Write-Host "[INFO] Database configuration saved to: $script:DatabaseConfigPath"

    } catch {
        Write-Host "[ERROR] Failed to save database configuration: $($_.Exception.Message)"
        $script:txtConnectionStatus.Text = "Save failed"
        $script:txtConnectionStatus.Foreground = "Red"

        [System.Windows.MessageBox]::Show(
            "Failed to save database configuration:`n`n$($_.Exception.Message)",
            "Save Failed",
            "OK",
            "Error"
        )
    }
}

# SIG # Begin signature block
# MIIcQwYJKoZIhvcNAQcCoIIcNDCCHDACAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUW0r9Mu5WsGyxR9kUlQufv/dE
# fm+gghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
# AQsFADBAMT4wPAYDVQQDDDVQb3dlclNoZWxsIENvZGUgU2lnbmluZyAtIEFkdmFu
# Y2VkIFNRTCBTZXJ2ZXIgVG9vbGtpdDAeFw0yNjAzMDUxODIxMjNaFw0zMTAzMDUx
# ODMxMjNaMEAxPjA8BgNVBAMMNVBvd2VyU2hlbGwgQ29kZSBTaWduaW5nIC0gQWR2
# YW5jZWQgU1FMIFNlcnZlciBUb29sa2l0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
# MIIBCgKCAQEAotFBHI1KML2KYPkQWSCtJz7pn9RXbR02WiC9DWqVHZFSQg2tMAz0
# gEZDeStmUbFxdeq34jD1NCe/7a3xBTA/3AL02Lp+WQqZcQpy+jfPYvUQAcfslIX5
# drAb54WtDqqeTFsFPfiqgrMlUeetx2/Tkc0V1UdUsiIbL1rWN1oEXHXmpPfv1NoZ
# 7nAKFDtfynEzXuE+/B3B7FqkoWXEd2AzT2Up6L56qtSpwEJbazOp80L/28q4kyZ4
# /zBIflaVc8kUeqSrvX4C8Gbbo36BKw8CB6v7HT4SQpbURr6NCkdLEBMOSoBpAv3/
# RGVRASRMvAQORPoLifdemPD5bYK8x7uglQIDAQABo0YwRDAOBgNVHQ8BAf8EBAMC
# B4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwHQYDVR0OBBYEFJjfdl8aNDqvP7OzR0yz
# FpqsVRK2MA0GCSqGSIb3DQEBCwUAA4IBAQAB5CXdnzyYiyAPgZEKa1Hw6pBPQZuE
# WvI2KgCwiCIVbT63xiXghbB4u28yrXvCxjChx4oCPgZPJO4yk3bmo0jRWFpzecrm
# x0cwTn+/WY27w7ylC7jOxgbUkiEJS7DaqbIvK5fwOn+hCmidtMgLxrKGE8lNdNga
# 3cA2IrzEVWqrQWzP+488RLwJL3WviIl/JlnzouJQYQ4jfPhYy6zbOlnvipoTyghn
# jyxff2JxVB8JjUzMvJNVKvHZ89mbuXw4/qYEq0aNfIpXLwhid/SzRuPHmerGq0Ba
# vxpcLD7iCVzXZgnr5XJSH5CUy62ggGf5BMvplsZlPpa1D+BQT3IwKte6MIIFjTCC
# BHWgAwIBAgIQDpsYjvnQLefv21DiCEAYWjANBgkqhkiG9w0BAQwFADBlMQswCQYD
# VQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3d3cuZGln
# aWNlcnQuY29tMSQwIgYDVQQDExtEaWdpQ2VydCBBc3N1cmVkIElEIFJvb3QgQ0Ew
# HhcNMjIwODAxMDAwMDAwWhcNMzExMTA5MjM1OTU5WjBiMQswCQYDVQQGEwJVUzEV
# MBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3d3cuZGlnaWNlcnQuY29t
# MSEwHwYDVQQDExhEaWdpQ2VydCBUcnVzdGVkIFJvb3QgRzQwggIiMA0GCSqGSIb3
# DQEBAQUAA4ICDwAwggIKAoICAQC/5pBzaN675F1KPDAiMGkz7MKnJS7JIT3yithZ
# wuEppz1Yq3aaza57G4QNxDAf8xukOBbrVsaXbR2rsnnyyhHS5F/WBTxSD1Ifxp4V
# pX6+n6lXFllVcq9ok3DCsrp1mWpzMpTREEQQLt+C8weE5nQ7bXHiLQwb7iDVySAd
# YyktzuxeTsiT+CFhmzTrBcZe7FsavOvJz82sNEBfsXpm7nfISKhmV1efVFiODCu3
# T6cw2Vbuyntd463JT17lNecxy9qTXtyOj4DatpGYQJB5w3jHtrHEtWoYOAMQjdjU
# N6QuBX2I9YI+EJFwq1WCQTLX2wRzKm6RAXwhTNS8rhsDdV14Ztk6MUSaM0C/CNda
# SaTC5qmgZ92kJ7yhTzm1EVgX9yRcRo9k98FpiHaYdj1ZXUJ2h4mXaXpI8OCiEhtm
# mnTK3kse5w5jrubU75KSOp493ADkRSWJtppEGSt+wJS00mFt6zPZxd9LBADMfRyV
# w4/3IbKyEbe7f/LVjHAsQWCqsWMYRJUadmJ+9oCw++hkpjPRiQfhvbfmQ6QYuKZ3
# AeEPlAwhHbJUKSWJbOUOUlFHdL4mrLZBdd56rF+NP8m800ERElvlEFDrMcXKchYi
# Cd98THU/Y+whX8QgUWtvsauGi0/C1kVfnSD8oR7FwI+isX4KJpn15GkvmB0t9dmp
# sh3lGwIDAQABo4IBOjCCATYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU7Nfj
# gtJxXWRM3y5nP+e6mK4cD08wHwYDVR0jBBgwFoAUReuir/SSy4IxLVGLp6chnfNt
# yA8wDgYDVR0PAQH/BAQDAgGGMHkGCCsGAQUFBwEBBG0wazAkBggrBgEFBQcwAYYY
# aHR0cDovL29jc3AuZGlnaWNlcnQuY29tMEMGCCsGAQUFBzAChjdodHRwOi8vY2Fj
# ZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRBc3N1cmVkSURSb290Q0EuY3J0MEUG
# A1UdHwQ+MDwwOqA4oDaGNGh0dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2Vy
# dEFzc3VyZWRJRFJvb3RDQS5jcmwwEQYDVR0gBAowCDAGBgRVHSAAMA0GCSqGSIb3
# DQEBDAUAA4IBAQBwoL9DXFXnOF+go3QbPbYW1/e/Vwe9mqyhhyzshV6pGrsi+Ica
# aVQi7aSId229GhT0E0p6Ly23OO/0/4C5+KH38nLeJLxSA8hO0Cre+i1Wz/n096ww
# epqLsl7Uz9FDRJtDIeuWcqFItJnLnU+nBgMTdydE1Od/6Fmo8L8vC6bp8jQ87PcD
# x4eo0kxAGTVGamlUsLihVo7spNU96LHc/RzY9HdaXFSMb++hUD38dglohJ9vytsg
# jTVgHAIDyyCwrFigDkBjxZgiwbJZ9VVrzyerbHbObyMt9H5xaiNrIv8SuFQtJ37Y
# OtnwtoeW/VvRXKwYw02fc7cBqZ9Xql4o4rmUMIIGtDCCBJygAwIBAgIQDcesVwX/
# IZkuQEMiDDpJhjANBgkqhkiG9w0BAQsFADBiMQswCQYDVQQGEwJVUzEVMBMGA1UE
# ChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3d3cuZGlnaWNlcnQuY29tMSEwHwYD
# VQQDExhEaWdpQ2VydCBUcnVzdGVkIFJvb3QgRzQwHhcNMjUwNTA3MDAwMDAwWhcN
# MzgwMTE0MjM1OTU5WjBpMQswCQYDVQQGEwJVUzEXMBUGA1UEChMORGlnaUNlcnQs
# IEluYy4xQTA/BgNVBAMTOERpZ2lDZXJ0IFRydXN0ZWQgRzQgVGltZVN0YW1waW5n
# IFJTQTQwOTYgU0hBMjU2IDIwMjUgQ0ExMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A
# MIICCgKCAgEAtHgx0wqYQXK+PEbAHKx126NGaHS0URedTa2NDZS1mZaDLFTtQ2oR
# jzUXMmxCqvkbsDpz4aH+qbxeLho8I6jY3xL1IusLopuW2qftJYJaDNs1+JH7Z+Qd
# SKWM06qchUP+AbdJgMQB3h2DZ0Mal5kYp77jYMVQXSZH++0trj6Ao+xh/AS7sQRu
# QL37QXbDhAktVJMQbzIBHYJBYgzWIjk8eDrYhXDEpKk7RdoX0M980EpLtlrNyHw0
# Xm+nt5pnYJU3Gmq6bNMI1I7Gb5IBZK4ivbVCiZv7PNBYqHEpNVWC2ZQ8BbfnFRQV
# ESYOszFI2Wv82wnJRfN20VRS3hpLgIR4hjzL0hpoYGk81coWJ+KdPvMvaB0WkE/2
# qHxJ0ucS638ZxqU14lDnki7CcoKCz6eum5A19WZQHkqUJfdkDjHkccpL6uoG8pbF
# 0LJAQQZxst7VvwDDjAmSFTUms+wV/FbWBqi7fTJnjq3hj0XbQcd8hjj/q8d6ylgx
# CZSKi17yVp2NL+cnT6Toy+rN+nM8M7LnLqCrO2JP3oW//1sfuZDKiDEb1AQ8es9X
# r/u6bDTnYCTKIsDq1BtmXUqEG1NqzJKS4kOmxkYp2WyODi7vQTCBZtVFJfVZ3j7O
# gWmnhFr4yUozZtqgPrHRVHhGNKlYzyjlroPxul+bgIspzOwbtmsgY1MCAwEAAaOC
# AV0wggFZMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFO9vU0rp5AZ8esri
# kFb2L9RJ7MtOMB8GA1UdIwQYMBaAFOzX44LScV1kTN8uZz/nupiuHA9PMA4GA1Ud
# DwEB/wQEAwIBhjATBgNVHSUEDDAKBggrBgEFBQcDCDB3BggrBgEFBQcBAQRrMGkw
# JAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmRpZ2ljZXJ0LmNvbTBBBggrBgEFBQcw
# AoY1aHR0cDovL2NhY2VydHMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0VHJ1c3RlZFJv
# b3RHNC5jcnQwQwYDVR0fBDwwOjA4oDagNIYyaHR0cDovL2NybDMuZGlnaWNlcnQu
# Y29tL0RpZ2lDZXJ0VHJ1c3RlZFJvb3RHNC5jcmwwIAYDVR0gBBkwFzAIBgZngQwB
# BAIwCwYJYIZIAYb9bAcBMA0GCSqGSIb3DQEBCwUAA4ICAQAXzvsWgBz+Bz0RdnEw
# vb4LyLU0pn/N0IfFiBowf0/Dm1wGc/Do7oVMY2mhXZXjDNJQa8j00DNqhCT3t+s8
# G0iP5kvN2n7Jd2E4/iEIUBO41P5F448rSYJ59Ib61eoalhnd6ywFLerycvZTAz40
# y8S4F3/a+Z1jEMK/DMm/axFSgoR8n6c3nuZB9BfBwAQYK9FHaoq2e26MHvVY9gCD
# A/JYsq7pGdogP8HRtrYfctSLANEBfHU16r3J05qX3kId+ZOczgj5kjatVB+NdADV
# ZKON/gnZruMvNYY2o1f4MXRJDMdTSlOLh0HCn2cQLwQCqjFbqrXuvTPSegOOzr4E
# Wj7PtspIHBldNE2K9i697cvaiIo2p61Ed2p8xMJb82Yosn0z4y25xUbI7GIN/TpV
# fHIqQ6Ku/qjTY6hc3hsXMrS+U0yy+GWqAXam4ToWd2UQ1KYT70kZjE4YtL8Pbzg0
# c1ugMZyZZd/BdHLiRu7hAWE6bTEm4XYRkA6Tl4KSFLFk43esaUeqGkH/wyW4N7Oi
# gizwJWeukcyIPbAvjSabnf7+Pu0VrFgoiovRDiyx3zEdmcif/sYQsfch28bZeUz2
# rtY/9TCA6TD8dC3JE3rYkrhLULy7Dc90G6e8BlqmyIjlgp2+VqsS9/wQD7yFylIz
# 0scmbKvFoW2jNrbM1pD2T7m3XDCCBu0wggTVoAMCAQICEAqA7xhLjfEFgtHEdqeV
# dGgwDQYJKoZIhvcNAQELBQAwaTELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDkRpZ2lD
# ZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVkIEc0IFRpbWVTdGFt
# cGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMTAeFw0yNTA2MDQwMDAwMDBaFw0z
# NjA5MDMyMzU5NTlaMGMxCzAJBgNVBAYTAlVTMRcwFQYDVQQKEw5EaWdpQ2VydCwg
# SW5jLjE7MDkGA1UEAxMyRGlnaUNlcnQgU0hBMjU2IFJTQTQwOTYgVGltZXN0YW1w
# IFJlc3BvbmRlciAyMDI1IDEwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoIC
# AQDQRqwtEsae0OquYFazK1e6b1H/hnAKAd/KN8wZQjBjMqiZ3xTWcfsLwOvRxUwX
# cGx8AUjni6bz52fGTfr6PHRNv6T7zsf1Y/E3IU8kgNkeECqVQ+3bzWYesFtkepEr
# vUSbf+EIYLkrLKd6qJnuzK8Vcn0DvbDMemQFoxQ2Dsw4vEjoT1FpS54dNApZfKY6
# 1HAldytxNM89PZXUP/5wWWURK+IfxiOg8W9lKMqzdIo7VA1R0V3Zp3DjjANwqAf4
# lEkTlCDQ0/fKJLKLkzGBTpx6EYevvOi7XOc4zyh1uSqgr6UnbksIcFJqLbkIXIPb
# cNmA98Oskkkrvt6lPAw/p4oDSRZreiwB7x9ykrjS6GS3NR39iTTFS+ENTqW8m6TH
# uOmHHjQNC3zbJ6nJ6SXiLSvw4Smz8U07hqF+8CTXaETkVWz0dVVZw7knh1WZXOLH
# gDvundrAtuvz0D3T+dYaNcwafsVCGZKUhQPL1naFKBy1p6llN3QgshRta6Eq4B40
# h5avMcpi54wm0i2ePZD5pPIssoszQyF4//3DoK2O65Uck5Wggn8O2klETsJ7u8xE
# ehGifgJYi+6I03UuT1j7FnrqVrOzaQoVJOeeStPeldYRNMmSF3voIgMFtNGh86w3
# ISHNm0IaadCKCkUe2LnwJKa8TIlwCUNVwppwn4D3/Pt5pwIDAQABo4IBlTCCAZEw
# DAYDVR0TAQH/BAIwADAdBgNVHQ4EFgQU5Dv88jHt/f3X85FxYxlQQ89hjOgwHwYD
# VR0jBBgwFoAU729TSunkBnx6yuKQVvYv1Ensy04wDgYDVR0PAQH/BAQDAgeAMBYG
# A1UdJQEB/wQMMAoGCCsGAQUFBwMIMIGVBggrBgEFBQcBAQSBiDCBhTAkBggrBgEF
# BQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQuY29tMF0GCCsGAQUFBzAChlFodHRw
# Oi8vY2FjZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkRzRUaW1lU3Rh
# bXBpbmdSU0E0MDk2U0hBMjU2MjAyNUNBMS5jcnQwXwYDVR0fBFgwVjBUoFKgUIZO
# aHR0cDovL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0VHJ1c3RlZEc0VGltZVN0
# YW1waW5nUlNBNDA5NlNIQTI1NjIwMjVDQTEuY3JsMCAGA1UdIAQZMBcwCAYGZ4EM
# AQQCMAsGCWCGSAGG/WwHATANBgkqhkiG9w0BAQsFAAOCAgEAZSqt8RwnBLmuYEHs
# 0QhEnmNAciH45PYiT9s1i6UKtW+FERp8FgXRGQ/YAavXzWjZhY+hIfP2JkQ38U+w
# tJPBVBajYfrbIYG+Dui4I4PCvHpQuPqFgqp1PzC/ZRX4pvP/ciZmUnthfAEP1HSh
# TrY+2DE5qjzvZs7JIIgt0GCFD9ktx0LxxtRQ7vllKluHWiKk6FxRPyUPxAAYH2Vy
# 1lNM4kzekd8oEARzFAWgeW3az2xejEWLNN4eKGxDJ8WDl/FQUSntbjZ80FU3i54t
# px5F/0Kr15zW/mJAxZMVBrTE2oi0fcI8VMbtoRAmaaslNXdCG1+lqvP4FbrQ6IwS
# BXkZagHLhFU9HCrG/syTRLLhAezu/3Lr00GrJzPQFnCEH1Y58678IgmfORBPC1JK
# kYaEt2OdDh4GmO0/5cHelAK2/gTlQJINqDr6JfwyYHXSd+V08X1JUPvB4ILfJdmL
# +66Gp3CSBXG6IwXMZUXBhtCyIaehr0XkBoDIGMUG1dUtwq1qmcwbdUfcSYCn+Own
# cVUXf53VJUNOaMWMts0VlRYxe5nK+At+DI96HAlXHAL5SlfYxJ7La54i71McVWRP
# 66bW+yERNpbJCjyCYG2j+bdpxo/1Cy4uPcU3AWVPGrbn5PhDBf3Froguzzhk++am
# i+r3Qrx5bIbY3TVzgiFI7Gq3zWcxggUfMIIFGwIBATBUMEAxPjA8BgNVBAMMNVBv
# d2VyU2hlbGwgQ29kZSBTaWduaW5nIC0gQWR2YW5jZWQgU1FMIFNlcnZlciBUb29s
# a2l0AhAkMCFLui38h0VwFeyQJFQCMAkGBSsOAwIaBQCgeDAYBgorBgEEAYI3AgEM
# MQowCKACgAChAoAAMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3AgEEMBwGCisGAQQB
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBRVu/l+WoxdDSkY
# 0KsfUY0LEQI6RjANBgkqhkiG9w0BAQEFAASCAQBcQv5lCyCwhFfpbA3qeNquTjjo
# nmKjwrROrfS7fJodeb6m2SqP80E8qwqJ+cDCwLhA5NBaD8MzPVknblxTdwHpCMmY
# Hpqglkcl7w1pjmQD8ryzQ8uKsewsTulcuN9rfJKJJ/xE81Y2fJg40pldYgvyPCfy
# htiDMOkIyHU8Y/nG9nCExcnhZwsF4DhoOn21u90j0ultDArFtceW4a+CiALdRGS5
# SqC/F+wrslXAM6gmRVMvzDFWL4zG93o01xwBGmJwLTNtElSbdKmjynK5Y+/0/AlN
# X42iEiervhPjl0sUWHwNE4m82sWtRJSPS4/5NAz86Uir04Em84ggJK1AlbWhoYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMTQ1MlowLwYJKoZIhvcNAQkE
# MSIEIIYRAazOiO99gF1akHetnYrhW/V9dqds8mDlo3dZq0OrMA0GCSqGSIb3DQEB
# AQUABIICALSffQFwMOyXFaUPFppCO66db4L4lTjrzoBe8W2PoOTYZqoUQdBc5dTR
# NxE17JbVJNAYwp0VMSCyFJ69YKFevAnVSAyXrvBm9jYWHz41PJ6UcOQypE3CLw9A
# ktTMFjd4xaB6ccigLUeaVcjBFoSNns+uEPVVCO9DNl1eXDI0YSx7O3CN0BJRgMWD
# nxH1OySOpBxOhpnmzk9+cVPJ1ecqnNccTe7TfckCMgkc2Uz/NS8pl5BemkwZQBhL
# KIOzs4Fx50XAwWiY8yqEgq9zMMPVX5HgpNvai2i9urEAdrgkN8k7U7wOW3rjZzQF
# BSWX2UguSsICaplrZxIDkKl5iAUCNOcDjgXphUzlQ+9hQdcTI8FDdFMIH2TAoZnL
# wVBYseE2xgUWTTtByp+3ub5nXDckB8sMCL3lc0zi9/pSUdePaWnqCncbv9MiTuJ+
# +4wlWuy9UU6NgveAxrCezCqaD/ylsvmf1mHTfb1gpfKXNNU2b/IBnHtck0lrLC0q
# kq+T7NX286SGVQOsXbiT5t/CB/P0batoFVuzCAU80YBMzSVVtpuGXVWRixFExB3s
# EjNKDC4aXEnTC+S0usAF/Pj291YvJRFS74OBiwsWihjMr8qO6PxjMxsGQSSpxVkw
# H0YNPedS4KkXygUSeZNYQrvKrRoQbMuoRFUxLyrH2r3E3LXoptvH
# SIG # End signature block
