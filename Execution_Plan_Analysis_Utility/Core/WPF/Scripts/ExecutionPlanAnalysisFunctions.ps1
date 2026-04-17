# ExecutionPlanAnalysisFunctions.ps1

# ============================================================================
# CONSTANTS
# ============================================================================
$script:COMPLETION_CHECK_INTERVAL_SECONDS = 1
$script:COMPLETION_CHECK_MAX_ATTEMPTS = 300  # 5 minutes (300 seconds / 1 second interval)
$script:PYTHON_EXECUTABLE = "python"
$script:DEFAULT_CONFIG_FILENAME = "execution-plan-config.json"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Initialize-Paths {
    <#
    .SYNOPSIS
    Initialize all paths relative to script location for portability.
    #>

    # Calculate paths relative to script location
    # Script is in: WPF/Scripts/
    # Project root is: ../../ from script
    $scriptPath = Split-Path -Parent $PSCommandPath
    $wpfPath = Split-Path -Parent $scriptPath
    $corePath = Split-Path -Parent $wpfPath
    $script:ProjectRoot = Split-Path -Parent $corePath

    # Set all paths relative to project root
    $script:ConfigDir = Join-Path $script:ProjectRoot "Config"
    $script:OutputDir = Join-Path $script:ProjectRoot "Output"
    $script:LogsDir = Join-Path $script:ProjectRoot "Core\Logs"
    $script:PythonDir = Join-Path $script:ProjectRoot "Core\Python"

    Write-Host "[INFO] Paths initialized (relative to script location):"
    Write-Host "[INFO]   Project Root : $script:ProjectRoot"
    Write-Host "[INFO]   Config Dir   : $script:ConfigDir"
    Write-Host "[INFO]   Output Dir   : $script:OutputDir"
    Write-Host "[INFO]   Logs Dir     : $script:LogsDir"
    Write-Host "[INFO]   Python Dir   : $script:PythonDir"

    # Validate critical paths exist
    $missingPaths = @()
    if (-not (Test-Path $script:ConfigDir)) { $missingPaths += "Config" }
    if (-not (Test-Path $script:PythonDir)) { $missingPaths += "Python" }

    if ($missingPaths.Count -gt 0) {
        Write-Host "[WARN] Missing directories: $($missingPaths -join ', ')"
    }
}

function Test-PythonInstallation {
    <#
    .SYNOPSIS
    Validate that Python is installed and accessible.
    #>

    try {
        $pythonVersion = & $script:PYTHON_EXECUTABLE --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Python found: $pythonVersion"
            return $true
        } else {
            Write-Host "[ERROR] Python command failed with exit code: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Host "[ERROR] Python not found in PATH: $($_.Exception.Message)"
        return $false
    }
}

function Test-Prerequisites {
    <#
    .SYNOPSIS
    Validate all prerequisites before running analysis.
    #>

    $issues = @()

    # Check Python installation
    if (-not (Test-PythonInstallation)) {
        $issues += "Python is not installed or not in PATH. Please install Python 3.x and add it to PATH."
    }

    # Check required Python scripts
    $requiredScripts = @(
        "01_analyze_execution_plans.py",
        "02_export_to_excel.py",
        "03_analyze_single_plan.py",
        "04_export_single_plan_to_excel.py"
    )

    foreach ($scriptName in $requiredScripts) {
        $scriptPath = Join-Path $script:PythonDir $scriptName
        if (-not (Test-Path $scriptPath)) {
            $issues += "Missing Python script: $scriptName"
        }
    }

    # Check config directory
    if (-not (Test-Path $script:ConfigDir)) {
        $issues += "Config directory not found: $script:ConfigDir"
    }

    return $issues
}

