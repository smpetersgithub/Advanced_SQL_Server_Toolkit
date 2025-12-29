# Example1Functions.ps1

function Initialize-Example1 {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Window]$MainWindow,

        # Override if you move the JSON files
        [string]$ExecutionsJson = 'C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\JSON\Example1_Executions.json',
        [string]$TemplatesJson  = 'C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\JSON\Example1_Templates.json'
    )

    Write-Host "[INFO] Example1 init starting..."

    # Find the DataGrids (either directly on MainWindow or inside the Example1 tab)
    $ExecutionsGrid = $MainWindow.FindName('ExecutionsGrid')
    $TemplatesGrid  = $MainWindow.FindName('TemplatesGrid')

    if (-not $ExecutionsGrid -or -not $TemplatesGrid) {
        # If they’re within a tab usercontrol, try to find by header
        $tabControl = $MainWindow.FindName('TabControl')
        if ($tabControl) {
            $example1Tab = $tabControl.Items | Where-Object { $_.Header -eq 'Example 1' -or $_.Name -eq 'Example1Tab' }
            if ($example1Tab) {
                if (-not $ExecutionsGrid) { $ExecutionsGrid = $example1Tab.FindName('ExecutionsGrid') }
                if (-not $TemplatesGrid)  { $TemplatesGrid  = $example1Tab.FindName('TemplatesGrid')  }
            }
        }
    }

    if (-not $ExecutionsGrid) { Write-Host "[WARN] Could not find 'ExecutionsGrid'."; return }
    if (-not $TemplatesGrid)  { Write-Host "[WARN] Could not find 'TemplatesGrid'." ; return }

    # Load JSON safely and bind
    if (Test-Path -LiteralPath $ExecutionsJson) {
        try {
            $data = Get-Content -LiteralPath $ExecutionsJson -Raw | ConvertFrom-Json
            $ExecutionsGrid.ItemsSource = $data
            Write-Host "[INFO] Bound ExecutionsGrid to $ExecutionsJson"
        } catch {
            Write-Host "[ERROR] Failed to bind ExecutionsGrid: $($_.Exception.Message)"
        }
    } else {
        Write-Host "[WARN] Executions JSON not found: $ExecutionsJson"
    }

    if (Test-Path -LiteralPath $TemplatesJson) {
        try {
            $data = Get-Content -LiteralPath $TemplatesJson -Raw | ConvertFrom-Json
            $TemplatesGrid.ItemsSource = $data
            Write-Host "[INFO] Bound TemplatesGrid to $TemplatesJson"
        } catch {
            Write-Host "[ERROR] Failed to bind TemplatesGrid: $($_.Exception.Message)"
        }
    } else {
        Write-Host "[WARN] Templates JSON not found: $TemplatesJson"
    }

    Write-Host "[INFO] Example1 init complete."
}
