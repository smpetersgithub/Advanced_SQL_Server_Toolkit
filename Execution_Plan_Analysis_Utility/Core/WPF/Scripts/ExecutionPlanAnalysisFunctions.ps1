# ExecutionPlanAnalysisFunctions.ps1

function Initialize-ExecutionPlanAnalysis {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow,

        [string]$ConfigPath = $null
    )

    Write-Host "[INFO] ExecutionPlanAnalysis init starting..."

    # ============================================================================
    # HARDCODED PATHS - Update these paths for your environment
    # ============================================================================

    $script:ProjectRoot = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility"
    $script:ConfigDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config"
    $script:OutputDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Output"
    $script:LogsDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Logs"
    $script:PythonDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\Python"

    # Set default config path if not provided
    if (-not $ConfigPath) {
        $ConfigPath = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Config\execution_plan_configurations.json"
    }

    # Store config path at script level for use in event handlers
    $script:ConfigPath = $ConfigPath

    Write-Host "[INFO] Project Root : $script:ProjectRoot"
    Write-Host "[INFO] Config Path  : $script:ConfigPath"
    Write-Host "[INFO] Output Dir   : $script:OutputDir"
    Write-Host "[INFO] Python Dir   : $script:PythonDir"

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
        $saveFileDialog.FileName = "execution_plan_configurations.json"
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

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try {
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
            $pythonExe = "python"
            $script1 = Join-Path $script:PythonDir "001_analyze_execution_plans.py"
            $script2 = Join-Path $script:PythonDir "002_export_to_excel.py"

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

            # Create a batch file to run both Python scripts sequentially
            $batchFile = [System.IO.Path]::GetTempFileName() + ".bat"
            $batchContent = @"
@echo off
cd /d "$($script:ProjectRoot)"
python "$script1"
if %ERRORLEVEL% EQU 0 (
    python "$script2"
)
"@
            [System.IO.File]::WriteAllText($batchFile, $batchContent)

            # Run the batch file in background (non-blocking)
            Write-Host "[INFO] Running analysis scripts via batch file: $batchFile"
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$batchFile`"" -WindowStyle Hidden

            Write-Host "[INFO] Analysis running in background."

        } catch {
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
            $pythonExe = "python"
            $script1 = Join-Path $script:PythonDir "003_analyze_single_plan.py"
            $script2 = Join-Path $script:PythonDir "004_export_single_plan_to_excel.py"

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

            # Create a batch file to run both Python scripts sequentially
            $batchFile = [System.IO.Path]::GetTempFileName() + ".bat"
            $batchContent = @"
@echo off
cd /d "$($script:ProjectRoot)"
python "$script1"
if %ERRORLEVEL% EQU 0 (
    python "$script2"
)
"@
            [System.IO.File]::WriteAllText($batchFile, $batchContent)

            # Run the batch file in background (non-blocking)
            Write-Host "[INFO] Running individual analysis scripts via batch file: $batchFile"
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$batchFile`"" -WindowStyle Hidden

            Write-Host "[INFO] Individual analysis running in background."

            # Start a timer to check for completion
            $timer = New-Object System.Windows.Threading.DispatcherTimer
            $timer.Interval = [TimeSpan]::FromSeconds(1)
            $script:checkCount = 0
            $script:maxChecks = 300  # 5 minutes timeout

            $timer.Add_Tick({
                param($sender, $e)
                $script:checkCount++

                $flagPath = Join-Path $script:OutputDir ".single_plan_complete"

                if (Test-Path $flagPath) {
                    # Stop the timer
                    $sender.Stop()

                    # Show completion message
                    [System.Windows.MessageBox]::Show(
                        "Individual Plan Analysis Complete!`n`nFiles are saved in the Output folder.",
                        "Export Complete",
                        [System.Windows.MessageBoxButton]::OK,
                        [System.Windows.MessageBoxImage]::Information
                    )

                    # Clean up the completion flag
                    Remove-Item $flagPath -Force -ErrorAction SilentlyContinue

                    Write-Host "[INFO] Individual plan analysis completed successfully"
                }
                elseif ($script:checkCount -ge $script:maxChecks) {
                    # Timeout - stop checking
                    $sender.Stop()
                    Write-Host "[WARN] Completion check timed out after $($script:maxChecks) seconds"
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

        # Set cursor to wait (hourglass)
        $MainWindow.Cursor = [System.Windows.Input.Cursors]::Wait

        try {
            # Check if the directory exists
            if (Test-Path $script:OutputDir) {
                Write-Host "[INFO] Opening folder: $script:OutputDir"
                Start-Process explorer.exe -ArgumentList $script:OutputDir
            } else {
                Write-Host "[WARN] Output directory does not exist: $script:OutputDir"
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

        # Confirm with user before deleting
        $result = [System.Windows.MessageBox]::Show(
            "This will delete all files in the Output and Logs folders.`n`nAre you sure you want to continue?",
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

                # Clean Output folder
                if (Test-Path $script:OutputDir) {
                    Write-Host "[INFO] Cleaning Output folder: $script:OutputDir"
                    Get-ChildItem -Path $script:OutputDir -File | ForEach-Object {
                        try {
                            Remove-Item $_.FullName -Force
                            $deletedCount++
                            Write-Host "[INFO] Deleted: $($_.Name)"
                        } catch {
                            $errorCount++
                            Write-Host "[ERROR] Failed to delete: $($_.Name) - $($_.Exception.Message)"
                        }
                    }
                }

                # Clean Logs folder
                if (Test-Path $script:LogsDir) {
                    Write-Host "[INFO] Cleaning Logs folder: $script:LogsDir"
                    Get-ChildItem -Path $script:LogsDir -File | ForEach-Object {
                        try {
                            Remove-Item $_.FullName -Force
                            $deletedCount++
                            Write-Host "[INFO] Deleted: $($_.Name)"
                        } catch {
                            $errorCount++
                            Write-Host "[ERROR] Failed to delete: $($_.Name) - $($_.Exception.Message)"
                        }
                    }
                }

                # Show completion message
                $message = "Cleanup complete!`n`nFiles deleted: $deletedCount"
                if ($errorCount -gt 0) {
                    $message += "`nErrors: $errorCount (some files may be in use)"
                }

                [System.Windows.MessageBox]::Show(
                    $message,
                    "Cleanup Complete",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )

                Write-Host "[INFO] Cleanup complete - Deleted: $deletedCount, Errors: $errorCount"

            } catch {
                Write-Host "[ERROR] Cleanup failed: $($_.Exception.Message)"
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
        }
    })

    # Add Click Event for Backup Configurations Button
    $btnBackupConfigurations.Add_Click({
        Write-Host "[INFO] Backup Configurations button clicked"

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
                    "No JSON configuration files found in:`n$configDir",
                    "No Files to Backup",
                    [System.Windows.MessageBoxButton]::OK,
                    [System.Windows.MessageBoxImage]::Information
                )
                return
            }

            # Create backup filename with timestamp
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupFileName = "Config_Backup_$timestamp.zip"
            $backupPath = Join-Path $configDir $backupFileName

            Write-Host "[INFO] Creating backup: $backupFileName"
            Write-Host "[INFO] Found $($jsonFiles.Count) JSON file(s) to backup"

            # Log each file being backed up
            foreach ($file in $jsonFiles) {
                Write-Host "[INFO] Adding to backup: $($file.Name)"
            }

            # Create zip file using PowerShell's Compress-Archive cmdlet
            Compress-Archive -Path $jsonFiles.FullName -DestinationPath $backupPath -Force

            Write-Host "[INFO] Backup created successfully: $backupPath"

            # Show success message
            [System.Windows.MessageBox]::Show(
                "Configuration backup created successfully!`n`nBackup file: $backupFileName`nLocation: $configDir`n`nFiles backed up: $($jsonFiles.Count)",
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