function Invoke-PythonScripts {
    <#
    .SYNOPSIS
    Execute Python scripts sequentially with proper error handling.
    #>
    param(
        [Parameter(Mandatory)]
        [string[]]$Scripts,

        [Parameter(Mandatory)]
        [string]$WorkingDirectory
    )

    Write-Host "[INFO] Executing $($Scripts.Count) Python script(s)..."

    # Validate all scripts exist first
    foreach ($script in $Scripts) {
        if (-not (Test-Path $script)) {
            throw "Python script not found: $script"
        }
    }

    # Execute scripts sequentially
    for ($i = 0; $i -lt $Scripts.Count; $i++) {
        $scriptPath = $Scripts[$i]
        $scriptName = Split-Path -Leaf $scriptPath

        Write-Host "[INFO] Running script $($i + 1)/$($Scripts.Count): $scriptName"

        $process = Start-Process -FilePath $script:PYTHON_EXECUTABLE `
            -ArgumentList "`"$scriptPath`"" `
            -WorkingDirectory $WorkingDirectory `
            -NoNewWindow `
            -PassThru `
            -Wait

        if ($process.ExitCode -ne 0) {
            throw "Script failed with exit code $($process.ExitCode): $scriptName"
        }

        Write-Host "[INFO] Script completed successfully: $scriptName"
    }

    Write-Host "[INFO] All scripts completed successfully"
}

# ============================================================================
# MAIN INITIALIZATION FUNCTION
# ============================================================================

function Initialize-ExecutionPlanAnalysis {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow,

        [string]$ConfigPath = $null
    )

    Write-Host "[INFO] ExecutionPlanAnalysis init starting..."

    # Initialize paths (relative to script location)
    Initialize-Paths

    # Set default config path if not provided
    if (-not $ConfigPath) {
        $ConfigPath = Join-Path $script:ConfigDir $script:DEFAULT_CONFIG_FILENAME
    }

    # Store config path at script level for use in event handlers
    $script:ConfigPath = $ConfigPath

    Write-Host "[INFO] Config Path  : $script:ConfigPath"

    # Validate prerequisites
    Write-Host "[INFO] Validating prerequisites..."
    $prerequisiteIssues = Test-Prerequisites

    if ($prerequisiteIssues.Count -gt 0) {
        $errorMessage = "Prerequisites check failed:`n`n" + ($prerequisiteIssues -join "`n")
        Write-Host "[ERROR] $errorMessage"
        [System.Windows.MessageBox]::Show(
            $errorMessage,
            "Prerequisites Missing",
            "OK",
            "Error"
        )
        # Continue anyway but warn user
    } else {
        Write-Host "[INFO] All prerequisites validated successfully"
    }

    # Find the DataGrid, Description TextBox, and Buttons
    $script:ExecutionPlanGridView = $MainWindow.FindName('ExecutionPlanGridView')
    $script:txtDescription = $MainWindow.FindName('txtDescription')
    $script:btnSaveDescription = $MainWindow.FindName('btnSaveDescription')
    $btnLoadSourceTarget = $MainWindow.FindName('btnLoadSourceTarget')
    $btnCheckForNewPlans = $MainWindow.FindName('btnCheckForNewPlans')
    $btnLoadConfiguration = $MainWindow.FindName('btnLoadConfiguration')
    $btnSaveExecutionPlanConfiguration = $MainWindow.FindName('btnSaveExecutionPlanConfiguration')
    $btnCompareExecutionPlans = $MainWindow.FindName('btnCompareExecutionPlans')
    $btnAnalyzeIndividualPlans = $MainWindow.FindName('btnAnalyzeIndividualPlans')
    $btnOpenOutputFolder = $MainWindow.FindName('btnOpenOutputFolder')
    $btnCleanup = $MainWindow.FindName('btnCleanup')
    $btnBackupConfigurations = $MainWindow.FindName('btnBackupConfigurations')

    # Configuration Tab Controls
    $script:cmbConfigFiles = $MainWindow.FindName('cmbConfigFiles')
    $script:txtConfigContent = $MainWindow.FindName('txtConfigContent')
    $script:txtConfigFilePath = $MainWindow.FindName('txtConfigFilePath')
    $script:btnRefreshConfig = $MainWindow.FindName('btnRefreshConfig')
    $script:btnCopyConfigPath = $MainWindow.FindName('btnCopyConfigPath')
    $script:btnSaveConfigFile = $MainWindow.FindName('btnSaveConfigFile')

    # Output Log Tab Controls
    $script:txtOutputLog = $MainWindow.FindName('txtOutputLog')
    $script:btnClearLog = $MainWindow.FindName('btnClearLog')
    $script:btnOpenLogsFolder = $MainWindow.FindName('btnOpenLogsFolder')

    if (-not $script:ExecutionPlanGridView -or -not $btnLoadSourceTarget) {
        # If they're within a tab usercontrol, try to find by header
        $tabControl = $MainWindow.FindName('TabControl')
        if ($tabControl) {
            $executionPlanTab = $tabControl.Items | Where-Object { $_.Header -eq 'Execution Plan Analysis' -or $_.Name -eq 'ExecutionPlanAnalysisTab' }
            if ($executionPlanTab) {
                if (-not $script:ExecutionPlanGridView) { $script:ExecutionPlanGridView = $executionPlanTab.FindName('ExecutionPlanGridView') }
                if (-not $btnLoadSourceTarget) { $btnLoadSourceTarget = $executionPlanTab.FindName('btnLoadSourceTarget') }
                if (-not $btnCheckForNewPlans) { $btnCheckForNewPlans = $executionPlanTab.FindName('btnCheckForNewPlans') }
                if (-not $btnLoadConfiguration) { $btnLoadConfiguration = $executionPlanTab.FindName('btnLoadConfiguration') }
                if (-not $btnSaveExecutionPlanConfiguration) { $btnSaveExecutionPlanConfiguration = $executionPlanTab.FindName('btnSaveExecutionPlanConfiguration') }
                if (-not $btnCompareExecutionPlans) { $btnCompareExecutionPlans = $executionPlanTab.FindName('btnCompareExecutionPlans') }
                if (-not $btnAnalyzeIndividualPlans) { $btnAnalyzeIndividualPlans = $executionPlanTab.FindName('btnAnalyzeIndividualPlans') }
                if (-not $btnOpenOutputFolder) { $btnOpenOutputFolder = $executionPlanTab.FindName('btnOpenOutputFolder') }
                if (-not $btnCleanup) { $btnCleanup = $executionPlanTab.FindName('btnCleanup') }
                if (-not $btnBackupConfigurations) { $btnBackupConfigurations = $executionPlanTab.FindName('btnBackupConfigurations') }
            }
        }
    }

    if (-not $script:ExecutionPlanGridView) {
        Write-Host "[WARN] Could not find 'ExecutionPlanGridView'."
        return
    }
    if (-not $btnLoadSourceTarget) {
        Write-Host "[WARN] Could not find 'btnLoadSourceTarget'."
        return
    }
    if (-not $script:txtDescription) {
        Write-Host "[WARN] Could not find 'txtDescription'."
        return
    }
    if (-not $script:btnSaveDescription) {
        Write-Host "[WARN] Could not find 'btnSaveDescription'."
        return
    }

    # Initialize the DataGrid with an empty collection
    $script:ExecutionPlansData = New-Object System.Collections.ObjectModel.ObservableCollection[Object]
    $script:ExecutionPlanGridView.ItemsSource = $script:ExecutionPlansData

    # Load existing data from JSON file if it exists
    if (Test-Path $script:ConfigPath) {
        Write-Host "[INFO] Loading existing configuration from: $script:ConfigPath"
        Load-ExecutionPlansFromJson -FilePath $script:ConfigPath -ClearExisting $false
    } else {
        Write-Host "[INFO] No existing configuration found at: $script:ConfigPath"
    }

    # Add CellEditEnding event to auto-save when user edits cells
    $script:ExecutionPlanGridView.Add_CellEditEnding({
        param($sender, $e)

        # Use a dispatcher to delay the save until after the edit is committed
        $sender.Dispatcher.InvokeAsync({
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration auto-saved after cell edit"
            } catch {
                Write-Host "[ERROR] Failed to auto-save configuration: $($_.Exception.Message)"
            }
        }, [System.Windows.Threading.DispatcherPriority]::Background)
    })

    # Add SelectionChanged event to update description text box
    $script:ExecutionPlanGridView.Add_SelectionChanged({
        param($sender, $e)

        $script:isUpdatingFromSelection = $true

        if ($sender.SelectedItem) {
            $selectedPlan = $sender.SelectedItem
            $script:txtDescription.Text = if ($selectedPlan.Description) { $selectedPlan.Description } else { "" }
            $script:txtDescription.IsEnabled = $true
            $script:btnSaveDescription.IsEnabled = $true
        } else {
            $script:txtDescription.Text = ""
            $script:txtDescription.IsEnabled = $false
            $script:btnSaveDescription.IsEnabled = $false
        }

        $script:isUpdatingFromSelection = $false
    })

    # Add LostFocus event to save description when user leaves the text box
    $script:isUpdatingFromSelection = $false

    $script:txtDescription.Add_LostFocus({
        # Prevent recursive updates
        if ($script:isUpdatingFromSelection) {
            return
        }

        if ($script:ExecutionPlanGridView.SelectedItem) {
            $selectedPlan = $script:ExecutionPlanGridView.SelectedItem

            # Update the Description property
            $selectedPlan.Description = $script:txtDescription.Text

            # Auto-save after description change
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration auto-saved after description edit (LostFocus)"
            } catch {
                Write-Host "[ERROR] Failed to auto-save configuration: $($_.Exception.Message)"
            }
        }
    })

    # Add KeyUp event to save on Ctrl+S
    $script:txtDescription.Add_KeyUp({
        param($sender, $e)

        # Check for Ctrl+S
        if ($e.Key -eq [System.Windows.Input.Key]::S -and
            [System.Windows.Input.Keyboard]::Modifiers -eq [System.Windows.Input.ModifierKeys]::Control) {

            if ($script:ExecutionPlanGridView.SelectedItem) {
                $selectedPlan = $script:ExecutionPlanGridView.SelectedItem
                $selectedPlan.Description = $script:txtDescription.Text

                try {
                    Save-ExecutionPlansToJson
                    Write-Host "[INFO] Configuration saved (Ctrl+S)"
                } catch {
                    Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"
                }
            }
        }
    })

    # Initially disable the description text box and save button
    $script:txtDescription.IsEnabled = $false
    $script:btnSaveDescription.IsEnabled = $false

    # Add Click Event for Save Description Button
    $script:btnSaveDescription.Add_Click({
        if ($script:ExecutionPlanGridView.SelectedItem) {
            $selectedPlan = $script:ExecutionPlanGridView.SelectedItem

            # Update the Description property
            $selectedPlan.Description = $script:txtDescription.Text

            # Auto-save after description change
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration saved successfully"

                [System.Windows.MessageBox]::Show(
                    "Description saved successfully!",
                    "Save Complete",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
            } catch {
                Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"

                [System.Windows.MessageBox]::Show(
                    "Failed to save description:`n$($_.Exception.Message)",
                    "Save Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            }
        } else {
            [System.Windows.MessageBox]::Show(
                "Please select a plan first.",
                "No Selection",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Warning
            )
        }
    })

    # Add Click Event for Load Configuration Button
    $btnLoadConfiguration.Add_Click({
        Write-Host "[INFO] Load Configuration button clicked"

        # Create OpenFileDialog
        Add-Type -AssemblyName System.Windows.Forms
        $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
        $openFileDialog.InitialDirectory = $script:ConfigDir
        $openFileDialog.Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*"
        $openFileDialog.Title = "Load Execution Plan Configuration"
        $openFileDialog.Multiselect = $false

        $dialogResult = $openFileDialog.ShowDialog()

        if ($dialogResult -eq [System.Windows.Forms.DialogResult]::OK) {
            $loadFilePath = $openFileDialog.FileName
            Write-Host "[INFO] Loading configuration from: $loadFilePath"

            # Use helper function to load JSON
            $loadSuccess = Load-ExecutionPlansFromJson -FilePath $loadFilePath -ClearExisting $true

            if ($loadSuccess) {
                [System.Windows.MessageBox]::Show(
                    "Successfully loaded $($script:ExecutionPlansData.Count) execution plan(s) from:`n$loadFilePath",
                    "Load Complete",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )

                # Auto-save to the default location after loading
                try {
                    Save-ExecutionPlansToJson
                    Write-Host "[INFO] Configuration auto-saved to default location"
                } catch {
                    Write-Host "[WARN] Failed to auto-save to default location: $($_.Exception.Message)"
                }
            } else {
                [System.Windows.MessageBox]::Show(
                    "Failed to load configuration from:`n$loadFilePath",
                    "Load Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            }
        } else {
            Write-Host "[INFO] Load operation cancelled by user"
        }
    })

    # Add Click Event for Load Execution Plans Button
    $btnLoadSourceTarget.Add_Click({
        Write-Host "[INFO] Load Execution Plans button clicked"
        Log-Output "Loading execution plans from folder..."

        # Create FolderBrowserDialog
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Select a directory containing .sqlplan files"
        $folderBrowser.ShowNewFolderButton = $false
        $folderBrowser.SelectedPath = "C:\"

        $result = $folderBrowser.ShowDialog()
        
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
            $selectedPath = $folderBrowser.SelectedPath
            Write-Host "[INFO] Selected directory: $selectedPath"
            
            # Find all .sqlplan files in the selected directory
            $sqlPlanFiles = Get-ChildItem -Path $selectedPath -Filter "*.sqlplan" -File | Sort-Object Name
            
            if ($sqlPlanFiles.Count -eq 0) {
                [System.Windows.MessageBox]::Show(
                    "No .sqlplan files found in the selected directory.",
                    "No Files Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
                Write-Host "[WARN] No .sqlplan files found in: $selectedPath"
                return
            }
            
            Write-Host "[INFO] Found $($sqlPlanFiles.Count) .sqlplan file(s)"
            
            # Clear existing data
            $script:ExecutionPlansData.Clear()
            
            # Generate Plan Names (Plan A, Plan B, Plan C, etc.)
            $planLetters = 65..90 | ForEach-Object { [char]$_ }  # A-Z
            $index = 0
            
            foreach ($file in $sqlPlanFiles) {
                if ($index -lt $planLetters.Count) {
                    $planName = "Plan $($planLetters[$index])"
                } else {
                    # If more than 26 files, use Plan AA, Plan AB, etc.
                    $planName = "Plan $($index + 1)"
                }
                
                # Create object with Add-Member to ensure properties are writable
                $planObject = New-Object PSObject
                $planObject | Add-Member -MemberType NoteProperty -Name 'ID' -Value ($index + 1)
                $planObject | Add-Member -MemberType NoteProperty -Name 'Name' -Value $planName
                $planObject | Add-Member -MemberType NoteProperty -Name 'File Name' -Value $file.Name
                $planObject | Add-Member -MemberType NoteProperty -Name 'Active' -Value $false
                $planObject | Add-Member -MemberType NoteProperty -Name 'Description' -Value $null
                $planObject | Add-Member -MemberType NoteProperty -Name 'FullPath' -Value $file.FullName

                $script:ExecutionPlansData.Add($planObject)
                Write-Host "[INFO] Added: $planName - $($file.Name)"
                
                $index++
            }
            
            Write-Host "[INFO] Successfully loaded $($script:ExecutionPlansData.Count) execution plan(s)"
            Log-Output "Successfully loaded $($script:ExecutionPlansData.Count) execution plan(s)"

            # Save to JSON file
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration saved to: $script:ConfigPath"
            } catch {
                Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"
            }

            [System.Windows.MessageBox]::Show(
                "Successfully loaded $($script:ExecutionPlansData.Count) execution plan(s).",
                "Load Complete",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )
        } else {
            Write-Host "[INFO] Folder selection cancelled"
        }
    })

    # Add Click Event for Check for New Plans Button
    $btnCheckForNewPlans.Add_Click({
        Write-Host "[INFO] Check for New Plans button clicked"

        # Check if there are any existing plans to determine the directory
        if ($script:ExecutionPlansData.Count -eq 0) {
            [System.Windows.MessageBox]::Show(
                "No execution plans loaded yet.`n`nPlease use 'Load Execution Plans' first to select a directory.",
                "No Plans Loaded",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )
            Write-Host "[WARN] No existing plans to check against"
            return
        }

        # Get the directory from the first plan's FullPath
        $firstPlan = $script:ExecutionPlansData | Select-Object -First 1
        $existingDirectory = Split-Path -Parent $firstPlan.FullPath
        Write-Host "[INFO] Checking directory: $existingDirectory"

        # Find all .sqlplan files in the directory
        if (-not (Test-Path $existingDirectory)) {
            [System.Windows.MessageBox]::Show(
                "The directory no longer exists:`n$existingDirectory`n`nPlease reload execution plans.",
                "Directory Not Found",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
            Write-Host "[ERROR] Directory not found: $existingDirectory"
            return
        }

        $sqlPlanFiles = Get-ChildItem -Path $existingDirectory -Filter "*.sqlplan" -File | Sort-Object Name

        if ($sqlPlanFiles.Count -eq 0) {
            [System.Windows.MessageBox]::Show(
                "No .sqlplan files found in the directory.",
                "No Files Found",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )
            Write-Host "[WARN] No .sqlplan files found in: $existingDirectory"
            return
        }

        Write-Host "[INFO] Found $($sqlPlanFiles.Count) .sqlplan file(s) in directory"

        # Get list of existing full paths and files in directory
        $existingPaths = $script:ExecutionPlansData | ForEach-Object { $_.FullPath }
        $directoryFilePaths = $sqlPlanFiles | ForEach-Object { $_.FullName }

        # Find files that need to be removed (exist in config but not in directory)
        $plansToRemove = $script:ExecutionPlansData | Where-Object { $directoryFilePaths -notcontains $_.FullPath }

        # Find new files not in the current configuration
        $newFiles = $sqlPlanFiles | Where-Object { $existingPaths -notcontains $_.FullName }

        # Track changes
        $removedCount = 0
        $addedCount = 0
        $changesMade = $false

        # Remove plans that no longer exist
        if ($plansToRemove.Count -gt 0) {
            Write-Host "[INFO] Found $($plansToRemove.Count) plan(s) to remove (files no longer exist)"

            foreach ($planToRemove in $plansToRemove) {
                Write-Host "[INFO] Removing plan: $($planToRemove.Name) - $($planToRemove.'File Name')"
                $script:ExecutionPlansData.Remove($planToRemove)
                $removedCount++
            }

            $changesMade = $true
        }

        # Check if there are new files to add
        if ($newFiles.Count -eq 0 -and $removedCount -eq 0) {
            [System.Windows.MessageBox]::Show(
                "No changes detected.`n`nAll .sqlplan files in the directory are already loaded and no files were removed.",
                "No Changes",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )
            Write-Host "[INFO] No changes - directory is in sync with configuration"
            return
        }

        if ($newFiles.Count -gt 0) {
            Write-Host "[INFO] Found $($newFiles.Count) new .sqlplan file(s) to add"
        }

        # Add new files if any
        if ($newFiles.Count -gt 0) {
            # Get the next ID
            $nextId = if ($script:ExecutionPlansData.Count -gt 0) {
                ($script:ExecutionPlansData | Measure-Object -Property ID -Maximum).Maximum + 1
            } else {
                1
            }

            # Generate Plan Names for new files
            $planLetters = 65..90 | ForEach-Object { [char]$_ }  # A-Z
            $currentCount = $script:ExecutionPlansData.Count

            foreach ($file in $newFiles) {
                $index = $currentCount + $addedCount

                if ($index -lt $planLetters.Count) {
                    $planName = "Plan $($planLetters[$index])"
                } else {
                    # If more than 26 files, use Plan 27, Plan 28, etc.
                    $planName = "Plan $($index + 1)"
                }

                # Create object with Add-Member to ensure properties are writable
                $planObject = New-Object PSObject
                $planObject | Add-Member -MemberType NoteProperty -Name 'ID' -Value $nextId
                $planObject | Add-Member -MemberType NoteProperty -Name 'Name' -Value $planName
                $planObject | Add-Member -MemberType NoteProperty -Name 'File Name' -Value $file.Name
                $planObject | Add-Member -MemberType NoteProperty -Name 'Active' -Value $false
                $planObject | Add-Member -MemberType NoteProperty -Name 'Description' -Value $null
                $planObject | Add-Member -MemberType NoteProperty -Name 'FullPath' -Value $file.FullName

                $script:ExecutionPlansData.Add($planObject)
                Write-Host "[INFO] Added new plan: $planName - $($file.Name)"

                $nextId++
                $addedCount++
            }

            Write-Host "[INFO] Successfully added $addedCount new execution plan(s)"
            $changesMade = $true
        }

        # Save to JSON file if changes were made
        if ($changesMade) {
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration saved with changes"
            } catch {
                Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"
            }
        }

        # Build summary message
        $summaryMessage = ""
        if ($removedCount -gt 0) {
            $summaryMessage += "Removed: $removedCount plan(s) (files no longer exist)`n"
        }
        if ($addedCount -gt 0) {
            $summaryMessage += "Added: $addedCount new plan(s)`n"
        }
        $summaryMessage += "`nTotal plans: $($script:ExecutionPlansData.Count)"

        [System.Windows.MessageBox]::Show(
            $summaryMessage,
            "Directory Reloaded",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Information
        )
    })

    # Add Click Event for Save Execution Plan Configuration Button
    $btnSaveExecutionPlanConfiguration.Add_Click({
        Write-Host "[INFO] Save Execution Plan Configuration button clicked"

        if ($script:ExecutionPlansData.Count -eq 0) {
            [System.Windows.MessageBox]::Show(
                "No execution plans to save. Please load execution plans first.",
                "Nothing to Save",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )
            return
        }

        # Create SaveFileDialog
        Add-Type -AssemblyName System.Windows.Forms
        $saveFileDialog = New-Object System.Windows.Forms.SaveFileDialog
        $saveFileDialog.InitialDirectory = $script:ConfigDir
        $saveFileDialog.FileName = $script:DEFAULT_CONFIG_FILENAME
        $saveFileDialog.Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*"
        $saveFileDialog.Title = "Save Execution Plan Configuration"
        $saveFileDialog.DefaultExt = "json"

        $dialogResult = $saveFileDialog.ShowDialog()

        if ($dialogResult -eq [System.Windows.Forms.DialogResult]::OK) {
            $saveFilePath = $saveFileDialog.FileName
            Write-Host "[INFO] Saving configuration to: $saveFilePath"

            # Use helper function to save JSON
            $saveSuccess = Save-ExecutionPlansToJson -FilePath $saveFilePath

            if ($saveSuccess) {
                [System.Windows.MessageBox]::Show(
                    "Configuration saved successfully to:`n$saveFilePath",
                    "Save Complete",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
            } else {
                [System.Windows.MessageBox]::Show(
                    "Failed to save configuration to:`n$saveFilePath",
                    "Save Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
            }
        } else {
            Write-Host "[INFO] Save operation cancelled by user"
        }
    })

    # Add Click Event for Compare Execution Plans Button
    $btnCompareExecutionPlans.Add_Click({
        Write-Host "[INFO] Compare Execution Plans button clicked"
        Log-Output "Starting execution plan comparison..."

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try{
            # Check if there are exactly 2 active plans
            $activePlans = @($script:ExecutionPlansData | Where-Object { $_.Active -eq $true })

            if ($activePlans.Count -lt 2) {
                [System.Windows.MessageBox]::Show(
                    "Please select exactly 2 active execution plans to compare.`n`nCurrent active plans: $($activePlans.Count)`n`nYou need to select 2 plans.",
                    "Insufficient Active Plans",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Warning
                )
                return
            }

            if ($activePlans.Count -gt 2) {
                [System.Windows.MessageBox]::Show(
                    "Please select exactly 2 active execution plans to compare.`n`nCurrent active plans: $($activePlans.Count)`n`nYou have too many plans selected. Please deselect $($activePlans.Count - 2) plan(s).",
                    "Too Many Active Plans",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Warning
                )
                return
            }

            Write-Host "[INFO] Found $($activePlans.Count) active plan(s) for comparison"

            # Save current configuration before running analysis
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration saved before analysis"
            } catch {
                Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "Failed to save configuration before analysis:`n$($_.Exception.Message)",
                    "Save Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            # Define Python script paths
            $script1 = Join-Path $script:PythonDir "01_analyze_execution_plans.py"
            $script2 = Join-Path $script:PythonDir "02_export_to_excel.py"

            # Check if Python scripts exist
            if (-not (Test-Path $script1)) {
                [System.Windows.MessageBox]::Show(
                    "Python script not found:`n$script1",
                    "Script Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            if (-not (Test-Path $script2)) {
                [System.Windows.MessageBox]::Show(
                    "Python script not found:`n$script2",
                    "Script Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            # Show progress message
            Write-Host "[INFO] Starting execution plan analysis..."

            # Run Python scripts directly (no batch file needed)
            try {
                Invoke-PythonScripts -Scripts @($script1, $script2) -WorkingDirectory $script:ProjectRoot
                Write-Host "[INFO] Analysis completed successfully"
                Log-Output "Execution plan comparison completed successfully!"
            } catch {
                throw "Analysis failed: $($_.Exception.Message)"
            }

        } catch {
            Log-Output "ERROR: Analysis failed - $($_.Exception.Message)"
            Write-Host "[ERROR] Failed to start Python scripts: $($_.Exception.Message)"
            [System.Windows.MessageBox]::Show(
                "Failed to start execution plan analysis:`n`n$($_.Exception.Message)",
                "Execution Error",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
        } finally {
            # Reset cursor to normal
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
        }
    })

    # Add Click Event for Analyze Individual Plans Button
    $btnAnalyzeIndividualPlans.Add_Click({
        Write-Host "[INFO] Analyze Individual Plans button clicked"
        Log-Output "Starting individual plan analysis..."

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try {
            # Check if there is at least 1 active plan
            $activePlans = @($script:ExecutionPlansData | Where-Object { $_.Active -eq $true })

            if ($activePlans.Count -lt 1) {
                [System.Windows.MessageBox]::Show(
                    "Please select at least 1 active execution plan to analyze.`n`nCurrent active plans: $($activePlans.Count)",
                    "No Active Plans",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Warning
                )
                return
            }

            Write-Host "[INFO] Found $($activePlans.Count) active plan(s) for individual analysis"

            # Save current configuration before running analysis
            try {
                Save-ExecutionPlansToJson
                Write-Host "[INFO] Configuration saved before analysis"
            } catch {
                Write-Host "[ERROR] Failed to save configuration: $($_.Exception.Message)"
                [System.Windows.MessageBox]::Show(
                    "Failed to save configuration before analysis:`n$($_.Exception.Message)",
                    "Save Error",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            # Define Python script paths
            $script1 = Join-Path $script:PythonDir "03_analyze_single_plan.py"
            $script2 = Join-Path $script:PythonDir "04_export_single_plan_to_excel.py"

            # Check if Python scripts exist
            if (-not (Test-Path $script1)) {
                [System.Windows.MessageBox]::Show(
                    "Python script not found:`n$script1",
                    "Script Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            if (-not (Test-Path $script2)) {
                [System.Windows.MessageBox]::Show(
                    "Python script not found:`n$script2",
                    "Script Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Error
                )
                return
            }

            # Show progress message
            Write-Host "[INFO] Starting individual plan analysis..."

            # Delete any existing completion flag
            $completionFlag = Join-Path $script:OutputDir ".single_plan_complete"
            if (Test-Path $completionFlag) {
                Remove-Item $completionFlag -Force
            }

            # Run Python scripts directly (no batch file needed)
            Write-Host "[INFO] Running individual analysis scripts..."

            # Run scripts in background using Start-Job for non-blocking execution
            $job = Start-Job -ScriptBlock {
                param($PythonExe, $Script1, $Script2, $WorkingDir)

                Set-Location $WorkingDir

                # Run first script
                & $PythonExe $Script1
                $exitCode1 = $LASTEXITCODE

                if ($exitCode1 -eq 0) {
                    # Run second script if first succeeded
                    & $PythonExe $Script2
                    return $LASTEXITCODE
                }

                return $exitCode1
            } -ArgumentList $script:PYTHON_EXECUTABLE, $script1, $script2, $script:ProjectRoot

            Write-Host "[INFO] Individual analysis running in background (Job ID: $($job.Id))"
            Write-Host "[INFO] Waiting for job to complete..."

            # Start a timer to check for completion
            $timer = New-Object System.Windows.Threading.DispatcherTimer
            $timer.Interval = [TimeSpan]::FromSeconds($script:COMPLETION_CHECK_INTERVAL_SECONDS)
            $script:checkCount = 0
            $script:analysisJob = $job

            $timer.Add_Tick({
                param($sender, $e)
                $script:checkCount++

                # Check if job is complete
                $jobState = $script:analysisJob.State
                Write-Host "[DEBUG] Timer tick $($script:checkCount): Job state = $jobState"

                if ($jobState -eq 'Completed') {
                    # Stop the timer
                    $sender.Stop()

                    # Get job result
                    $exitCode = Receive-Job -Job $script:analysisJob
                    Remove-Job -Job $script:analysisJob -Force

                    if ($exitCode -eq 0) {
                        # Show completion message
                        [System.Windows.MessageBox]::Show(
                            "Individual Plan Analysis Complete!`n`nFiles are saved in the Output folder.",
                            "Export Complete",
                            [System.Windows.MessageBoxButton]::OK,
                            [System.Windows.MessageBoxImage]::Information
                        )
                        Write-Host "[INFO] Individual plan analysis completed successfully"
                        Log-Output "Individual plan analysis completed successfully!"
                    } else {
                        Log-Output "WARNING: Individual plan analysis completed with exit code: $exitCode"
                        [System.Windows.MessageBox]::Show(
                            "Individual Plan Analysis completed with errors.`n`nExit Code: $exitCode`n`nCheck the log files for details.",
                            "Analysis Warning",
                            [System.Windows.MessageBoxButton]::OK,
                            [System.Windows.MessageBoxImage]::Warning
                        )
                        Write-Host "[WARN] Individual plan analysis completed with exit code: $exitCode"
                    }
                }
                elseif ($jobState -eq 'Failed') {
                    # Stop the timer
                    $sender.Stop()

                    # Get error details
                    $jobError = $script:analysisJob.ChildJobs[0].Error
                    Remove-Job -Job $script:analysisJob -Force

                    [System.Windows.MessageBox]::Show(
                        "Individual Plan Analysis failed.`n`nError: $jobError",
                        "Analysis Failed",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Error
                    )
                    Write-Host "[ERROR] Individual plan analysis failed: $jobError"
                }
                elseif ($script:checkCount -ge $script:COMPLETION_CHECK_MAX_ATTEMPTS) {
                    # Timeout - stop checking
                    $sender.Stop()
                    Remove-Job -Job $script:analysisJob -Force -ErrorAction SilentlyContinue
                    Write-Host "[WARN] Completion check timed out after $($script:COMPLETION_CHECK_MAX_ATTEMPTS) seconds"

                    [System.Windows.MessageBox]::Show(
                        "Analysis is taking longer than expected.`n`nThe process may still be running in the background.`n`nCheck the Output folder and log files.",
                        "Timeout",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Warning
                    )
                }
            })

            $timer.Start()

        } catch {
            Write-Host "[ERROR] Failed to start Python scripts: $($_.Exception.Message)"
            [System.Windows.MessageBox]::Show(
                "Failed to start individual plan analysis:`n`n$($_.Exception.Message)",
                "Execution Error",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
        } finally {
            # Reset cursor to normal
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
        }
    })

    # Add Click Event for Open Output Folder Button
    $btnOpenOutputFolder.Add_Click({
        Write-Host "[INFO] Open Output Folder button clicked"
        Log-Output "Opening output folder..."

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try {
            # Check if the directory exists
            if (Test-Path $script:OutputDir) {
                Write-Host "[INFO] Opening folder: $script:OutputDir"
                Log-Output "Opened directory: $script:OutputDir"
                Start-Process explorer.exe -ArgumentList $script:OutputDir
            } else {
                Write-Host "[WARN] Output directory does not exist: $script:OutputDir"
                Log-Output "WARNING: Output directory does not exist"
                [System.Windows.MessageBox]::Show(
                    "The output folder does not exist yet:`n$($script:OutputDir)`n`nRun 'Compare Execution Plans' first to generate results.",
                    "Folder Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
            }
        } finally {
            # Reset cursor to normal
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
        }
    })

    # Add Click Event for Cleanup Button
    $btnCleanup.Add_Click({
        Write-Host "[INFO] Cleanup button clicked"
        Log-Output "Cleanup operation started"

        # Load cleanup configuration from cleanup-config.json
        $cleanupConfigPath = Join-Path $script:ConfigDir "cleanup-config.json"

        if (-not (Test-Path $cleanupConfigPath)) {
            Write-Host "[ERROR] Cleanup configuration file not found: $cleanupConfigPath"
            [System.Windows.MessageBox]::Show(
                "Cleanup configuration file not found:`n$cleanupConfigPath",
                "Configuration Not Found",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
            return
        }

        try {
            $cleanupConfig = Get-Content $cleanupConfigPath -Raw | ConvertFrom-Json
        } catch {
            Write-Host "[ERROR] Failed to read cleanup configuration: $($_.Exception.Message)"
            [System.Windows.MessageBox]::Show(
                "Failed to read cleanup configuration:`n`n$($_.Exception.Message)",
                "Configuration Error",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
            return
        }

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

        # Confirm with user before deleting
        $result = [System.Windows.MessageBox]::Show(
            $confirmMessage,
            "Confirm Cleanup",
            [System.Windows.MessageBoxButton]::YesNo,
            [System.Windows.MessageBoxImage]::Warning
        )

        if ($result -eq [System.Windows.MessageBoxResult]::Yes) {
            # Set cursor to wait (hourglass)
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

            try {
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
        } else {
            Write-Host "[INFO] Cleanup cancelled by user"
            Log-Output "Cleanup cancelled by user"
        }
    })

    # Add Click Event for Backup Configurations Button
    $btnBackupConfigurations.Add_Click({
        Write-Host "[INFO] Backup Configurations button clicked"
        Log-Output "Backing up configurations..."

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try {
            # Check if Config directory exists
            if (-not (Test-Path $script:ConfigDir)) {
                Write-Host "[WARN] Config directory does not exist: $script:ConfigDir"
                [System.Windows.MessageBox]::Show(
                    "The Config folder does not exist:`n$($script:ConfigDir)",
                    "Folder Not Found",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Warning
                )
                return
            }

            # Get all JSON files in Config folder
            $jsonFiles = Get-ChildItem -Path $script:ConfigDir -Filter "*.json" -File

            if ($jsonFiles.Count -eq 0) {
                Write-Host "[WARN] No JSON files found in Config folder"
                [System.Windows.MessageBox]::Show(
                    "No JSON configuration files found in:`n$($script:ConfigDir)",
                    "No Files to Backup",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
                return
            }

            # Create Backup directory if it doesn't exist
            $backupDir = Join-Path $script:ConfigDir "Backup"
            if (-not (Test-Path $backupDir)) {
                New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
                Write-Host "[INFO] Created Backup directory: $backupDir"
            }

            # Create backup filename with timestamp
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupFileName = "Config_Backup_$timestamp.zip"
            $backupPath = Join-Path $backupDir $backupFileName

            Write-Host "[INFO] Creating backup: $backupFileName"
            Write-Host "[INFO] Backup location: $backupDir"
            Write-Host "[INFO] Found $($jsonFiles.Count) JSON file(s) to backup"

            # Log each file being backed up
            foreach ($file in $jsonFiles) {
                Write-Host "[INFO] Adding to backup: $($file.Name)"
            }

            # Create zip file using PowerShell's Compress-Archive cmdlet
            # Suppress all output to prevent console window flash
            Compress-Archive -Path $jsonFiles.FullName -DestinationPath $backupPath -Force -ErrorAction Stop | Out-Null

            Write-Host "[INFO] Backup created successfully: $backupPath"

            # Show success message
            [System.Windows.MessageBox]::Show(
                "Configuration backup created successfully!`n`nBackup file: $backupFileName`nLocation: $backupDir`n`nFiles backed up: $($jsonFiles.Count)",
                "Backup Complete",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Information
            )

        } catch {
            Write-Host "[ERROR] Backup failed: $($_.Exception.Message)"
            [System.Windows.MessageBox]::Show(
                "An error occurred during backup:`n`n$($_.Exception.Message)",
                "Backup Error",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
        } finally {
            # Reset cursor to normal
            $MainWindow.Cursor = [System.Windows.Input.Cursors]::Arrow
        }
    })

    # Add Click Event for GitHub Button
    $btnGitHub = $MainWindow.FindName("btnGitHub")
    $btnGitHub.Add_Click({
        Write-Host "[INFO] GitHub button clicked"

        try {
            # Open GitHub repository in default browser
            Start-Process "https://github.com/smpetersgithub/Advanced_SQL_Server_Toolkit"
            Write-Host "[INFO] Opened GitHub repository in browser"
        } catch {
            Write-Host "[ERROR] Failed to open GitHub URL: $($_.Exception.Message)"
            [System.Windows.MessageBox]::Show(
                "Failed to open GitHub repository.`n`nURL: https://github.com/smpetersgithub/Advanced_SQL_Server_Toolkit",
                "Error",
                [System.Windows.MessageBoxButton]::OK,
                [System.Windows.MessageBoxImage]::Error
            )
        }
    })

    # Configuration Tab Event Handlers
    if ($script:cmbConfigFiles -and $script:btnSaveConfigFile -and $script:btnCopyConfigPath) {
        # Load configuration files into combo box
        Load-ConfigurationFiles

        # Add event handler for config file selection
        $script:cmbConfigFiles.Add_SelectionChanged({ On-ConfigFileSelected })

        # Add event handler for Refresh Config button
        $script:btnRefreshConfig.Add_Click({ Refresh-ConfigurationFile })

        # Add event handler for Save Config button
        $script:btnSaveConfigFile.Add_Click({ Save-ConfigurationFile })

        # Add event handler for Copy Path button
        $script:btnCopyConfigPath.Add_Click({ Copy-ConfigurationPath })

        Write-Host "[INFO] Configuration tab initialized"
    } else {
        Write-Host "[WARN] Configuration tab controls not found - tab may not be available"
    }

    # Output Log Tab Event Handlers
    if ($script:btnClearLog) {
        $script:btnClearLog.Add_Click({
            Clear-OutputLog
        })
    }

    if ($script:btnOpenLogsFolder) {
        $script:btnOpenLogsFolder.Add_Click({
            Open-LogsFolder
        })
    }

    # Log initialization complete
    Log-Output "Execution Plan Analysis Utility initialized successfully"

    Write-Host "[INFO] ExecutionPlanAnalysis init complete."
}

# Helper function to save execution plans to JSON
function Save-ExecutionPlansToJson {
    param(
        [Parameter(Mandatory = $false)]
        [string]$FilePath = $script:ConfigPath
    )

    try {
        # Ensure the directory exists
        $configDir = Split-Path -Parent $FilePath
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
            Write-Host "[INFO] Created directory: $configDir"
        }

        # Convert ObservableCollection to array for JSON serialization
        $dataToSave = @()
        foreach ($item in $script:ExecutionPlansData) {
            $dataToSave += [PSCustomObject]@{
                'ID' = $item.ID
                'Name' = $item.Name
                'File Name' = $item.'File Name'
                'Active' = $item.Active
                'Description' = $item.Description
                'FullPath' = $item.FullPath
            }
        }

        # Save to JSON file with pretty formatting (UTF-8 without BOM)
        $jsonContent = $dataToSave | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($FilePath, $jsonContent, [System.Text.Encoding]::UTF8)
        Write-Host "[INFO] Saved $($dataToSave.Count) execution plan(s) to: $FilePath"
        return $true
    } catch {
        Write-Host "[ERROR] Failed to save configuration to ${FilePath}: $($_.Exception.Message)"
        return $false
    }
}

# Helper function to load execution plans from JSON
function Load-ExecutionPlansFromJson {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [bool]$ClearExisting = $false
    )

    try {
        # Read and parse the JSON file
        $jsonData = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8 | ConvertFrom-Json

        # Clear existing data if requested
        if ($ClearExisting) {
            $script:ExecutionPlansData.Clear()
        }

        # Load the data into the collection
        foreach ($item in $jsonData) {
            # Create object with Add-Member to ensure properties are writable
            $planObject = New-Object PSObject
            $planObject | Add-Member -MemberType NoteProperty -Name 'ID' -Value $item.ID
            $planObject | Add-Member -MemberType NoteProperty -Name 'Name' -Value $item.Name
            $planObject | Add-Member -MemberType NoteProperty -Name 'File Name' -Value $item.'File Name'
            $planObject | Add-Member -MemberType NoteProperty -Name 'Active' -Value $item.Active
            $planObject | Add-Member -MemberType NoteProperty -Name 'Description' -Value $item.Description
            $planObject | Add-Member -MemberType NoteProperty -Name 'FullPath' -Value $item.FullPath
            $script:ExecutionPlansData.Add($planObject)
        }

        Write-Host "[INFO] Loaded $($jsonData.Count) execution plan(s) from: $FilePath"
        return $true
    } catch {
        Write-Host "[ERROR] Failed to load configuration from ${FilePath}: $($_.Exception.Message)"
        return $false
    }
}

# ============================================================================
# CONFIGURATION TAB FUNCTIONS
# ============================================================================

function Load-ConfigurationFiles {
    Write-Host "[INFO] Loading configuration files..."

    try {
        # Get all JSON files in the Config directory
        $configFiles = Get-ChildItem -Path $script:ConfigDir -Filter "*.json" | Sort-Object Name

        # Clear and populate the combo box
        $script:cmbConfigFiles.Items.Clear()

        foreach ($file in $configFiles) {
            $script:cmbConfigFiles.Items.Add($file.Name) | Out-Null
        }

        Write-Host "[INFO] Loaded $($configFiles.Count) configuration file(s)"

        # Select the first file by default
        if ($script:cmbConfigFiles.Items.Count -gt 0) {
            $script:cmbConfigFiles.SelectedIndex = 0
            # Manually trigger the selection changed event to load the content
            On-ConfigFileSelected
        }

    } catch {
        Write-Host "[ERROR] Failed to load configuration files: $($_.Exception.Message)"
    }
}

function On-ConfigFileSelected {
    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        $script:txtConfigFilePath.Text = ""
        return
    }

    Write-Host "[INFO] Loading config file: $selectedFile"
    Log-Output "Loading config file: $selectedFile"

    try {
        $filePath = Join-Path $script:ConfigDir $selectedFile
        $script:txtConfigFilePath.Text = $filePath

        # Read and display the file content
        $content = Get-Content $filePath -Raw -Encoding UTF8
        $script:txtConfigContent.Text = $content

        Write-Host "[INFO] Loaded config file: $filePath"
        Log-Output "Config file loaded successfully"

    } catch {
        Write-Host "[ERROR] Failed to load config file: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to load config file - $($_.Exception.Message)"
        $script:txtConfigContent.Text = "Error loading file: $($_.Exception.Message)"
    }
}

function Save-ConfigurationFile {
    $selectedFile = $script:cmbConfigFiles.SelectedItem

    if ([string]::IsNullOrWhiteSpace($selectedFile)) {
        [System.Windows.MessageBox]::Show("No configuration file selected", "Info", "OK", "Information")
        return
    }

    Write-Host "[INFO] Saving config file: $selectedFile"
    Log-Output "Saving config file: $selectedFile"

    try {
        $filePath = Join-Path $script:ConfigDir $selectedFile

        # Validate JSON before saving
        try {
            $script:txtConfigContent.Text | ConvertFrom-Json | Out-Null
        } catch {
            [System.Windows.MessageBox]::Show(
                "Invalid JSON format. Please correct the syntax before saving.`n`nError: $($_.Exception.Message)",
                "JSON Validation Error",
                "OK",
                "Error"
            )
            Write-Host "[ERROR] JSON validation failed: $($_.Exception.Message)"
            return
        }

        # Save the content
        [System.IO.File]::WriteAllText($filePath, $script:txtConfigContent.Text, [System.Text.Encoding]::UTF8)

        [System.Windows.MessageBox]::Show(
            "Configuration file saved successfully!`n`nFile: $selectedFile",
            "Save Complete",
            "OK",
            "Information"
        )

        Write-Host "[INFO] Config file saved: $filePath"
        Log-Output "Config file saved successfully"

    } catch {
        Write-Host "[ERROR] Failed to save config file: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to save config file - $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to save configuration file.`n`nError: $($_.Exception.Message)",
            "Save Error",
            "OK",
            "Error"
        )
    }
}

function Refresh-ConfigurationFile {
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

function Copy-ConfigurationPath {
    Write-Host "[INFO] Copying config file path to clipboard..."

    try {
        $path = $script:txtConfigFilePath.Text

        if ([string]::IsNullOrWhiteSpace($path)) {
            [System.Windows.MessageBox]::Show("No file path available", "Info", "OK", "Information")
            return
        }

        Set-Clipboard -Value $path
        Write-Host "[INFO] Copied to clipboard: $path"

        [System.Windows.MessageBox]::Show(
            "File path copied to clipboard!`n`n$path",
            "Copy Complete",
            "OK",
            "Information"
        )

    } catch {
        Write-Host "[ERROR] Failed to copy path: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to copy path to clipboard.`n`nError: $($_.Exception.Message)",
            "Copy Error",
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
    Reads the logs_dir path from config.json and opens it in Windows Explorer.
    Creates the folder if it doesn't exist.
    #>

    Write-Host "[INFO] Opening Logs folder..."
    Log-Output "Opening Logs folder..."

    try {
        # Read config.json to get the logs_dir path
        $logsDir = $null

        if (Test-Path $script:ConfigPath) {
            $configJson = Get-Content -Path $script:ConfigPath -Raw | ConvertFrom-Json

            if ($configJson.paths.logs_dir) {
                # Construct full path
                $logsDir = Join-Path $script:ProjectRoot $configJson.paths.logs_dir
                Write-Host "[INFO] Logs directory from config: $logsDir"
            } else {
                Write-Host "[WARN] logs_dir not found in config.json, using default"
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
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUCQeDekmyW7od09kh6nl4Xxzi
# xSOgghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
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
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBRlrL0v97z6Ri8K
# O4WhmKIBQ/VOhzANBgkqhkiG9w0BAQEFAASCAQBYY7Zhks7PbfM2IBLlcZIVMje+
# Z0ilBrNAzLgrsesB/bRlcXgBoqDbGEvtAiuKFYV8NuUOVIyUEyN2e9PILIv2mSaC
# zzSixFlO8s0lRrso5eV1YgzKFx+uDz7P1sk+2BCPxWxOV9vghKGC/XlMkVeevp6H
# yvbDwNmka2v7Ecd0KAw9ZZJ59sUQpoSsXYfEKbImgua2SguLv9AuN4W1+VfGShrO
# 7c5gutZBfz64c9JVqm9jubjVPHS/UOxQR9O5XASZXLVa3kAcxq8C8wkv+o+GeBzy
# tyOJJXrlsNGogeDSyGq2USGZ/a7Yo1ZqSm407Fa5RM9db5GXi++o3PN/i5QmoYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMTAzNlowLwYJKoZIhvcNAQkE
# MSIEIAW20DxLmc51bt4nfxyRBRL13Ne/0/0rzN8WdQyDvOnMMA0GCSqGSIb3DQEB
# AQUABIICALHvsSf7/L7Z0rVyqmo0+ikWBZGkWEAk6ALxhpq1IXDAyHHsYkny7fQw
# 4P8X2AvC/ecBGKzwu8/Z9YinTzcegG+quz0Bc+aVLzf2cmI+9Mdu5nx0tiIH4yG8
# vAhqVUNSG4QUrqELfrC5elnBHeUu+qxUI6bTDFSH11ATIKyxHeCN2Zy8H0GQjkIF
# uQHR/Ts6NHHwlGnHChsp8b0CZFD5+6cPK/Xjy5/uNUf0XH7V9JpMz9vzGEfsEAQB
# iT7MPAuSLTNxJPIDjtiVkIb1e6eSWsVNMcytlpbPmRriVwkSncq+3qAQSoMtLIQK
# QiXSGaFu9bUIkRFItvElAZlPxcbokbCtAd9hUrK1VflX21AdXzWdX4JKqfToZZk+
# A+aDk67a/MUDrlKABWWar0nF4gdq54fNhyO8+88Pj/iu/ivktFN4ywkRPz0mVfIu
# WFEhEylfu9AIWXVitPvxDuHVWrJq0+aIYdeQXe0+j81tIrdyIAOA/TGpRihD6oM0
# hLkBgYBpMjgk8zecaDvtqX7hUxsNYFivopGSdR2AV6ZlOkysjMDI1R+EZBbfzgma
# gQ2LFN671q4VYYcF5EE8FPLrcGj0C5C+G96mvoJu5DfBHN8JI19LCGHhV5qiUbhQ
# nxK2LvYUgrW1KRyn7nwvN5rcHNqHt4xrJjG+eIfFI59/6KYlZkAK
# SIG # End signature block
