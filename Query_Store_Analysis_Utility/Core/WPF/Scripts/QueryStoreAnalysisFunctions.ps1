# QueryStoreAnalysisFunctions.ps1

function Initialize-QueryStoreAnalysis {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow,

        [Parameter(Mandatory)]
        [string]$ProjectRoot
    )

    Write-Host "[INFO] QueryStoreAnalysis init starting..."

    # ============================================================================
    # STORE PROJECT PATHS AT SCRIPT LEVEL
    # ============================================================================
    $script:ProjectRoot = $ProjectRoot
    $script:ConfigDir = Join-Path $ProjectRoot "Config"
    $script:OutputDir = Join-Path $ProjectRoot "Output"
    $script:LogsDir = Join-Path $ProjectRoot "Core\Logs"
    $script:PythonDir = Join-Path $ProjectRoot "Core\Python"
    $script:ReportsConfigPath = Join-Path $script:ConfigDir "reports-config.json"
    $script:DatabaseConfigPath = Join-Path $script:ConfigDir "database-config.json"
    $script:SelectedReportKey = $null
    $script:ReportsConfig = $null

    Write-Host "[INFO] Config Dir   : $script:ConfigDir"
    Write-Host "[INFO] Output Dir   : $script:OutputDir"
    Write-Host "[INFO] Python Dir   : $script:PythonDir"
    Write-Host "[INFO] DB Config    : $script:DatabaseConfigPath"

    # ============================================================================
    # FIND UI CONTROLS
    # ============================================================================
    Write-Host "[DEBUG] Finding UI controls..."

    # Connection Tab Controls
    $script:txtServer = $MainWindow.FindName('txtServer')
    $script:txtDatabase = $MainWindow.FindName('txtDatabase')
    $script:txtUsername = $MainWindow.FindName('txtUsername')
    $script:txtPassword = $MainWindow.FindName('txtPassword')
    $script:btnTestConnection = $MainWindow.FindName('btnTestConnection')
    $script:btnSaveConfig = $MainWindow.FindName('btnSaveConfig')
    $script:txtConnectionStatus = $MainWindow.FindName('txtConnectionStatus')

    # QueryID Tab Controls
    $script:txtQueryID = $MainWindow.FindName('txtQueryID')
    $script:btnExecuteQueryLookup = $MainWindow.FindName('btnExecuteQueryLookup')
    $script:txtStoredProcedure = $MainWindow.FindName('txtStoredProcedure')
    $script:btnOpenObject = $MainWindow.FindName('btnOpenObject')
    $script:txtQueryText = $MainWindow.FindName('txtQueryText')
    $script:btnCopySQL = $MainWindow.FindName('btnCopySQL')
    $script:txtGitHubProcsPath = $MainWindow.FindName('txtGitHubProcsPath')
    $script:txtGitHubFunctionsPath = $MainWindow.FindName('txtGitHubFunctionsPath')

    # Reports Tab Controls
    $script:ReportsGrid = $MainWindow.FindName('ReportsGrid')
    $script:btnExecuteReport = $MainWindow.FindName('btnExecuteReport')
    $script:txtSelectedReport = $MainWindow.FindName('txtSelectedReport')
    $script:txtTopN = $MainWindow.FindName('txtTopN')
    $script:chkIncludePlans = $MainWindow.FindName('chkIncludePlans')
    $script:pnlProgress = $MainWindow.FindName('pnlProgress')
    $script:progressBar = $MainWindow.FindName('progressBar')
    $script:txtProgressStatus = $MainWindow.FindName('txtProgressStatus')
    $script:chkAnalyzeIndexes = $MainWindow.FindName('chkAnalyzeIndexes')
    $script:txtReportOutputDir = $MainWindow.FindName('txtReportOutputDir')
    $script:linkReportOutputDir = $MainWindow.FindName('linkReportOutputDir')
    $script:btnSaveReportConfig = $MainWindow.FindName('btnSaveReportConfig')

    # Results Tab Controls
    $script:txtResultsReportName = $MainWindow.FindName('txtResultsReportName')
    $script:btnExportToExcel = $MainWindow.FindName('btnExportToExcel')
    $script:btnRefreshResults = $MainWindow.FindName('btnRefreshResults')
    $script:ResultsGrid = $MainWindow.FindName('ResultsGrid')

    # AI Prompts Tab Controls
    $script:cmbAIPrompts = $MainWindow.FindName('cmbAIPrompts')
    $script:txtPromptContent = $MainWindow.FindName('txtPromptContent')
    $script:txtPromptsDirectoryPath = $MainWindow.FindName('txtPromptsDirectoryPath')
    $script:btnCopyPromptsPath = $MainWindow.FindName('btnCopyPromptsPath')

    # Config Tab Controls
    $script:cmbConfigFiles = $MainWindow.FindName('cmbConfigFiles')
    $script:txtConfigContent = $MainWindow.FindName('txtConfigContent')
    $script:txtConfigFilePath = $MainWindow.FindName('txtConfigFilePath')
    $script:btnRefreshConfig = $MainWindow.FindName('btnRefreshConfig')
    $script:btnSaveConfigFile = $MainWindow.FindName('btnSaveConfigFile')
    $script:btnCopyConfigPath = $MainWindow.FindName('btnCopyConfigPath')

    # Output Log Tab Controls
    $script:txtOutputLog = $MainWindow.FindName('txtOutputLog')
    $script:btnClearLog = $MainWindow.FindName('btnClearLog')
    $script:btnOpenLogsFolder = $MainWindow.FindName('btnOpenLogsFolder')

    # Toolbar Buttons
    $script:btnOpenOutputFolder = $MainWindow.FindName('btnOpenOutputFolder')
    $script:btnDeleteOutput = $MainWindow.FindName('btnDeleteOutput')

    # Status Bar
    $script:txtStatus = $MainWindow.FindName('txtStatus')
    $script:txtVersion = $MainWindow.FindName('txtVersion')

    # Tab Control
    $script:MainTabControl = $MainWindow.FindName('MainTabControl')

    # ============================================================================
    # LOAD CONFIGURATIONS
    # ============================================================================
    Load-DatabaseConfiguration
    Load-ReportsConfiguration
    Load-AIPrompts
    Load-PythonConfig
    Load-GitHubPaths

    # ============================================================================
    # ATTACH EVENT HANDLERS
    # ============================================================================
    Write-Host "[INFO] Attaching event handlers..."

    # Connection Tab
    $script:btnTestConnection.Add_Click({ Test-DatabaseConnection })
    $script:btnSaveConfig.Add_Click({ Save-DatabaseConfiguration })

    # QueryID Tab
    $script:btnExecuteQueryLookup.Add_Click({ Get-QueryByID })
    $script:btnOpenObject.Add_Click({ Open-ObjectFile })
    $script:btnCopySQL.Add_Click({ Copy-QuerySQL })

    # Reports Tab
    $script:ReportsGrid.Add_SelectionChanged({ On-ReportSelected })
    $script:btnExecuteReport.Add_Click({ Execute-Report })
    $script:btnSaveReportConfig.Add_Click({ Save-ReportConfiguration -ShowSuccessMessage $true })

    # Results Tab
    $script:btnExportToExcel.Add_Click({ Export-ResultsToExcel })
    $script:btnRefreshResults.Add_Click({ Refresh-Results })

    # AI Prompts Tab
    $script:cmbAIPrompts.Add_SelectionChanged({ On-PromptSelected })
    $script:btnCopyPromptsPath.Add_Click({ Copy-PromptsPath })

    # Config Tab
    $script:cmbConfigFiles.Add_SelectionChanged({ On-ConfigFileSelected })
    $script:btnRefreshConfig.Add_Click({ Refresh-ConfigFile })
    $script:btnSaveConfigFile.Add_Click({ Save-ConfigFile })
    $script:btnCopyConfigPath.Add_Click({ Copy-ConfigPath })

    # Output Log Tab
    if ($script:btnClearLog) {
        $script:btnClearLog.Add_Click({ Clear-OutputLog })
    }

    if ($script:btnOpenLogsFolder) {
        $script:btnOpenLogsFolder.Add_Click({ Open-LogsFolder })
    }

    # Toolbar
    $script:btnOpenOutputFolder.Add_Click({ Open-OutputFolder })
    $script:btnDeleteOutput.Add_Click({ Delete-OutputFolders })

    # Hyperlink for Output Directory
    $script:linkReportOutputDir.Add_RequestNavigate({
        param($sender, $e)
        $path = $e.Uri.OriginalString
        if (Test-Path $path) {
            Start-Process explorer.exe -ArgumentList $path
        } else {
            [System.Windows.MessageBox]::Show("Directory does not exist: $path", "Error", "OK", "Warning")
        }
        $e.Handled = $true
    })

    Write-Host "[INFO] Event handlers attached successfully"

    # Log initialization complete
    Log-Output "Query Store Analysis Utility initialized successfully"

    Write-Host "[INFO] Initialization complete!"
}

