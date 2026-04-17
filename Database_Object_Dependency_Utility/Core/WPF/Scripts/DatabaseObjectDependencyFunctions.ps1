# DatabaseObjectDependencyFunctions.ps1

function Initialize-DatabaseObjectDependency {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow
    )

    Write-Host "[INFO] DatabaseObjectDependency init starting..."

    # ============================================================================
    # CALCULATE PROJECT ROOT DIRECTORY (RELATIVE PATHS)
    # ============================================================================

    # Get the directory where this script is located
    $ScriptRoot = $PSScriptRoot
    if (-not $ScriptRoot) {
        $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    }

    # Navigate up from Scripts folder to project root
    # Current structure: ProjectRoot\Core\WPF\Scripts\DatabaseObjectDependencyFunctions.ps1
    # So we need to go up 3 levels: Scripts -> WPF -> Core -> ProjectRoot
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptRoot))

    Write-Host "[INFO] Script Root  : $ScriptRoot"
    Write-Host "[INFO] Project Root : $ProjectRoot"

    # Define all paths relative to project root
    $script:ProjectRoot = $ProjectRoot
    $script:ConfigDir = Join-Path $ProjectRoot "Config"
    $script:OutputDir = Join-Path $ProjectRoot "Output"
    $script:LogsDir = Join-Path $ProjectRoot "Core\Logs"
    $script:PythonDir = Join-Path $ProjectRoot "Core\Python"

    # Load config.json file from Config directory
    $script:ConfigJsonPath = Join-Path $script:ConfigDir "config.json"

    Write-Host "[INFO] Config JSON  : $script:ConfigJsonPath"
    Write-Host "[INFO] Output Dir   : $script:OutputDir"
    Write-Host "[INFO] Python Dir   : $script:PythonDir"

    # Find the TextBox and Buttons
    $script:txtStoredProceduresInput = $MainWindow.FindName('txtStoredProceduresInput')
    $script:txtDatabaseObjectsFilePath = $MainWindow.FindName('txtDatabaseObjectsFilePath')
    $script:txtConfigFilePath = $MainWindow.FindName('txtConfigFilePath')

    # Connection Tab elements
    $script:txtServer = $MainWindow.FindName('txtServer')
    $script:txtDatabase = $MainWindow.FindName('txtDatabase')
    $script:txtUsername = $MainWindow.FindName('txtUsername')
    $script:txtPassword = $MainWindow.FindName('txtPassword')
    $script:btnTestConnection = $MainWindow.FindName('btnTestConnection')
    $script:btnSaveConnection = $MainWindow.FindName('btnSaveConnection')
    $script:txtConnectionStatus = $MainWindow.FindName('txtConnectionStatus')

    # Config Tab elements
    $script:cmbConfigFiles = $MainWindow.FindName('cmbConfigFiles')
    $script:txtConfigContent = $MainWindow.FindName('txtConfigContent')
    $script:btnRefreshConfig = $MainWindow.FindName('btnRefreshConfig')
    $script:btnSaveConfigFile = $MainWindow.FindName('btnSaveConfigFile')
    $script:btnCopyConfigPath = $MainWindow.FindName('btnCopyConfigPath')

    # Output Log Tab elements
    $script:txtOutputLog = $MainWindow.FindName('txtOutputLog')
    $script:btnClearLog = $MainWindow.FindName('btnClearLog')
    $script:btnOpenLogsFolder = $MainWindow.FindName('btnOpenLogsFolder')

    # Toolbar buttons
    $btnExecuteObjectDependencyAnalysis = $MainWindow.FindName('btnExecuteObjectDependencyAnalysis')
    $btnOpenDirectory = $MainWindow.FindName('btnOpenDirectory')
    $btnCleanup = $MainWindow.FindName('btnCleanup')
    $btnGitHub = $MainWindow.FindName('btnGitHub')

    if (-not $script:txtStoredProceduresInput) {
        Write-Host "[WARN] Could not find 'txtStoredProceduresInput'."
    }
    if (-not $script:txtDatabaseObjectsFilePath) {
        Write-Host "[WARN] Could not find 'txtDatabaseObjectsFilePath'."
    }
    if (-not $script:txtConfigFilePath) {
        Write-Host "[WARN] Could not find 'txtConfigFilePath'."
    }
    if (-not $script:txtServer) {
        Write-Host "[WARN] Could not find 'txtServer'."
    }
    if (-not $script:txtDatabase) {
        Write-Host "[WARN] Could not find 'txtDatabase'."
    }
    if (-not $script:btnTestConnection) {
        Write-Host "[WARN] Could not find 'btnTestConnection'."
    }
    if (-not $script:btnSaveConnection) {
        Write-Host "[WARN] Could not find 'btnSaveConnection'."
    }
    if (-not $script:cmbConfigFiles) {
        Write-Host "[WARN] Could not find 'cmbConfigFiles'."
    }
    if (-not $script:txtConfigContent) {
        Write-Host "[WARN] Could not find 'txtConfigContent'."
    }
    if (-not $script:btnSaveConfigFile) {
        Write-Host "[WARN] Could not find 'btnSaveConfigFile'."
    }
    if (-not $script:btnCopyConfigPath) {
        Write-Host "[WARN] Could not find 'btnCopyConfigPath'."
    }
    if (-not $btnExecuteObjectDependencyAnalysis) {
        Write-Host "[WARN] Could not find 'btnExecuteObjectDependencyAnalysis'."
    }
    if (-not $btnOpenDirectory) {
        Write-Host "[WARN] Could not find 'btnOpenDirectory'."
    }
    if (-not $btnCleanup) {
        Write-Host "[WARN] Could not find 'btnCleanup'."
    }
    if (-not $btnGitHub) {
        Write-Host "[WARN] Could not find 'btnGitHub'."
    }

    # Load and parse config.json to get the stored procedures input file path
    $script:storedProceduresInputFile = $null
    $script:storedProceduresInputPath = $null

    if (Test-Path $script:ConfigJsonPath) {
        Write-Host "[INFO] Loading config.json from: $script:ConfigJsonPath"

        # Parse the config.json file
        $configJson = Get-Content -Path $script:ConfigJsonPath -Raw | ConvertFrom-Json

        # Extract the database_object_input value from files section
        if ($configJson.files.database_object_input) {
            $script:storedProceduresInputFile = $configJson.files.database_object_input
            Write-Host "[INFO] Found database_object_input: $script:storedProceduresInputFile"

            # Build the full path (relative to project root)
            $script:storedProceduresInputPath = Join-Path $script:ProjectRoot $script:storedProceduresInputFile

            # Load the file content
            if (Test-Path $script:storedProceduresInputPath) {
                Write-Host "[INFO] Loading stored procedures from: $script:storedProceduresInputPath"
                # Read with UTF8 without BOM
                $utf8NoBom = New-Object System.Text.UTF8Encoding $false
                $fileContent = [System.IO.File]::ReadAllText($script:storedProceduresInputPath, $utf8NoBom)
                $script:txtStoredProceduresInput.Text = $fileContent
                $script:txtDatabaseObjectsFilePath.Text = "($script:storedProceduresInputFile)"
                Write-Host "[INFO] Successfully loaded stored procedures input file"
            } else {
                Write-Host "[WARN] Stored procedures input file not found: $script:storedProceduresInputPath"
                $script:txtStoredProceduresInput.Text = "File not found: $script:storedProceduresInputPath"
                $script:txtDatabaseObjectsFilePath.Text = "(File not found)"
            }
        } else {
            Write-Host "[WARN] Could not find 'database_object_input' in config.json"
            $script:txtStoredProceduresInput.Text = "Error: 'database_object_input' not found in config.json"
            $script:txtDatabaseObjectsFilePath.Text = "(Configuration error)"
        }
    } else {
        Write-Host "[WARN] config.json not found at: $script:ConfigJsonPath"
        $script:txtStoredProceduresInput.Text = "Error: config.json not found at $script:ConfigJsonPath"
        $script:txtDatabaseObjectsFilePath.Text = "(config.json not found)"
    }

    # Add TextChanged event handler to auto-save when content is modified
    if ($script:txtStoredProceduresInput -and $script:storedProceduresInputPath) {
        # Use a timer to debounce saves (wait after last change before saving)
        $script:saveTimer = $null
        $script:autoSaveDelaySeconds = 1

        $script:txtStoredProceduresInput.Add_TextChanged({
            # Cancel existing timer if it exists
            if ($script:saveTimer) {
                $script:saveTimer.Stop()
                $script:saveTimer = $null
            }

            # Create a new timer that will save after delay with no changes
            $script:saveTimer = New-Object System.Windows.Threading.DispatcherTimer
            $script:saveTimer.Interval = [TimeSpan]::FromSeconds($script:autoSaveDelaySeconds)

            $script:saveTimer.Add_Tick({
                # Stop the timer
                $script:saveTimer.Stop()

                # Save the content
                try {
                    if ($script:storedProceduresInputPath) {
                        $content = $script:txtStoredProceduresInput.Text
                        # Use UTF8 without BOM
                        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
                        [System.IO.File]::WriteAllText($script:storedProceduresInputPath, $content, $utf8NoBom)
                        Write-Host "[INFO] Auto-saved stored procedures input to: $script:storedProceduresInputPath"
                    }
                } catch {
                    Write-Host "[ERROR] Failed to auto-save: $($_.Exception.Message)"
                }
            })

            # Start the timer
            $script:saveTimer.Start()
        })

        Write-Host "[INFO] Auto-save enabled for stored procedures input"
    }

    # ============================================================================
    # INITIALIZE CONFIG TAB
    # ============================================================================

    # Load config files into dropdown and wire up event handlers
    if ($script:cmbConfigFiles -and $script:txtConfigContent) {
        Load-ConfigFiles

        # Wire up event handlers
        $script:cmbConfigFiles.Add_SelectionChanged({ On-ConfigFileSelected })
        $script:btnRefreshConfig.Add_Click({ Refresh-ConfigFile })
        $script:btnSaveConfigFile.Add_Click({ Save-ConfigFile })
        $script:btnCopyConfigPath.Add_Click({ Copy-ConfigPath })

        Write-Host "[INFO] Config tab initialized successfully"
    }

    # ============================================================================
    # LOAD DATABASE CONNECTION CONFIGURATION
    # ============================================================================

    # Get database config path from config.json
    if (Test-Path $script:ConfigJsonPath) {
        $configJson = Get-Content -Path $script:ConfigJsonPath -Raw | ConvertFrom-Json
        if ($configJson.files.database_config) {
            $script:DatabaseConfigPath = Join-Path $script:ProjectRoot $configJson.files.database_config
            Write-Host "[INFO] Database config path: $script:DatabaseConfigPath"
        }
    }

    # Load database configuration into Connection tab
    if ($script:txtServer -and $script:txtDatabase) {
        Load-DatabaseConfiguration
    }

    # ============================================================================
    # CONNECTION TAB EVENT HANDLERS
    # ============================================================================

    if ($script:btnTestConnection) {
        $script:btnTestConnection.Add_Click({ Test-DatabaseConnection })
    }

    if ($script:btnSaveConnection) {
        $script:btnSaveConnection.Add_Click({ Save-DatabaseConfiguration })
    }


    # ============================================================================
    # BUTTON EVENT HANDLERS
    # ============================================================================

    # Execute Object Dependency Analysis Button
    if ($btnExecuteObjectDependencyAnalysis) {
        $btnExecuteObjectDependencyAnalysis.Add_Click({
            Write-Host "[INFO] Execute Object Dependency Analysis button clicked"

            try {
                # Path to the Python script
                $pythonScript = Join-Path $script:PythonDir "00_run_all_scripts.py"

                # Check if the script exists
                if (Test-Path $pythonScript) {
                    Write-Host "[INFO] Running Python script: $pythonScript"

                    # Show confirmation dialog
                    $result = [System.Windows.MessageBox]::Show(
                        "Starting Object Dependency Analysis...`n`nThis may take a few moments.`n`nDo you want to continue?",
                        "Execute Analysis",
                        [System.Windows.MessageBoxButton]::YesNo,
                        [System.Windows.MessageBoxImage]::Question
                    )

                    if ($result -eq [System.Windows.MessageBoxResult]::Yes) {
                        # Close any open Excel processes before running analysis
                        Write-Host "[INFO] Checking for open Excel processes..."
                        try {
                            $excelProcesses = Get-Process -Name "EXCEL" -ErrorAction SilentlyContinue
                            if ($excelProcesses) {
                                Write-Host "[INFO] Found $($excelProcesses.Count) Excel process(es). Closing..."
                                # Try graceful close first
                                $excelProcesses | ForEach-Object { $_.CloseMainWindow() | Out-Null }
                                Start-Sleep -Milliseconds 500
                                # Force kill any remaining processes
                                $remainingProcesses = Get-Process -Name "EXCEL" -ErrorAction SilentlyContinue
                                if ($remainingProcesses) {
                                    $remainingProcesses | Stop-Process -Force
                                    Write-Host "[INFO] Force closed $($remainingProcesses.Count) Excel process(es)"
                                }
                                Write-Host "[INFO] Excel processes closed successfully"
                            } else {
                                Write-Host "[INFO] No Excel processes found"
                            }
                        } catch {
                            Write-Host "[WARN] Error closing Excel: $($_.Exception.Message)"
                        }

                        # Create progress window
                        [xml]$progressXaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Analysis in Progress"
        Height="150"
        Width="400"
        WindowStartupLocation="CenterOwner"
        ResizeMode="NoResize"
        WindowStyle="ToolWindow"
        Topmost="True">
    <Grid Margin="20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
        </Grid.RowDefinitions>

        <TextBlock Grid.Row="0"
                   Text="Running Object Dependency Analysis..."
                   FontSize="14"
                   FontWeight="Bold"
                   Margin="0,0,0,10"/>

        <TextBlock Grid.Row="1"
                   Text="Please wait while the analysis is being performed..."
                   FontSize="12"
                   Margin="0,0,0,15"/>

        <ProgressBar Grid.Row="2"
                     x:Name="progressBar"
                     Height="25"
                     IsIndeterminate="True"/>
    </Grid>
</Window>
"@

                        # Load progress window
                        $progressReader = New-Object System.Xml.XmlNodeReader $progressXaml
                        $progressWindow = [Windows.Markup.XamlReader]::Load($progressReader)
                        $progressWindow.Owner = $MainWindow

                        # Start the Python process without waiting


                        # Use cmd /c to properly capture exit code


                        $psi = New-Object System.Diagnostics.ProcessStartInfo


                        $psi.FileName = "cmd.exe"


                        $psi.Arguments = "/c python `"$pythonScript`""


                        $psi.WorkingDirectory = $script:ProjectRoot


                        $psi.UseShellExecute = $false


                        $psi.CreateNoWindow = $true


                        $process = [System.Diagnostics.Process]::Start($psi)

                        # Create a timer to check if the process has completed
                        $checkTimer = New-Object System.Windows.Threading.DispatcherTimer
                        $checkTimer.Interval = [TimeSpan]::FromMilliseconds(500)

                        $checkTimer.Add_Tick({
                            if ($process.HasExited) {
                                # Stop the timer
                                $checkTimer.Stop()

                                # Close the progress window
                                $progressWindow.Close()

                                # Get the exit code (handle null case)
                                $exitCode = $process.ExitCode
                                if ($null -eq $exitCode) {
                                    $exitCode = -1
                                    Write-Host "[WARN] Process exit code is null, treating as error"
                                }

                                Write-Host "[INFO] Process exited with code: $exitCode"

                                # Check exit code and show completion message
                                if ($exitCode -eq 0) {
                                    Write-Host "[INFO] Analysis completed successfully"
                                    Log-Output "Analysis completed successfully!"
                                    [System.Windows.MessageBox]::Show(
                                        "Object Dependency Analysis completed successfully!`n`nResults have been saved to the Output folder.",
                                        "Analysis Complete",
                                        [System.Windows.MessageBoxButton]::OK,
                                        [System.Windows.MessageBoxImage]::Information
                                    )
                                } else {
                                    Write-Host "[WARN] Analysis completed with exit code: $exitCode"
                                    Log-Output "WARNING: Analysis completed with exit code: $exitCode"
                                    [System.Windows.MessageBox]::Show(
                                        "Analysis completed with warnings or errors.`n`nExit code: $exitCode`n`nCheck the console output for details.",
                                        "Analysis Complete",
                                        [System.Windows.MessageBoxButton]::OK,
                                        [System.Windows.MessageBoxImage]::Warning
                                    )
                                }
                            }
                        })

                        # Start the timer
                        $checkTimer.Start()

                        # Show the progress window (this will block until closed)
                        $progressWindow.ShowDialog() | Out-Null

                    } else {
                        Write-Host "[INFO] Analysis cancelled by user"
                    }
                } else {
                    Write-Host "[ERROR] Python script not found: $pythonScript"
                    [System.Windows.MessageBox]::Show(
                        "Python script not found:`n$pythonScript",
                        "Script Not Found",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Error
                    )
                }
            } catch {
                Write-Host "[ERROR] Failed to run analysis: $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "An error occurred while running the analysis:`n`n$($_.Exception.Message)",
                    "Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            }
        })
    }

    # Open Directory Button
    if ($btnOpenDirectory) {
        $btnOpenDirectory.Add_Click({
            Write-Host "[INFO] Open Directory button clicked"

            # Set cursor to wait (hourglass)
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

            try {
                # Check if the directory exists
                if (Test-Path $script:OutputDir) {
                    Write-Host "[INFO] Opening directory: $script:OutputDir"
                    Start-Process explorer.exe -ArgumentList $script:OutputDir
                } else {
                    Write-Host "[WARN] Output directory does not exist: $script:OutputDir"
                    [System.Windows.MessageBox]::Show(
                        "The output directory does not exist:`n$($script:OutputDir)",
                        "Directory Not Found",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Warning
                    )
                }
            } catch {
                Write-Host "[ERROR] Failed to open directory: $($_.Exception.Message)"
                Log-Output "ERROR: Failed to open directory - $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "An error occurred while opening the directory:`n`n$($_.Exception.Message)",
                    "Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            } finally {
                # Reset cursor to normal
                $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
            }
        })
    }

    # Cleanup Button - Uses cleanup-config.json
    if ($btnCleanup) {
        $btnCleanup.Add_Click({
            Write-Host "[INFO] Cleanup button clicked"
            Log-Output "Cleanup operation started"

            # Set cursor to wait (hourglass)
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

            try {
                # Path to cleanup configuration file
                $cleanupConfigPath = Join-Path $script:ConfigDir "cleanup-config.json"

                # Check if cleanup config exists
                if (-not (Test-Path $cleanupConfigPath)) {
                    Write-Host "[ERROR] Cleanup configuration not found: $cleanupConfigPath"
                    [System.Windows.MessageBox]::Show(
                        "Cleanup configuration file not found:`n$cleanupConfigPath",
                        "Configuration Not Found",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Error
                    )
                    return
                }

                # Load cleanup configuration
                Write-Host "[INFO] Loading cleanup configuration from: $cleanupConfigPath"
                $cleanupConfig = Get-Content $cleanupConfigPath -Raw | ConvertFrom-Json

                # Get only delete operations (ignore copy_file operations)
                $deleteOperations = $cleanupConfig.cleanup_operations | Where-Object { $_.action -eq "delete_folder" }

                if ($deleteOperations.Count -eq 0) {
                    Write-Host "[WARN] No delete operations configured in cleanup-config.json"
                    [System.Windows.MessageBox]::Show(
                        "No delete operations configured in cleanup-config.json",
                        "No Operations",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Information
                    )
                    return
                }

                # Build confirmation message
                $confirmMessage = "This will delete files from the following folders:`n`n"
                foreach ($operation in $deleteOperations) {
                    $confirmMessage += "$($operation.path)`n  ($($operation.description))`n`n"
                }
                $confirmMessage += "This action cannot be undone. Continue?"

                # Confirm with user before proceeding
                $result = [System.Windows.MessageBox]::Show(
                    $confirmMessage,
                    "Confirm Cleanup",
                    [System.Windows.MessageBoxButton]::YesNo,
                    [System.Windows.MessageBoxImage]::Warning
                )

                if ($result -eq [System.Windows.MessageBoxResult]::Yes) {
                    $deletedCount = 0
                    $errorCount = 0

                    # Process each delete operation
                    foreach ($operation in $deleteOperations) {
                        $path = $operation.path
                        $description = $operation.description

                        Write-Host "[INFO] Processing: $description"
                        Write-Host "[INFO] Path: $path"

                        if (Test-Path $path) {
                            # Delete all files in the folder
                            Get-ChildItem -Path $path -File -Recurse | ForEach-Object {
                                try {
                                    Remove-Item $_.FullName -Force
                                    $deletedCount++
                                    Write-Host "[INFO] Deleted: $($_.FullName)"
                                } catch {
                                    $errorCount++
                                    Write-Host "[ERROR] Failed to delete: $($_.FullName) - $($_.Exception.Message)"
                                }
                            }
                        } else {
                            Write-Host "[WARN] Path does not exist: $path"
                        }
                    }

                    # Show completion message
                    if ($errorCount -eq 0) {
                        $message = "Cleanup completed successfully!`n`n$deletedCount file(s) deleted"
                        $icon = [System.Windows.MessageBoxImage]::Information
                    } else {
                        $message = "Cleanup completed with errors.`n`n$deletedCount file(s) deleted`n$errorCount error(s) occurred"
                        $icon = [System.Windows.MessageBoxImage]::Warning
                    }

                    [System.Windows.MessageBox]::Show(
                        $message,
                        "Cleanup Complete",
                        [System.Windows.MessageBoxButton]::OK,
                        $icon
                    )

                    Write-Host "[INFO] Cleanup complete - Deleted: $deletedCount, Errors: $errorCount"
                    Log-Output "Cleanup complete - Deleted: $deletedCount files, Errors: $errorCount"
                } else {
                    Write-Host "[INFO] Cleanup cancelled by user"
                    Log-Output "Cleanup cancelled by user"
                }

            } catch {
                Write-Host "[ERROR] Cleanup failed: $($_.Exception.Message)"
                Log-Output "ERROR: Cleanup failed - $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "An error occurred during cleanup:`n`n$($_.Exception.Message)",
                    "Cleanup Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            } finally {
                # Reset cursor to normal
                $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
            }
        })
    }

    # GitHub Button
    if ($btnGitHub) {
        $btnGitHub.Add_Click({
            Write-Host "[INFO] GitHub button clicked"
            Log-Output "Opening GitHub repository..."

            try {
                # Open GitHub repository in default browser
                Start-Process "https://github.com/smpetersgithub/Advanced_SQL_Server_Toolkit"
                Write-Host "[INFO] Opened GitHub repository in browser"
                Log-Output "Opened GitHub repository in browser"
            } catch {
                Write-Host "[ERROR] Failed to open GitHub URL: $($_.Exception.Message)"
                Log-Output "ERROR: Failed to open GitHub URL - $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "Failed to open GitHub repository.`n`nURL: https://github.com/smpetersgithub/Advanced_SQL_Server_Toolkit",
                    "Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            }
        })
    }

    # Clear Log Button
    if ($script:btnClearLog) {
        $script:btnClearLog.Add_Click({
            Clear-OutputLog
        })
    }

    # Open Logs Folder Button
    if ($script:btnOpenLogsFolder) {
        $script:btnOpenLogsFolder.Add_Click({
            Open-LogsFolder
        })
    }

    # Log initialization complete
    Log-Output "Database Object Dependency Utility initialized successfully"

    Write-Host "[INFO] ExecutionPlanAnalysis init complete."
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

    Write-Host "[INFO] Config file selected: $selectedFile"
    Log-Output "Loading config file: $selectedFile"

    try {
        $configPath = Join-Path $script:ConfigDir $selectedFile

        if (Test-Path $configPath) {
            # Read with UTF8 without BOM
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            $configRaw = [System.IO.File]::ReadAllText($configPath, $utf8NoBom)

            # Pretty-print the JSON for better readability
            try {
                $configObject = $configRaw | ConvertFrom-Json
                $configPretty = $configObject | ConvertTo-Json -Depth 10
                $script:txtConfigContent.Text = $configPretty
            } catch {
                # If JSON parsing fails, show raw content
                $script:txtConfigContent.Text = $configRaw
            }

            $script:txtConfigFilePath.Text = $configPath
            Write-Host "[INFO] Loaded config file: $configPath"
            Log-Output "Config file loaded successfully"
        } else {
            $script:txtConfigContent.Text = "Error: File not found at $configPath"
            $script:txtConfigFilePath.Text = "(File not found)"
            Write-Host "[WARN] Config file not found: $configPath"
            Log-Output "WARNING: Config file not found"
        }

    } catch {
        Write-Host "[ERROR] Failed to load config file: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to load config file - $($_.Exception.Message)"
        $script:txtConfigContent.Text = "Error loading file: $($_.Exception.Message)"
        $script:txtConfigFilePath.Text = "(Error)"
    }
}

function Save-ConfigFile {
    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        [System.Windows.MessageBox]::Show("No configuration file selected", "Info", "OK", "Information")
        return
    }

    Write-Host "[INFO] Saving config file: $selectedFile"
    Log-Output "Saving config file: $selectedFile"

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

        # Save with UTF8 without BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($configPath, $configContent, $utf8NoBom)

        Write-Host "[INFO] Config file saved successfully: $configPath"
        Log-Output "Config file saved successfully"
        [System.Windows.MessageBox]::Show("Configuration file saved successfully!`n`n$configPath", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to save config file: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to save config file - $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to save configuration file:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

function Refresh-ConfigFile {
    Write-Host "[INFO] Refreshing config file..."
    Log-Output "Refreshing config file..."

    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        [System.Windows.MessageBox]::Show("No configuration file selected", "Info", "OK", "Information")
        return
    }

    try {
        # Reload the selected config file
        On-ConfigFileSelected

        Write-Host "[INFO] Config file refreshed: $selectedFile"

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
    Log-Output "Copying config file path to clipboard..."

    try {
        $path = $script:txtConfigFilePath.Text

        if ([string]::IsNullOrWhiteSpace($path)) {
            [System.Windows.MessageBox]::Show("No file path available", "Info", "OK", "Information")
            return
        }

        # Copy to clipboard
        Set-Clipboard -Value $path

        Write-Host "[INFO] Copied to clipboard: $path"
        Log-Output "Path copied to clipboard successfully"
        [System.Windows.MessageBox]::Show("Config file path copied to clipboard!`n`n$path", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to copy path: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to copy path - $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to copy path to clipboard:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

# ============================================================================
# CONNECTION TAB FUNCTIONS
# ============================================================================

function Load-DatabaseConfiguration {
    Write-Host "[INFO] Loading database configuration..."

    try {
        if (-not (Test-Path $script:DatabaseConfigPath)) {
            Write-Host "[WARN] Database config file not found: $script:DatabaseConfigPath"
            return
        }

        $dbConfig = Get-Content -Path $script:DatabaseConfigPath -Raw | ConvertFrom-Json

        # Populate the form fields
        if ($dbConfig.server) {
            $script:txtServer.Text = $dbConfig.server
        }
        if ($dbConfig.database) {
            $script:txtDatabase.Text = $dbConfig.database
        }
        if ($dbConfig.username) {
            $script:txtUsername.Text = $dbConfig.username
        }
        if ($dbConfig.password) {
            $script:txtPassword.Text = $dbConfig.password
        }

        $script:txtConnectionStatus.Text = "Configuration loaded"
        $script:txtConnectionStatus.Foreground = "Green"

        Write-Host "[INFO] Database configuration loaded successfully"

    } catch {
        Write-Host "[ERROR] Failed to load database configuration: $($_.Exception.Message)"
        $script:txtConnectionStatus.Text = "Failed to load configuration"
        $script:txtConnectionStatus.Foreground = "Red"
    }
}

function Test-DatabaseConnection {
    Write-Host "[INFO] Testing database connection..."
    Log-Output "Testing database connection..."

    $script:txtConnectionStatus.Text = "Testing connection..."
    $script:txtConnectionStatus.Foreground = "Orange"

    try {
        $server = $script:txtServer.Text
        $database = $script:txtDatabase.Text
        $username = $script:txtUsername.Text
        $password = $script:txtPassword.Text

        if ([string]::IsNullOrWhiteSpace($server) -or [string]::IsNullOrWhiteSpace($database)) {
            [System.Windows.MessageBox]::Show("Server and Database are required fields", "Validation Error", "OK", "Warning")
            $script:txtConnectionStatus.Text = "Validation failed"
            $script:txtConnectionStatus.Foreground = "Red"
            return
        }

        # Build connection string
        if ([string]::IsNullOrWhiteSpace($username)) {
            # Windows Authentication
            $connectionString = "Server=$server;Database=$database;Integrated Security=True;TrustServerCertificate=True;"
        } else {
            # SQL Server Authentication
            $connectionString = "Server=$server;Database=$database;User Id=$username;Password=$password;TrustServerCertificate=True;"
        }

        # Test connection
        $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
        $connection.Open()
        $connection.Close()

        $script:txtConnectionStatus.Text = "Connection successful!"
        $script:txtConnectionStatus.Foreground = "Green"

        [System.Windows.MessageBox]::Show(
            "Successfully connected to:`n`nServer: $server`nDatabase: $database",
            "Connection Successful",
            "OK",
            "Information"
        )

        Write-Host "[INFO] Database connection test successful"
        Log-Output "Database connection test successful!"

    } catch {
        Write-Host "[ERROR] Connection test failed: $($_.Exception.Message)"
        Log-Output "ERROR: Connection test failed - $($_.Exception.Message)"
        $script:txtConnectionStatus.Text = "Connection failed"
        $script:txtConnectionStatus.Foreground = "Red"

        [System.Windows.MessageBox]::Show(
            "Failed to connect to database:`n`n$($_.Exception.Message)",
            "Connection Failed",
            "OK",
            "Error"
        )
    }
}

function Save-DatabaseConfiguration {
    Write-Host "[INFO] Saving database configuration..."
    Log-Output "Saving database configuration..."

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
            server = $server
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
        Log-Output "Database configuration saved successfully"

    } catch {
        Write-Host "[ERROR] Failed to save database configuration: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to save database configuration - $($_.Exception.Message)"
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

function Clear-OutputLog {
    if ($script:txtOutputLog) {
        $script:txtOutputLog.Clear()
        Log-Output "Log cleared"
    }
}

function Open-LogsFolder {
    <#
    .SYNOPSIS
    Open the Logs folder in Windows Explorer.

    .DESCRIPTION
    Reads the log_dir path from config.json and opens it in Windows Explorer.
    Creates the folder if it doesn't exist.
    #>

    Write-Host "[INFO] Opening Logs folder..."
    Log-Output "Opening Logs folder..."

    try {
        # Read config.json to get the log_dir path
        $logsDir = $null

        if (Test-Path $script:ConfigJsonPath) {
            $configJson = Get-Content -Path $script:ConfigJsonPath -Raw | ConvertFrom-Json

            if ($configJson.paths.log_dir) {
                # Construct full path
                $logsDir = Join-Path $script:ProjectRoot $configJson.paths.log_dir
                Write-Host "[INFO] Logs directory from config: $logsDir"
            } else {
                Write-Host "[WARN] log_dir not found in config.json, using default"
                $logsDir = Join-Path $script:ProjectRoot "Logs"
            }
        } else {
            Write-Host "[WARN] config.json not found, using default Logs directory"
            $logsDir = Join-Path $script:ProjectRoot "Logs"
        }

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

# SIG # Begin signature block
# MIIcQwYJKoZIhvcNAQcCoIIcNDCCHDACAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUw14Ur5grjxODDbu9yniSkUsx
# YtmgghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
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
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBT4suJtXydFSIVC
# QrpIMYdEQp9z5DANBgkqhkiG9w0BAQEFAASCAQA4IPG5kLg1yeISL34fPVBp5g6F
# NKFn53d2eH7NiBHKG0aIsCtwzbKngxlYpluHk365zLoky9gfC+s/y2McdEsBpNoN
# eEIiYaImyqwAsKSpcBKCI+zlogZYEvJaCGan1qU0iuaab0bqz0Y0hLZXEzQqFVB2
# gj7tF3MWWZyiXVQZMTGKFBMtS44HeqMn24wptnxiQ8NL09CyHKCAy8k0wL0LyUNt
# xJ2GHkYOvz8hanpjNAEYFNU05xupjddykcjqj8uZaR9Cu5RhofEiM1a1Yn/jzE8z
# E0PDkxOK/sQE306SBSRvKmcszWu6KTq8NqPkKzsK1lRc9DEQn1/mF/EimAJeoYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMTIzM1owLwYJKoZIhvcNAQkE
# MSIEIMJufqG74qpJVkgUhRBRzp7EZK/YAtURgcBJ58yd+WWrMA0GCSqGSIb3DQEB
# AQUABIICADxySt6HrG6c3ArATLLG8DF408RHYNR3vJgXt3muzujWZ/KaX8d75RqJ
# 5Tpdku1fx0raKT0z7Jgkpnf6hjTumtP9M8XvrLftF8JzQfbidW+1qtrUGNfKqcUm
# qwX3R2bO1GHw2oJSf6ebWy1Ef2cjOUfh0KjNKLpiK3R3f31kGpRV8FlvQyP4g1+C
# feM8ZgXcZFe3Hpoa3a9Vaj17OhrRwIFHmzHq1XruIWlFcYtrbc7Mi5lVJotYAfBP
# ogcJdGwHwY4NZVgC7ms0DugQtWb0aOKyJlspyYEkPNk7sFpBDy+zR2z8RA50/84T
# G/pgC/SOFMSgoqt/n56HZK+i731UVoJRQXwEXjBVHX0Ek6rETXrMwVRL2vgWaum9
# cIJbS2yxQk4E9M0uJ+M+IpLZoyMeta2YEH/2ajNg90O3sZKbOvGmDIdCWMVwBvW3
# 67RKg+8mJhaPZc1AuxAEE3bvI5aFp9A62suTvQwpPM6+ukz9Khh5oIT9j+DMGfME
# KH8Z7YG2LMac1NThtubXfzNAfDmrgGqH2htuZCXDLbhP8Mn69BlQk30fCwu/NpSI
# +JfZmaXwJjxRMY76FFrcYSzeMJ1M1WPLuKyHEGl4L5rAAXtaQa0T7FpvYzkEzHZX
# /DDR8xlWpayOJvv3zsf/uQG8uo4N35anbkzizCEZ6NhpmS7C6Ts4
# SIG # End signature block