# ============================================================================
# CONFIGURATION FUNCTIONS
# ============================================================================

function Load-DatabaseConfiguration {
    Write-Host "[INFO] Loading database configuration..."

    if (-not (Test-Path $script:DatabaseConfigPath)) {
        Write-Host "[WARN] Database config not found: $script:DatabaseConfigPath"
        Write-Host "[INFO] Using default values"
        return
    }

    try {
        $dbConfig = Get-Content $script:DatabaseConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

        # Populate UI fields
        if ($dbConfig.servername) {
            $script:txtServer.Text = $dbConfig.servername
            Write-Host "[INFO] Loaded server: $($dbConfig.servername)"
        }

        if ($dbConfig.database) {
            $script:txtDatabase.Text = $dbConfig.database
            Write-Host "[INFO] Loaded database: $($dbConfig.database)"
        }

        if ($dbConfig.username) {
            $script:txtUsername.Text = $dbConfig.username
            Write-Host "[INFO] Loaded username: $($dbConfig.username)"
        }

        if ($dbConfig.password) {
            $script:txtPassword.Text = $dbConfig.password
            Write-Host "[INFO] Loaded password: $($dbConfig.password)"
        }

        $script:txtStatus.Text = "Database configuration loaded from file"

    } catch {
        Write-Host "[ERROR] Failed to load database config: $($_.Exception.Message)"
        $script:txtStatus.Text = "ERROR: Failed to load database configuration"
    }
}

function Save-DatabaseConfiguration {
    Write-Host "[INFO] Saving database configuration..."
    Log-Output "Saving database configuration..."

    try {
        $dbConfig = @{
            servername = $script:txtServer.Text
            database = $script:txtDatabase.Text
            username = $script:txtUsername.Text
            password = $script:txtPassword.Text
        }

        $json = $dbConfig | ConvertTo-Json -Depth 10

        # Write JSON without BOM (Python requires UTF-8 without BOM)
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($script:DatabaseConfigPath, $json, $utf8NoBom)

        Write-Host "[INFO] Database configuration saved to: $script:DatabaseConfigPath"
        Write-Host "[INFO] Server: $($script:txtServer.Text)"
        Write-Host "[INFO] Database: $($script:txtDatabase.Text)"
        Write-Host "[INFO] Username: $($script:txtUsername.Text)"
        # SECURITY: Do not log password
        Log-Output "Database configuration saved successfully"
        $script:txtStatus.Text = "Database configuration saved"

        [System.Windows.MessageBox]::Show("Database configuration saved successfully!`n`nServer: $($script:txtServer.Text)`nDatabase: $($script:txtDatabase.Text)`nUsername: $($script:txtUsername.Text)", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to save database config: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to save database configuration - $($_.Exception.Message)"
        $script:txtStatus.Text = "ERROR: Failed to save database configuration"
        [System.Windows.MessageBox]::Show("Failed to save database configuration:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

function Load-ReportsConfiguration {
    Write-Host "[INFO] Loading reports configuration..."

    if (-not (Test-Path $script:ReportsConfigPath)) {
        Write-Host "[ERROR] Reports config not found: $script:ReportsConfigPath"
        $script:txtStatus.Text = "ERROR: Reports configuration not found"
        return
    }

    try {
        $script:ReportsConfig = Get-Content $script:ReportsConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

        # Create collection for reports grid
        $reportsCollection = New-Object System.Collections.ObjectModel.ObservableCollection[Object]

        foreach ($reportKey in $script:ReportsConfig.reports.PSObject.Properties.Name) {
            $report = $script:ReportsConfig.reports.$reportKey

            if ($report.enabled) {
                $reportItem = [PSCustomObject]@{
                    key = $reportKey
                    name = $report.name
                    description = $report.description
                    status = "Ready"
                }
                $reportsCollection.Add($reportItem)
            }
        }

        # Bind to grid
        $script:ReportsGrid.ItemsSource = $reportsCollection

        Write-Host "[INFO] Loaded $($reportsCollection.Count) enabled reports"
        $script:txtStatus.Text = "Loaded $($reportsCollection.Count) reports - Configure connection and select a report"

    } catch {
        Write-Host "[ERROR] Failed to load reports config: $($_.Exception.Message)"
        $script:txtStatus.Text = "ERROR: Failed to load reports configuration"
    }
}

function Load-GitHubPaths {
    Write-Host "[INFO] Loading GitHub repository paths..."

    $pythonConfigPath = Join-Path $script:ConfigDir "config.json"

    if (-not (Test-Path $pythonConfigPath)) {
        Write-Host "[WARN] Python config not found: $pythonConfigPath"
        $script:txtGitHubProcsPath.Text = "config.json not found"
        $script:txtGitHubFunctionsPath.Text = "config.json not found"
        return
    }

    try {
        $pythonConfig = Get-Content $pythonConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

        # Extract GitHub repo paths
        $procsPath = $pythonConfig.paths.github_repo.procs
        $functionsPath = $pythonConfig.paths.github_repo.functions

        # Display in the UI
        $script:txtGitHubProcsPath.Text = if ($procsPath) { $procsPath } else { "Not configured" }
        $script:txtGitHubFunctionsPath.Text = if ($functionsPath) { $functionsPath } else { "Not configured" }

        Write-Host "[INFO] GitHub Procs Path: $procsPath"
        Write-Host "[INFO] GitHub Functions Path: $functionsPath"

    } catch {
        Write-Host "[ERROR] Failed to load GitHub paths: $($_.Exception.Message)"
        $script:txtGitHubProcsPath.Text = "Error loading paths"
        $script:txtGitHubFunctionsPath.Text = "Error loading paths"
    }
}

function Load-AIPrompts {
    Write-Host "[INFO] Loading AI prompts..."

    $promptsDir = Join-Path $script:ProjectRoot "AI_Prompt"

    if (-not (Test-Path $promptsDir)) {
        Write-Host "[WARN] AI_Prompt directory not found: $promptsDir"
        return
    }

    try {
        # Get all .md files in the AI_Prompt directory (excluding backup folder)
        $promptFiles = Get-ChildItem -Path $promptsDir -Filter "*.md" -File | Where-Object { $_.DirectoryName -eq $promptsDir }

        # Clear existing items
        $script:cmbAIPrompts.Items.Clear()

        # Add each prompt file to the dropdown
        foreach ($file in $promptFiles) {
            $promptItem = [PSCustomObject]@{
                DisplayName = $file.BaseName -replace '_', ' '
                FileName = $file.Name
                FullPath = $file.FullName
            }
            $script:cmbAIPrompts.Items.Add($promptItem) | Out-Null
        }

        # Set display member path
        $script:cmbAIPrompts.DisplayMemberPath = "DisplayName"

        Write-Host "[INFO] Loaded $($promptFiles.Count) AI prompts"

        # Select first item if available
        if ($script:cmbAIPrompts.Items.Count -gt 0) {
            $script:cmbAIPrompts.SelectedIndex = 0
        }

    } catch {
        Write-Host "[ERROR] Failed to load AI prompts: $($_.Exception.Message)"
    }
}

# ============================================================================
# CONNECTION TAB EVENT HANDLERS
# ============================================================================

function Test-DatabaseConnection {
    Write-Host "[INFO] Testing database connection..."

    $server = $script:txtServer.Text
    $database = $script:txtDatabase.Text
    $username = $script:txtUsername.Text
    $password = $script:txtPassword.Text

    if ([string]::IsNullOrWhiteSpace($server) -or [string]::IsNullOrWhiteSpace($database)) {
        [System.Windows.MessageBox]::Show("Please enter server and database names", "Validation Error", "OK", "Warning")
        return
    }

    $script:txtStatus.Text = "Testing connection..."
    $script:txtConnectionStatus.Text = "Testing..."
    $script:txtConnectionStatus.Foreground = "Orange"
    $script:btnTestConnection.IsEnabled = $false

    try {
        # Build connection string based on authentication type
        if ([string]::IsNullOrWhiteSpace($username)) {
            # Windows Authentication
            Write-Host "[INFO] Using Windows Authentication"
            $connectionString = "Server=$server;Database=$database;Integrated Security=True;TrustServerCertificate=True;Connection Timeout=5;"
        } else {
            # SQL Server Authentication
            Write-Host "[INFO] Using SQL Server Authentication with username: $username"
            $connectionString = "Server=$server;Database=$database;User ID=$username;Password=$password;TrustServerCertificate=True;Connection Timeout=5;"
        }

        # Test connection using .NET SqlConnection
        Add-Type -AssemblyName System.Data
        $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
        $connection.Open()

        $version = $connection.ServerVersion
        $connection.Close()

        $script:txtStatus.Text = "Connection successful!"
        $script:txtConnectionStatus.Text = "Connected - Server Version: $version"
        $script:txtConnectionStatus.Foreground = "Green"
        $script:txtConnectionStatus.FontStyle = "Normal"

        $authType = if ([string]::IsNullOrWhiteSpace($username)) { "Windows Authentication" } else { "SQL Authentication (User: $username)" }
        [System.Windows.MessageBox]::Show("Connection successful!`n`nServer: $server`nDatabase: $database`nAuthentication: $authType`nVersion: $version", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Connection failed: $($_.Exception.Message)"
        $script:txtStatus.Text = "Connection failed"
        $script:txtConnectionStatus.Text = "Connection failed"
        $script:txtConnectionStatus.Foreground = "Red"
        $script:txtConnectionStatus.FontStyle = "Normal"

        [System.Windows.MessageBox]::Show("Connection failed:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    } finally {
        $script:btnTestConnection.IsEnabled = $true
    }
}

# ============================================================================
# QUERYID TAB EVENT HANDLERS
# ============================================================================

function Get-QueryByID {
    Write-Host "[INFO] Retrieving query by ID..."
    Log-Output "Retrieving query by ID..."

    $queryID = $script:txtQueryID.Text.Trim()

    # Validate input
    if ([string]::IsNullOrWhiteSpace($queryID)) {
        [System.Windows.MessageBox]::Show("Please enter a Query ID", "Validation Error", "OK", "Warning")
        return
    }

    # Validate it's a number
    if (-not ($queryID -match '^\d+$')) {
        [System.Windows.MessageBox]::Show("Query ID must be a number", "Validation Error", "OK", "Warning")
        return
    }

    try {
        $script:txtStatus.Text = "Retrieving query $queryID..."
        $script:txtQueryText.Text = "Loading query from database...`n`nThis may take a few seconds..."

        # Path to Python script
        $pythonScript = Join-Path $script:PythonDir "06_lookup_query_by_id.py"

        if (-not (Test-Path $pythonScript)) {
            throw "Python script not found: $pythonScript"
        }

        Write-Host "[INFO] Executing Python script: $pythonScript"
        Write-Host "[INFO] Query ID: $queryID"

        # Execute Python script with unique temp files to avoid conflicts
        $pythonExe = "python"
        $arguments = @($pythonScript, $queryID)

        # Use unique temp file names to avoid conflicts with multiple instances
        $tempGuid = [System.Guid]::NewGuid().ToString()
        $tempOutputFile = Join-Path $env:TEMP "query_lookup_output_$tempGuid.txt"
        $tempErrorFile = Join-Path $env:TEMP "query_lookup_error_$tempGuid.txt"

        try {
            $process = Start-Process -FilePath $pythonExe -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $tempOutputFile -RedirectStandardError $tempErrorFile

            # Check exit code
            if ($process.ExitCode -ne 0) {
                $errorOutput = if (Test-Path $tempErrorFile) { Get-Content $tempErrorFile -Raw } else { "Unknown error" }
                Write-Host "[ERROR] Python script failed with exit code: $($process.ExitCode)"
                Write-Host "[ERROR] Error output: $errorOutput"

                if ($errorOutput -match "not found") {
                    $script:txtQueryText.Text = "Query ID $queryID not found in Query Store"
                    [System.Windows.MessageBox]::Show("Query ID $queryID not found in Query Store", "Not Found", "OK", "Information")
                } else {
                    throw "Python script failed: $errorOutput"
                }
                return
            }

            # Get output file path from Python script output
            $output = if (Test-Path $tempOutputFile) { Get-Content $tempOutputFile -Raw } else { "" }
            Write-Host "[DEBUG] Python output:"
            Write-Host $output

            $outputFileLine = $output -split "`n" | Where-Object { $_ -match "^OUTPUT_FILE:" } | Select-Object -First 1

            if ($outputFileLine) {
                $outputFile = ($outputFileLine -replace "^OUTPUT_FILE:", "").Trim()
                Write-Host "[INFO] Output file path: $outputFile"
                Write-Host "[DEBUG] File exists: $(Test-Path $outputFile)"

                # Read the formatted query from the output file
                if (Test-Path $outputFile) {
                    $formattedQuery = Get-Content $outputFile -Raw -Encoding UTF8
                    $script:txtQueryText.Text = $formattedQuery

                    # Extract object name from the file header
                    $objectName = "Ad-hoc query"
                    if ($formattedQuery -match "-- Object: (.+)") {
                        $objectName = $matches[1]
                    }
                    $script:txtStoredProcedure.Text = $objectName
                    Write-Host "[INFO] Object name: $objectName"

                    Write-Host "[INFO] Retrieved query $queryID successfully"
                    Log-Output "Retrieved query $queryID successfully - Object: $objectName"
                    $script:txtStatus.Text = "Query $queryID retrieved - saved to Output\QueryID_Lookup\"

                    # Show success message
                    [System.Windows.MessageBox]::Show(
                        "Query ID $queryID retrieved successfully!`n`nObject: $objectName`n`nFormatted query saved to:`n$outputFile",
                        "Success",
                        "OK",
                        "Information"
                    )
                } else {
                    Write-Host "[ERROR] Output file not found at: $outputFile"
                    Log-Output "ERROR: Output file not found"
                    Write-Host "[DEBUG] Checking Output directory..."
                    $outputDir = Join-Path $script:OutputDir "QueryID_Lookup"
                    if (Test-Path $outputDir) {
                        Write-Host "[DEBUG] Files in output directory:"
                        Get-ChildItem $outputDir | ForEach-Object { Write-Host "  - $($_.Name)" }
                    }
                    throw "Output file not found: $outputFile"
                }
            } else {
                Write-Host "[ERROR] Could not find OUTPUT_FILE line in Python output"
                throw "Could not find output file path in Python script output"
            }

        } catch {
            Write-Host "[ERROR] Failed to retrieve query: $($_.Exception.Message)"
            $script:txtQueryText.Text = "Error: $($_.Exception.Message)"
            $script:txtStatus.Text = "Error retrieving query"
            [System.Windows.MessageBox]::Show("Failed to retrieve query:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
        } finally {
            # Clean up temp files
            if (Test-Path $tempOutputFile) { Remove-Item $tempOutputFile -Force -ErrorAction SilentlyContinue }
            if (Test-Path $tempErrorFile) { Remove-Item $tempErrorFile -Force -ErrorAction SilentlyContinue }
        }

    } catch {
        Write-Host "[ERROR] Failed to execute query lookup: $($_.Exception.Message)"
        $script:txtQueryText.Text = "Error: $($_.Exception.Message)"
        $script:txtStatus.Text = "Error"
    }
}

function Copy-QuerySQL {
    Write-Host "[INFO] Copying SQL to clipboard..."

    $queryText = $script:txtQueryText.Text

    if ([string]::IsNullOrWhiteSpace($queryText) -or $queryText -eq "Error: " -or $queryText.StartsWith("Loading")) {
        [System.Windows.MessageBox]::Show("No query text to copy. Please retrieve a query first.", "Info", "OK", "Information")
        return
    }

    try {
        # Copy to clipboard
        Set-Clipboard -Value $queryText

        Write-Host "[INFO] SQL copied to clipboard"
        $script:txtStatus.Text = "SQL query copied to clipboard"

        [System.Windows.MessageBox]::Show("SQL query copied to clipboard!", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to copy SQL: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to copy SQL to clipboard:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

function Open-ObjectFile {
    Write-Host "[INFO] Opening object file..."

    $objectName = $script:txtStoredProcedure.Text

    if ([string]::IsNullOrWhiteSpace($objectName) -or $objectName -eq "Ad-hoc query") {
        [System.Windows.MessageBox]::Show("No stored procedure or function to open. This is an ad-hoc query.", "Info", "OK", "Information")
        return
    }

    try {
        # Load config.json to get GitHub paths
        $pythonConfigPath = Join-Path $script:ConfigDir "config.json"

        if (-not (Test-Path $pythonConfigPath)) {
            [System.Windows.MessageBox]::Show("Python config file not found: $pythonConfigPath", "Error", "OK", "Warning")
            return
        }

        $pythonConfig = Get-Content $pythonConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $procsPath = $pythonConfig.paths.github_repo.procs
        $functionsPath = $pythonConfig.paths.github_repo.functions

        if ([string]::IsNullOrWhiteSpace($procsPath) -or [string]::IsNullOrWhiteSpace($functionsPath)) {
            [System.Windows.MessageBox]::Show("GitHub repository paths not configured in config.json", "Error", "OK", "Warning")
            return
        }

        # Determine object type and file extension based on naming convention
        $filePath = $null
        $fileExtension = $null
        $objectType = $null

        if ($objectName -match '^sp') {
            # Stored Procedure - use .PRC extension and procs path
            $fileExtension = ".PRC"
            $filePath = Join-Path $procsPath "$objectName$fileExtension"
            $objectType = "Stored Procedure"
            Write-Host "[INFO] Detected stored procedure (starts with 'sp'): $objectName"
        } elseif ($objectName -match '^fn') {
            # Function - use .UDF extension and functions path
            $fileExtension = ".UDF"
            $filePath = Join-Path $functionsPath "$objectName$fileExtension"
            $objectType = "Function"
            Write-Host "[INFO] Detected function (starts with 'fn'): $objectName"
        } else {
            # Unknown type - try both locations with .sql extension as fallback
            Write-Host "[WARN] Object name doesn't start with 'sp' or 'fn', trying both locations..."
            $procFile = Join-Path $procsPath "$objectName.sql"
            $functionFile = Join-Path $functionsPath "$objectName.sql"

            if (Test-Path $procFile) {
                $filePath = $procFile
                $objectType = "Stored Procedure"
            } elseif (Test-Path $functionFile) {
                $filePath = $functionFile
                $objectType = "Function"
            }
        }

        # Try to open the file
        if ($filePath -and (Test-Path $filePath)) {
            Write-Host "[INFO] Opening $objectType`: $filePath"
            Start-Process $filePath
            $script:txtStatus.Text = "Opened: $objectName"
        } else {
            $message = "Object file not found:`n`n"
            if ($objectName -match '^sp') {
                $message += "Expected Path: $filePath`n"
                $message += "Object Type: Stored Procedure (.PRC)`n"
            } elseif ($objectName -match '^fn') {
                $message += "Expected Path: $filePath`n"
                $message += "Object Type: Function (.UDF)`n"
            } else {
                $message += "Tried Procs: $(Join-Path $procsPath "$objectName.sql")`n"
                $message += "Tried Functions: $(Join-Path $functionsPath "$objectName.sql")`n"
            }
            $message += "`nPlease verify the object name and GitHub repository paths."
            [System.Windows.MessageBox]::Show($message, "File Not Found", "OK", "Warning")
            Write-Host "[WARN] Object file not found: $objectName"
        }

    } catch {
        Write-Host "[ERROR] Failed to open object file: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to open object file:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

# ============================================================================
# REPORTS TAB EVENT HANDLERS
# ============================================================================

function On-ReportSelected {
    if ($script:ReportsGrid.SelectedItem -eq $null) {
        $script:btnExecuteReport.IsEnabled = $false
        $script:btnSaveReportConfig.IsEnabled = $false
        $script:txtSelectedReport.Text = "None"
        $script:txtReportOutputDir.Text = ""
        $script:SelectedReportKey = $null
        return
    }

    try {
        $selectedReport = $script:ReportsGrid.SelectedItem
        $script:SelectedReportKey = $selectedReport.key

        Write-Host "[INFO] Selected report: $($selectedReport.name) ($($script:SelectedReportKey))"

        # Update UI
        $script:txtSelectedReport.Text = $selectedReport.name
        $script:btnExecuteReport.IsEnabled = $true
        $script:btnSaveReportConfig.IsEnabled = $true

        # Get report configuration
        $reportConfig = $script:ReportsConfig.reports.($script:SelectedReportKey)

        if (-not $reportConfig) {
            Write-Host "[ERROR] Report configuration not found for: $($script:SelectedReportKey)"
            [System.Windows.MessageBox]::Show(
                "Report configuration not found for: $($selectedReport.name)`n`nPlease verify the report is properly configured.",
                "Configuration Error",
                "OK",
                "Warning"
            )
            $script:btnExecuteReport.IsEnabled = $false
            $script:btnSaveReportConfig.IsEnabled = $false
            return
        }

        # Update output directory (with validation)
        if ($reportConfig.output -and $reportConfig.output.base_dir) {
            $outputPath = Join-Path $script:ProjectRoot $reportConfig.output.base_dir
            $script:txtReportOutputDir.Text = $outputPath
            $script:linkReportOutputDir.NavigateUri = $outputPath
        } else {
            Write-Host "[WARN] Report missing output configuration"
            $script:txtReportOutputDir.Text = "Not configured"
        }

        # Update Top N from config (with validation)
        if ($reportConfig.processing -and ($reportConfig.processing.PSObject.Properties.Name -contains 'top_n_queries')) {
            $script:txtTopN.Text = $reportConfig.processing.top_n_queries.ToString()
        } else {
            # Set default value if not configured
            $script:txtTopN.Text = "10"
            Write-Host "[INFO] Report does not have top_n_queries property, using default: 10"
        }

        # Update checkboxes from config (with validation)
        if ($reportConfig.processing -and ($reportConfig.processing.PSObject.Properties.Name -contains 'include_execution_plans')) {
            $script:chkIncludePlans.IsChecked = $reportConfig.processing.include_execution_plans
        } else {
            $script:chkIncludePlans.IsChecked = $false
        }

        if ($reportConfig.processing -and ($reportConfig.processing.PSObject.Properties.Name -contains 'analyze_indexes')) {
            $script:chkAnalyzeIndexes.IsChecked = $reportConfig.processing.analyze_indexes
        } else {
            $script:chkAnalyzeIndexes.IsChecked = $false
        }

        $script:txtStatus.Text = "Selected: $($selectedReport.name) - Click Execute to run"

    } catch {
        Write-Host "[ERROR] Failed to select report: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to load report configuration.`n`nError: $($_.Exception.Message)",
            "Error",
            "OK",
            "Error"
        )
        $script:btnExecuteReport.IsEnabled = $false
        $script:btnSaveReportConfig.IsEnabled = $false
        $script:txtStatus.Text = "Error loading report configuration"
    }
}

function Save-ReportConfiguration {
    param([bool]$ShowSuccessMessage = $false)

    Write-Host "[INFO] Saving report configuration changes..."
    Write-Host "[DEBUG] Selected report key: $script:SelectedReportKey"

    if ($null -eq $script:SelectedReportKey) {
        Write-Host "[ERROR] No report selected"
        if ($ShowSuccessMessage) {
            [System.Windows.MessageBox]::Show("Please select a report first.", "Validation Error", "OK", "Warning")
        }
        return
    }

    try {
        # Update the in-memory config with UI values
        $reportConfig = $script:ReportsConfig.reports.($script:SelectedReportKey)

        if ($null -eq $reportConfig) {
            Write-Host "[ERROR] Report config is null for key: $script:SelectedReportKey"
            return
        }

        Write-Host "[DEBUG] Current top_n_queries: $($reportConfig.processing.top_n_queries)"
        Write-Host "[DEBUG] UI txtTopN value: $($script:txtTopN.Text)"

        # Update Top N (only if the property exists)
        if ($reportConfig.processing.PSObject.Properties.Name -contains 'top_n_queries') {
            $topN = [int]$script:txtTopN.Text
            $reportConfig.processing.top_n_queries = $topN
            Write-Host "[INFO] Updated top_n_queries to: $topN"
        } else {
            Write-Host "[WARN] Report does not have top_n_queries property"
        }

        # Update Include Plans
        $reportConfig.processing.include_execution_plans = $script:chkIncludePlans.IsChecked
        Write-Host "[INFO] Updated include_execution_plans to: $($script:chkIncludePlans.IsChecked)"

        # Update Analyze Indexes
        $reportConfig.processing.analyze_indexes = $script:chkAnalyzeIndexes.IsChecked
        Write-Host "[INFO] Updated analyze_indexes to: $($script:chkAnalyzeIndexes.IsChecked)"

        # Save to file
        Write-Host "[DEBUG] Saving to: $script:ReportsConfigPath"
        $json = $script:ReportsConfig | ConvertTo-Json -Depth 10
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($script:ReportsConfigPath, $json, $utf8NoBom)

        Write-Host "[INFO] Report configuration saved successfully"

        # Update status
        $script:txtStatus.Text = "Configuration saved for: $($reportConfig.name)"

        # Show success message if requested
        if ($ShowSuccessMessage) {
            [System.Windows.MessageBox]::Show("Configuration saved successfully!`n`nReport: $($reportConfig.name)`nTop N: $($script:txtTopN.Text)`nInclude Plans: $($script:chkIncludePlans.IsChecked)`nAnalyze Indexes: $($script:chkAnalyzeIndexes.IsChecked)", "Success", "OK", "Information")
        }
    } catch {
        Write-Host "[ERROR] Failed to save report configuration: $($_.Exception.Message)"
        Write-Host "[ERROR] Stack trace: $($_.ScriptStackTrace)"

        if ($ShowSuccessMessage) {
            [System.Windows.MessageBox]::Show("Failed to save configuration:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
        }
    }
}

function Execute-Report {
    Write-Host "[INFO] Execute-Report triggered"
    Log-Output "Executing Query Store report..."

    # Validate connection settings
    if ([string]::IsNullOrWhiteSpace($script:txtServer.Text)) {
        [System.Windows.MessageBox]::Show("Please enter a server name in the Connection tab", "Validation Error", "OK", "Warning")
        $script:MainTabControl.SelectedIndex = 0  # Switch to Connection tab
        return
    }

    if ([string]::IsNullOrWhiteSpace($script:txtDatabase.Text)) {
        [System.Windows.MessageBox]::Show("Please enter a database name in the Connection tab", "Validation Error", "OK", "Warning")
        $script:MainTabControl.SelectedIndex = 0  # Switch to Connection tab
        return
    }

    if ($script:SelectedReportKey -eq $null) {
        [System.Windows.MessageBox]::Show("Please select a report", "Validation Error", "OK", "Warning")
        return
    }

    $reportConfig = $script:ReportsConfig.reports.($script:SelectedReportKey)
    $reportName = $reportConfig.name

    Write-Host "[INFO] Executing report: $reportName ($($script:SelectedReportKey))"

    # Save report configuration changes (Top N, checkboxes, etc.)
    Save-ReportConfiguration

    # Show progress bar
    $script:pnlProgress.Visibility = "Visible"
    $script:progressBar.Value = 0
    $script:txtProgressStatus.Text = "Initializing..."

    # Update status
    $script:txtStatus.Text = "Executing $reportName..."
    $script:btnExecuteReport.IsEnabled = $false

    # Update report status in grid
    $selectedItem = $script:ReportsGrid.SelectedItem
    $selectedItem.status = "Running..."
    $script:ReportsGrid.Items.Refresh()

    # Force UI update
    [System.Windows.Forms.Application]::DoEvents()

    # Build Python command
    $pythonScript = Join-Path $script:PythonDir "run_all_scripts.py"

    $script:progressBar.Value = 10
    $script:txtProgressStatus.Text = "Validating Python scripts..."
    [System.Windows.Forms.Application]::DoEvents()

    if (-not (Test-Path $pythonScript)) {
        [System.Windows.MessageBox]::Show("Python script not found: $pythonScript", "Error", "OK", "Error")
        $script:txtStatus.Text = "Error: Python script not found"
        $script:btnExecuteReport.IsEnabled = $true
        $script:pnlProgress.Visibility = "Collapsed"
        $selectedItem.status = "Error"
        $script:ReportsGrid.Items.Refresh()
        return
    }

    # Update active-report-config.json with the selected report
    $script:progressBar.Value = 20
    $script:txtProgressStatus.Text = "Updating configuration..."
    [System.Windows.Forms.Application]::DoEvents()

    $activeReportPath = Join-Path $script:ConfigDir "active-report-config.json"
    try {
        $activeReportConfig = Get-Content $activeReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $activeReportConfig.active_report = $script:SelectedReportKey
        $json = $activeReportConfig | ConvertTo-Json -Depth 10

        # Write JSON without BOM (Python requires UTF-8 without BOM)
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($activeReportPath, $json, $utf8NoBom)

        Write-Host "[INFO] Updated active report to: $script:SelectedReportKey"
    } catch {
        Write-Host "[WARN] Failed to update active-report-config.json: $($_.Exception.Message)"
    }

    # Set environment variables for Python script (for backward compatibility)
    $env:QS_SERVER = $script:txtServer.Text
    $env:QS_DATABASE = $script:txtDatabase.Text
    $env:QS_REPORT_TYPE = $script:SelectedReportKey

    try {
        # Run Python script with real-time output parsing
        $script:progressBar.Value = 30
        $script:txtProgressStatus.Text = "Starting Python analysis..."
        [System.Windows.Forms.Application]::DoEvents()

        Write-Host "[INFO] Executing: python `"$pythonScript`""

        # Start Python process with output redirection
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "`"$pythonScript`""
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true

        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi

        # Track script progress (maps script name to progress percentage)
        $scriptProgress = @{
            "01_extract_query_store_data.py" = 35
            "02_extract_xml_execution_plans.py" = 45
            "03_extract_table_names_from_xml_plans.py" = 55
            "04_extract_index_and_statistics_for_tables.py" = 65
            "05_create_json_execution_plans.py" = 75
        }

        # Track total scripts and current script for dynamic progress
        $totalScripts = 0
        $currentScriptIndex = 0

        # Collections to store output
        $stdoutLines = New-Object System.Collections.ArrayList
        $stderrLines = New-Object System.Collections.ArrayList

        # Event handlers for asynchronous output reading (prevents deadlock)
        $stdoutEvent = Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action {
            if ($EventArgs.Data) {
                $line = $EventArgs.Data
                Write-Host $line
                [void]$Event.MessageData.Add($line)
            }
        } -MessageData $stdoutLines

        $stderrEvent = Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action {
            if ($EventArgs.Data) {
                $line = $EventArgs.Data
                Write-Host ("[STDERR] " + $line)
                [void]$Event.MessageData.Add($line)
            }
        } -MessageData $stderrLines

        # Start process and begin async reading
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()

        # Monitor progress while process is running
        while (-not $process.HasExited) {
            Start-Sleep -Milliseconds 100

            # Process stdout lines for progress updates
            foreach ($line in $stdoutLines) {
                # Detect total number of scripts
                if ($line -match "Scripts to execute: (\d+)") {
                    $totalScripts = [int]$matches[1]
                    Write-Host "[INFO] Total scripts to run: $totalScripts"
                }

                # Parse for script execution messages
                if ($line -match "\[(\d+)/(\d+)\] Executing: (\d+_\w+\.py)") {
                    $currentScriptIndex = [int]$matches[1]
                    $totalScripts = [int]$matches[2]
                    $scriptName = $matches[3]
                    Write-Host "[INFO] Detected script $currentScriptIndex of $totalScripts : $scriptName"

                    # Update progress bar based on which script is running
                    if ($scriptProgress.ContainsKey($scriptName)) {
                        $script:progressBar.Value = $scriptProgress[$scriptName]
                        $script:txtProgressStatus.Text = "[$currentScriptIndex/$totalScripts] Running: $scriptName"
                        [System.Windows.Forms.Application]::DoEvents()
                    }
                }
                elseif ($line -match "Starting: (\d+_\w+\.py)") {
                    $scriptName = $matches[1]
                    Write-Host "[INFO] Starting script: $scriptName"

                    if ($scriptProgress.ContainsKey($scriptName)) {
                        $script:progressBar.Value = $scriptProgress[$scriptName]
                        if ($totalScripts -gt 0 -and $currentScriptIndex -gt 0) {
                            $script:txtProgressStatus.Text = "[$currentScriptIndex/$totalScripts] Running: $scriptName"
                        } else {
                            $script:txtProgressStatus.Text = "Running: $scriptName"
                        }
                        [System.Windows.Forms.Application]::DoEvents()
                    }
                }
            }

            # Keep UI responsive
            [System.Windows.Forms.Application]::DoEvents()
        }

        # Wait for process to fully exit
        $process.WaitForExit()
        $exitCode = $process.ExitCode

        # Unregister event handlers
        Unregister-Event -SourceIdentifier $stdoutEvent.Name -ErrorAction SilentlyContinue
        Unregister-Event -SourceIdentifier $stderrEvent.Name -ErrorAction SilentlyContinue

        # Display any errors
        if ($stderrLines.Count -gt 0) {
            Write-Host "[ERROR] Python errors:"
            foreach ($errLine in $stderrLines) {
                Write-Host $errLine
            }
        }

        $script:progressBar.Value = 80
        $script:txtProgressStatus.Text = "Processing results..."
        [System.Windows.Forms.Application]::DoEvents()

        # Check if successful
        if ($exitCode -eq 0) {
            $script:progressBar.Value = 90
            $script:txtProgressStatus.Text = "Loading results..."
            [System.Windows.Forms.Application]::DoEvents()

            $script:txtStatus.Text = "Report complete - Loading results..."
            $selectedItem.status = "Complete"
            $script:ReportsGrid.Items.Refresh()

            # Load results
            Load-ReportResults -ReportKey $script:SelectedReportKey

            $script:progressBar.Value = 100
            $script:txtProgressStatus.Text = "Complete!"
            [System.Windows.Forms.Application]::DoEvents()

            # Switch to Results tab
            $script:MainTabControl.SelectedIndex = 2

            $script:txtStatus.Text = "Report execution complete!"
            Log-Output "Report executed successfully!"

            # Hide progress bar after a short delay (500ms for user feedback)
            Start-Sleep -Milliseconds 500
            $script:pnlProgress.Visibility = "Collapsed"

            [System.Windows.MessageBox]::Show("Report executed successfully!`n`nResults loaded in the Results tab.", "Success", "OK", "Information")
        } else {
            Log-Output "ERROR: Report execution failed with exit code: $exitCode"
            $script:txtStatus.Text = "Report execution failed - Check console for details"
            $selectedItem.status = "Failed"
            $script:ReportsGrid.Items.Refresh()
            $script:pnlProgress.Visibility = "Collapsed"
            [System.Windows.MessageBox]::Show("Report execution failed. Check the console output for details.", "Error", "OK", "Error")
        }
    } catch {
        Write-Host "[ERROR] Failed to execute report: $($_.Exception.Message)"
        $script:txtStatus.Text = "Error: $($_.Exception.Message)"
        $selectedItem.status = "Error"
        $script:ReportsGrid.Items.Refresh()
        $script:pnlProgress.Visibility = "Collapsed"
        [System.Windows.MessageBox]::Show("Error executing report: $($_.Exception.Message)", "Error", "OK", "Error")
    } finally {
        $script:btnExecuteReport.IsEnabled = $true
    }
}

# ============================================================================
# RESULTS TAB EVENT HANDLERS
# ============================================================================

function Load-ReportResults {
    param([string]$ReportKey)

    Write-Host "[INFO] Loading results for: $ReportKey"

    try {
        $reportConfig = $script:ReportsConfig.reports.$ReportKey

        if (-not $reportConfig) {
            Write-Host "[ERROR] Report not found in config: $ReportKey"
            [System.Windows.MessageBox]::Show(
                "Report configuration not found for: $ReportKey`n`nPlease verify the report is properly configured.",
                "Report Not Available",
                "OK",
                "Warning"
            )
            $script:txtStatus.Text = "Report not available"
            return
        }

        # Validate report configuration has required properties
        if (-not $reportConfig.output) {
            Write-Host "[ERROR] Report configuration missing 'output' section: $ReportKey"
            [System.Windows.MessageBox]::Show(
                "Report '$($reportConfig.name)' is not properly configured.`n`nMissing output configuration.",
                "Report Not Available",
                "OK",
                "Warning"
            )
            $script:txtStatus.Text = "Report configuration incomplete"
            return
        }

        if (-not $reportConfig.output.base_dir) {
            Write-Host "[ERROR] Report configuration missing 'output.base_dir': $ReportKey"
            [System.Windows.MessageBox]::Show(
                "Report '$($reportConfig.name)' is not properly configured.`n`nMissing output directory configuration.",
                "Report Not Available",
                "OK",
                "Warning"
            )
            $script:txtStatus.Text = "Report configuration incomplete"
            return
        }

        if (-not $reportConfig.output.main_results_json) {
            Write-Host "[ERROR] Report configuration missing 'output.main_results_json': $ReportKey"
            [System.Windows.MessageBox]::Show(
                "Report '$($reportConfig.name)' is not properly configured.`n`nMissing results file configuration.",
                "Report Not Available",
                "OK",
                "Warning"
            )
            $script:txtStatus.Text = "Report configuration incomplete"
            return
        }

        # Build path to results JSON
        $resultsPath = Join-Path $script:ProjectRoot $reportConfig.output.base_dir
        $resultsFile = Join-Path $resultsPath $reportConfig.output.main_results_json

        Write-Host "[INFO] Looking for results at: $resultsFile"

        if (-not (Test-Path $resultsFile)) {
            Write-Host "[WARN] Results file not found: $resultsFile"
            [System.Windows.MessageBox]::Show(
                "Report '$($reportConfig.name)' has not been executed yet or results are not available.`n`nExpected file: $resultsFile`n`nPlease execute the report first.",
                "Results Not Available",
                "OK",
                "Information"
            )
            $script:txtStatus.Text = "No results found - Execute report first"
            $script:txtResultsReportName.Text = "$($reportConfig.name) - No results found"
            return
        }

        # Load JSON results
        $jsonContent = Get-Content $resultsFile -Raw -Encoding UTF8 | ConvertFrom-Json

        # Check if the JSON has the new wrapper structure (with 'data' property)
        if ($jsonContent.PSObject.Properties.Name -contains 'data') {
            Write-Host "[INFO] Detected new JSON format with wrapper structure"
            $results = $jsonContent.data
            $recordCount = $jsonContent.record_count
            $timestamp = $jsonContent.extraction_timestamp
            Write-Host "[INFO] Extraction timestamp: $timestamp"
            Write-Host "[INFO] Record count: $recordCount"
        } else {
            # Old format - direct array
            Write-Host "[INFO] Detected old JSON format (direct array)"
            $results = $jsonContent
        }

        # Clear existing data
        $script:ResultsGrid.ItemsSource = $null
        $script:ResultsGrid.Items.Refresh()
        Write-Host "[DEBUG] Cleared existing grid data"

        # Convert to array if needed
        if ($results -is [System.Array]) {
            $dataArray = $results
        } else {
            $dataArray = @($results)
        }

        Write-Host "[DEBUG] Data array count: $($dataArray.Count)"
        Write-Host "[DEBUG] Data array type: $($dataArray.GetType().Name)"

        # Convert to ArrayList for proper sorting support in WPF
        $arrayList = New-Object System.Collections.ArrayList
        foreach ($item in $dataArray) {
            $arrayList.Add($item) | Out-Null
        }

        # Bind to grid (auto-generate columns from JSON)
        $script:ResultsGrid.ItemsSource = $arrayList
        Write-Host "[DEBUG] Grid ItemsSource set with ArrayList"

        # Get the Items collection view and enable live sorting
        $itemsView = $script:ResultsGrid.Items
        if ($itemsView -ne $null) {
            Write-Host "[DEBUG] Items view obtained, CanSort: $($itemsView.CanSort)"
            Write-Host "[DEBUG] Items view type: $($itemsView.GetType().Name)"
        }

        # Force UI update
        [System.Windows.Forms.Application]::DoEvents()

        # Update header
        $script:txtResultsReportName.Text = "$($reportConfig.name) - $($dataArray.Count) rows"

        Write-Host "[INFO] Loaded $($dataArray.Count) results"
        $script:txtStatus.Text = "Loaded $($dataArray.Count) rows from $($reportConfig.name)"

    } catch {
        Write-Host "[ERROR] Failed to load results: $($_.Exception.Message)"
        Write-Host "[ERROR] Stack trace: $($_.ScriptStackTrace)"

        # Show user-friendly error message
        [System.Windows.MessageBox]::Show(
            "Failed to load report results.`n`nError: $($_.Exception.Message)`n`nPlease check the error log for details.",
            "Error Loading Results",
            "OK",
            "Error"
        )

        $script:txtStatus.Text = "Error loading results"
        if ($reportConfig -and $reportConfig.name) {
            $script:txtResultsReportName.Text = "$($reportConfig.name) - Error loading results"
        } else {
            $script:txtResultsReportName.Text = "Error loading results"
        }
    }
}

function Refresh-Results {
    Write-Host "[INFO] Refreshing results..."

    if ($script:SelectedReportKey -eq $null) {
        [System.Windows.MessageBox]::Show("No report has been executed yet. Please execute a report first.", "Info", "OK", "Information")
        return
    }

    Load-ReportResults -ReportKey $script:SelectedReportKey
    $script:txtStatus.Text = "Results refreshed"
}

function Clear-Results {
    Write-Host "[INFO] Clearing results..."

    $script:ResultsGrid.ItemsSource = $null
    $script:txtResultsReportName.Text = "No results loaded"
    $script:txtStatus.Text = "Results cleared"
}

function Export-ResultsToExcel {
    Write-Host "[INFO] Exporting results to Excel..."
    Log-Output "Exporting results to Excel..."

    # Validate that we have results to export
    if ($script:ResultsGrid.ItemsSource -eq $null -or $script:ResultsGrid.Items.Count -eq 0) {
        [System.Windows.MessageBox]::Show("No results to export. Please execute a report first.", "Info", "OK", "Information")
        return
    }

    if ($script:SelectedReportKey -eq $null) {
        [System.Windows.MessageBox]::Show("No report selected.", "Error", "OK", "Warning")
        return
    }

    try {
        $script:txtStatus.Text = "Exporting to Excel..."

        # Get report configuration
        $reportConfig = $script:ReportsConfig.reports.$($script:SelectedReportKey)

        # Create Excel COM object
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false

        # Create new workbook
        $workbook = $excel.Workbooks.Add()
        $worksheet = $workbook.Worksheets.Item(1)
        $worksheet.Name = $reportConfig.name.Substring(0, [Math]::Min(31, $reportConfig.name.Length))

        # Get data from grid
        $data = $script:ResultsGrid.ItemsSource

        # Get column names from the first item
        $firstItem = $data[0]
        $properties = $firstItem.PSObject.Properties.Name

        # Write headers
        $col = 1
        foreach ($prop in $properties) {
            $worksheet.Cells.Item(1, $col).Value2 = $prop
            $col++
        }

        # Format header row
        $headerRange = $worksheet.Range($worksheet.Cells.Item(1, 1), $worksheet.Cells.Item(1, $properties.Count))
        $headerRange.Font.Bold = $true
        $headerRange.Font.Size = 11
        $headerRange.Interior.Color = 15773696  # Light blue
        $headerRange.Font.Color = 16777215      # White

        # Write data rows
        $row = 2
        foreach ($item in $data) {
            $col = 1
            foreach ($prop in $properties) {
                $value = $item.$prop
                if ($value -ne $null) {
                    # Convert value to string to avoid type casting issues
                    $cellValue = $value.ToString()
                    $worksheet.Cells.Item($row, $col).Value2 = $cellValue

                    # Try to format as number if it's numeric
                    if ($value -is [int] -or $value -is [long] -or $value -is [double] -or $value -is [decimal]) {
                        $worksheet.Cells.Item($row, $col).NumberFormat = "0"
                        if ($value -is [double] -or $value -is [decimal]) {
                            $worksheet.Cells.Item($row, $col).NumberFormat = "0.00"
                        }
                    }
                }
                $col++
            }
            $row++
        }

        # Auto-fit columns
        $usedRange = $worksheet.UsedRange
        $usedRange.Columns.AutoFit() | Out-Null

        # Add filters to header row
        $usedRange.AutoFilter() | Out-Null

        # Add grid borders
        $usedRange.Borders.LineStyle = 1  # xlContinuous
        $usedRange.Borders.Weight = 2     # xlThin

        # Freeze header row
        $worksheet.Application.ActiveWindow.SplitRow = 1
        $worksheet.Application.ActiveWindow.FreezePanes = $true

        # Determine output path
        $reportOutputDir = Join-Path $script:OutputDir $script:SelectedReportKey
        if (-not (Test-Path $reportOutputDir)) {
            New-Item -Path $reportOutputDir -ItemType Directory -Force | Out-Null
        }

        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $fileName = "$($script:SelectedReportKey)_$timestamp.xlsx"
        $filePath = Join-Path $reportOutputDir $fileName

        # Save workbook
        $workbook.SaveAs($filePath)
        Write-Host "[INFO] Excel file saved: $filePath"

        # Close workbook
        $workbook.Close($false)
        $excel.Quit()

        # Release COM objects
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()

        # Auto-open the file
        Write-Host "[INFO] Opening Excel file..."
        Start-Process $filePath

        $script:txtStatus.Text = "Exported $($data.Count) rows to Excel"
        Log-Output "Successfully exported $($data.Count) rows to Excel"
        [System.Windows.MessageBox]::Show("Successfully exported $($data.Count) rows to Excel!`n`nFile: $fileName`n`nLocation: $reportOutputDir", "Export Complete", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to export to Excel: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to export to Excel - $($_.Exception.Message)"
        Write-Host "[ERROR] Stack trace: $($_.ScriptStackTrace)"
        $script:txtStatus.Text = "Error exporting to Excel"
        [System.Windows.MessageBox]::Show("Failed to export to Excel:`n`n$($_.Exception.Message)", "Error", "OK", "Error")

        # Clean up COM objects on error
        if ($excel) {
            try {
                $excel.Quit()
                [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
            } catch {}
        }
    }
}

# ============================================================================
# AI PROMPTS TAB EVENT HANDLERS
# ============================================================================

function On-PromptSelected {
    if ($script:cmbAIPrompts.SelectedItem -eq $null) {
        $script:txtPromptContent.Text = ""
        $script:txtPromptsDirectoryPath.Text = ""
        return
    }

    $selectedPrompt = $script:cmbAIPrompts.SelectedItem
    Write-Host "[INFO] Selected prompt: $($selectedPrompt.DisplayName)"

    try {
        # Load the prompt file content
        $content = Get-Content $selectedPrompt.FullPath -Raw -Encoding UTF8
        $script:txtPromptContent.Text = $content

        # Update the path display to show the selected file path
        $script:txtPromptsDirectoryPath.Text = $selectedPrompt.FullPath

        Write-Host "[INFO] Loaded prompt from: $($selectedPrompt.FullPath)"
        $script:txtStatus.Text = "Loaded prompt: $($selectedPrompt.DisplayName)"

    } catch {
        Write-Host "[ERROR] Failed to load prompt: $($_.Exception.Message)"
        $script:txtPromptContent.Text = "Error loading prompt: $($_.Exception.Message)"
        $script:txtStatus.Text = "Error loading prompt"
    }
}

function Copy-PromptsPath {
    Write-Host "[INFO] Copying prompts directory path to clipboard..."

    try {
        $path = $script:txtPromptsDirectoryPath.Text

        if ([string]::IsNullOrWhiteSpace($path)) {
            [System.Windows.MessageBox]::Show("No directory path available", "Info", "OK", "Information")
            return
        }

        # Copy to clipboard
        Set-Clipboard -Value $path

        Write-Host "[INFO] Copied to clipboard: $path"
        $script:txtStatus.Text = "Directory path copied to clipboard"

        [System.Windows.MessageBox]::Show("Directory path copied to clipboard!`n`n$path", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to copy path: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to copy path to clipboard:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

# ============================================================================
# PYTHON CONFIG TAB EVENT HANDLERS
# ============================================================================

function Load-PythonConfig {
    Write-Host "[INFO] Loading Python configuration files..."

    try {
        # Get all JSON files in the Config directory
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
    Log-Output "Loading config file: $selectedFile"

    try {
        $configPath = Join-Path $script:ConfigDir $selectedFile

        if (-not (Test-Path $configPath)) {
            $script:txtConfigContent.Text = "Configuration file not found: $configPath"
            $script:txtConfigFilePath.Text = ""
            $script:txtStatus.Text = "Config file not found"
            return
        }

        # Read the config file
        $configContent = Get-Content $configPath -Raw -Encoding UTF8

        # Display in the text box
        $script:txtConfigContent.Text = $configContent

        # Update the path display to show the selected file path
        $script:txtConfigFilePath.Text = $configPath

        Write-Host "[INFO] Config file loaded: $selectedFile"
        Log-Output "Config file loaded successfully"
        $script:txtStatus.Text = "Loaded: $selectedFile"

    } catch {
        Write-Host "[ERROR] Failed to load config: $($_.Exception.Message)"
        Log-Output "ERROR: Failed to load config file - $($_.Exception.Message)"
        $script:txtConfigContent.Text = "Error loading configuration: $($_.Exception.Message)"
        $script:txtConfigFilePath.Text = ""
        $script:txtStatus.Text = "Error loading config"
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

    try{
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
        Log-Output "Config file saved successfully"
        $script:txtStatus.Text = "Saved: $selectedFile"

        [System.Windows.MessageBox]::Show("Configuration file saved successfully!`n`n$selectedFile", "Success", "OK", "Information")

        # Reload configurations if database or reports config was changed
        if ($selectedFile -eq "database-config.json") {
            Load-DatabaseConfiguration
        } elseif ($selectedFile -eq "reports-config.json") {
            Load-ReportsConfiguration
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
        $script:txtStatus.Text = "Config file refreshed"

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
        $script:txtStatus.Text = "Config file path copied to clipboard"

        [System.Windows.MessageBox]::Show("Config file path copied to clipboard!`n`n$path", "Success", "OK", "Information")

    } catch {
        Write-Host "[ERROR] Failed to copy path: $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show("Failed to copy path to clipboard:`n`n$($_.Exception.Message)", "Error", "OK", "Error")
    }
}

# ============================================================================
# TOOLBAR EVENT HANDLERS
# ============================================================================

function Open-OutputFolder {
    Write-Host "[INFO] Opening output folder..."
    Log-Output "Opening output folder..."

    if (Test-Path $script:OutputDir) {
        Start-Process explorer.exe -ArgumentList $script:OutputDir
        Log-Output "Opened output folder: $script:OutputDir"
    } else {
        Log-Output "WARNING: Output folder does not exist"
        [System.Windows.MessageBox]::Show("Output folder not found: $script:OutputDir", "Error", "OK", "Warning")
    }
}

function Delete-OutputFolders {
    Write-Host "[INFO] Delete Output Folders requested..."
    Log-Output "Cleanup operation started"

    # Load cleanup configuration from cleanup-config.json
    $cleanupConfigPath = Join-Path $script:ConfigDir "cleanup-config.json"

    if (-not (Test-Path $cleanupConfigPath)) {
        Write-Host "[ERROR] Cleanup configuration file not found: $cleanupConfigPath"
        [System.Windows.MessageBox]::Show(
            "Cleanup configuration file not found:`n$cleanupConfigPath",
            "Configuration Not Found",
            "OK",
            "Error"
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
            "OK",
            "Error"
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
            "OK",
            "Information"
        )
        return
    }

    # Build confirmation message
    $confirmMessage = "This will delete files from the following folders:`n`n"
    foreach ($operation in $deleteOperations) {
        $confirmMessage += "$($operation.path)`n  ($($operation.description))`n`n"
    }
    $confirmMessage += "This action cannot be undone. Continue?"

    # Confirm deletion
    $result = [System.Windows.MessageBox]::Show(
        $confirmMessage,
        "Confirm Deletion",
        "YesNo",
        "Warning"
    )

    if ($result -ne "Yes") {
        Write-Host "[INFO] Deletion cancelled by user"
        Log-Output "Cleanup cancelled by user"
        return
    }

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
                # Delete all files in the folder recursively
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
            $icon = "Information"
        } else {
            $message = "Cleanup completed with errors.`n`n$deletedCount file(s) deleted`n$errorCount error(s) occurred"
            $icon = "Warning"
        }

        [System.Windows.MessageBox]::Show(
            $message,
            "Cleanup Complete",
            "OK",
            $icon
        )

        $script:txtStatus.Text = "Cleanup complete - $deletedCount file(s) deleted"
        Write-Host "[INFO] Cleanup complete - Deleted: $deletedCount, Errors: $errorCount"
        Log-Output "Cleanup complete - Deleted: $deletedCount files, Errors: $errorCount"

    } catch {
        Write-Host "[ERROR] Failed to delete folders: $($_.Exception.Message)"
        Log-Output "ERROR: Cleanup failed - $($_.Exception.Message)"
        [System.Windows.MessageBox]::Show(
            "Failed to delete folders:`n`n$($_.Exception.Message)",
            "Error",
            "OK",
            "Error"
        )
        $script:txtStatus.Text = "Error deleting folders"
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
    Reads the logs base_dir path from config.json and opens it in Windows Explorer.
    Creates the folder if it doesn't exist.
    #>

    Write-Host "[INFO] Opening Logs folder..."
    Log-Output "Opening Logs folder..."

    try {
        # Read config.json to get the logs base_dir path
        $logsDir = $null
        $configPath = Join-Path $script:ConfigDir "config.json"

        if (Test-Path $configPath) {
            $configJson = Get-Content -Path $configPath -Raw | ConvertFrom-Json

            if ($configJson.paths.logs.base_dir) {
                # Construct full path
                $logsDir = Join-Path $script:ProjectRoot $configJson.paths.logs.base_dir
                Write-Host "[INFO] Logs directory from config: $logsDir"
            } else {
                Write-Host "[WARN] logs.base_dir not found in config.json, using default"
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
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUBCf0OGM57s9vs8JVGC5wFkxI
# ZMKgghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
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
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBTvWm+D/ZL/pXMF
# YNyGYIsz+6SbMDANBgkqhkiG9w0BAQEFAASCAQBP0nI1SoIZdAhXuNylCoasQbc1
# W3E8lqEDkwjO1S2sf/QwXBvClmpvOQnHuXebxCdWtxarbtRV/pusmMtbkc1zjN9A
# U7nNDKoeY6dCcan4/Ep/InRSJymobkq8/m8wBhGBADOpIKQu5WQpOwLE9cKwdpBa
# Ywm+gD2cfJS4sijaQZPiqdib1UlAqHy1IHYthYamtYQ3sZzE4nIS2WmCynyZVLNC
# i/LIgcPTPNtmbxY1H3wSNr1KGALbOBcqNMCnLZccZIwCxANmu1pb6EDqH8ZWQ4D2
# ioR8B5gaq9t6dkLyd1QBTv7PwjihCZm7IqL3A5TEuIllZSgD3gEzR0PJiD75oYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMzU1NlowLwYJKoZIhvcNAQkE
# MSIEIKFQ5/VG7kkvHFFFnQwH3cVk7IN2PbgOQ8IF6u6Fqc7tMA0GCSqGSIb3DQEB
# AQUABIICAELql9TLbNRzMaQB9JRlNqcvPx7hm+mOSb42GMEU1tAVwOSLk19Ip/cr
# YegEUBu4G6r3aUTRLx/wLh+DsdR8V6XJIBQ3xCDXp8Jlof+AvaZ7UWFqsFARHurW
# BYepsEEgDZ40HVz9dlWSe3eAXJMQlfB/z7lJ8UHZhpbcUeUhfnN6iD6XmXhiEOYk
# VCQIW82cILuewX8VCezkDncPwueARY16OiV+CHgx6Tb1glmtpsxTKmfOQAnChBTc
# zPmgSlplt4iUAJ70FQzErECkKlJZYNt6rvVF9Wt2h0TAnbojCr/S1Ijkyg4qRNKT
# 5oY4f7SqCp1pHMWzV26nBsfEUfp8Y4E/H9pS70QcGsmbHFSNNNLVCbWIHukQjz47
# 6W/T33rGzK2LG66KSB5pCZuks2PyheGrnNKUZXwu5GcV40cYWYTbvMstBWEA5ZJp
# myfx61ZmhabsDQ+5SRyO2PD563xm1ChRmj/6sqzOJIaIqxN5yhgdLccAaVNBtAI2
# YxMcJ8z8Xhs9b6s17ZMlXY8t0h63E2dFTX1+qbIsnOldS6LLjoSnX16e0234ZAMU
# 8+KeRsv6URFnRfAfvAlra78GZW03xX+7decXUed2QDt0YxVonkuvuNCvSCiu9ZQb
# B0wfnFI6p7h4jvaM6kikkyM9YAXAZvJm6zpzzSyV8hDWtCXtCvG0
# SIG # End signature block
