# ==============================================================================
# Main.ps1 - Entry point for SQL Server Query Store Analysis WPF UI
# ==============================================================================
# Description: Initializes and launches the Query Store Analysis utility
# Author: SQL Server Query Store Analysis Utility
# Last Modified: 2026-02-27
# ==============================================================================

#Requires -Version 5.1

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================
$script:ErrorLogPath = Join-Path $env:TEMP "QueryStoreAnalysis_Error.log"

function Write-Log {
    <#
    .SYNOPSIS
        Writes a message to both console and log file
    .PARAMETER Message
        The message to log
    .PARAMETER Level
        Log level: INFO, WARN, ERROR, DEBUG
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [Parameter(Mandatory = $false)]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG', 'START')]
        [string]$Level = 'INFO'
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - [$Level] $Message"

    # Write to log file
    try {
        $logMessage | Out-File -FilePath $script:ErrorLogPath -Append -Encoding UTF8
    } catch {
        # Silently fail if we can't write to log
    }

    # Write to console with color coding
    switch ($Level) {
        'ERROR' { Write-Host $logMessage -ForegroundColor Red }
        'WARN'  { Write-Host $logMessage -ForegroundColor Yellow }
        'DEBUG' { Write-Host $logMessage -ForegroundColor Gray }
        'START' { Write-Host $logMessage -ForegroundColor Cyan }
        default { Write-Host $logMessage -ForegroundColor White }
    }
}

Write-Log "Application starting..." -Level START
Write-Log "Error log location: $script:ErrorLogPath" -Level INFO

# ============================================================================
# ENSURE RUNNING IN STA MODE (REQUIRED FOR WPF)
# ============================================================================
# Note: When compiled with PS2EXE, this check works correctly
# When running as .ps1 script, we check and relaunch if needed
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    Write-Log "Not running in STA mode. Relaunching in STA mode..." -Level WARN

    # Get script path
    $scriptPath = $MyInvocation.MyCommand.Path
    if (-not $scriptPath) { $scriptPath = $PSCommandPath }

    if ($scriptPath) {
        Start-Process powershell.exe -ArgumentList "-STA", "-NoProfile", "-ExecutionPolicy Bypass", "-File `"$scriptPath`"" -Wait
        exit 0
    } else {
        Write-Log "Cannot determine script path to relaunch in STA mode!" -Level ERROR
        exit 1
    }
}

Write-Log "Running in STA mode - OK" -Level INFO

# ============================================================================
# LOAD WPF ASSEMBLIES
# ============================================================================
Write-Log "Loading WPF assemblies..." -Level INFO

try {
    Add-Type -AssemblyName PresentationFramework
    Add-Type -AssemblyName PresentationCore
    Add-Type -AssemblyName WindowsBase
    Add-Type -AssemblyName System.Windows.Forms
    Write-Log "WPF assemblies loaded successfully" -Level INFO
} catch {
    Write-Log "Failed to load WPF assemblies: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR

    # Can't use MessageBox if assemblies didn't load, so just exit
    Write-Host "`nFailed to load WPF assemblies. Check error log at: $script:ErrorLogPath" -ForegroundColor Red
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
    exit 1
}

# ============================================================================
# CALCULATE PROJECT ROOT DIRECTORY
# ============================================================================
# When running as compiled EXE, $PSScriptRoot is empty or points to temp location
# In that case, the working directory is the Build folder (where EXE is)
# and we need to go up one level to get to Scripts folder

Write-Log "Calculating project paths..." -Level INFO
Write-Log "PSScriptRoot = '$PSScriptRoot'" -Level DEBUG
Write-Log "Working Dir  = '$(Get-Location)'" -Level DEBUG

if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    # Running as compiled EXE
    # Working directory is Build folder, Scripts folder is one level up
    $BuildDir = (Get-Location).Path
    $ScriptRoot = Split-Path -Parent $BuildDir
    Write-Log "Running as compiled EXE" -Level INFO
    Write-Log "Build Dir    : $BuildDir" -Level INFO
} else {
    # Running as .ps1 script - use $PSScriptRoot
    $ScriptRoot = $PSScriptRoot
    Write-Log "Running as PowerShell script" -Level INFO
}

# Navigate up from Scripts folder to project root
# Current structure: ProjectRoot\Core\WPF\Scripts\Main.ps1
# So we need to go up 3 levels: Scripts -> WPF -> Core -> ProjectRoot
$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptRoot))

Write-Log "Script Root  : $ScriptRoot" -Level INFO
Write-Log "Project Root : $ProjectRoot" -Level INFO

# ============================================================================
# LOAD XAML
# ============================================================================
$XamlPath = Join-Path $ScriptRoot "MainWindow.xaml"
Write-Log "XAML Path: $XamlPath" -Level DEBUG

if (-not (Test-Path -Path $XamlPath -PathType Leaf)) {
    Write-Log "XAML file not found: $XamlPath" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "XAML file not found:`n$XamlPath`n`nCheck error log at:`n$script:ErrorLogPath",
        "Error - File Not Found",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

Write-Log "Loading XAML from: $XamlPath" -Level INFO

try {
    [xml]$xaml = Get-Content -Path $XamlPath -Encoding UTF8 -Raw
    $reader = New-Object System.Xml.XmlNodeReader $xaml
    $MainWindow = [Windows.Markup.XamlReader]::Load($reader)
    Write-Log "XAML loaded successfully" -Level INFO
} catch {
    Write-Log "Failed to load XAML: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "Failed to load XAML. Check error log at:`n$script:ErrorLogPath`n`nError: $($_.Exception.Message)",
        "Error - XAML Load Failed",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

# ============================================================================
# LOAD FUNCTIONS
# ============================================================================
$FunctionsPath = Join-Path $ScriptRoot "QueryStoreAnalysisFunctions.ps1"
Write-Log "Functions Path: $FunctionsPath" -Level DEBUG

if (-not (Test-Path -Path $FunctionsPath -PathType Leaf)) {
    Write-Log "Functions file not found: $FunctionsPath" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "Functions file not found:`n$FunctionsPath`n`nCheck error log at:`n$script:ErrorLogPath",
        "Error - File Not Found",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

Write-Log "Loading functions from: $FunctionsPath" -Level INFO

try {
    . $FunctionsPath
    Write-Log "Functions loaded successfully" -Level INFO
} catch {
    Write-Log "Failed to load functions: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "Failed to load functions. Check error log at:`n$script:ErrorLogPath`n`nError: $($_.Exception.Message)",
        "Error - Functions Load Failed",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

# ============================================================================
# INITIALIZE APPLICATION
# ============================================================================
Write-Log "Initializing Query Store Analysis UI..." -Level INFO

try {
    Initialize-QueryStoreAnalysis -MainWindow $MainWindow -ProjectRoot $ProjectRoot
    Write-Log "Initialization complete" -Level INFO
} catch {
    Write-Log "Failed to initialize: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "Failed to initialize application. Check error log at:`n$script:ErrorLogPath`n`nError: $($_.Exception.Message)",
        "Error - Initialization Failed",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

# ============================================================================
# SHOW WINDOW AND RUN APPLICATION
# ============================================================================
Write-Log "Showing main window..." -Level INFO

try {
    $result = $MainWindow.ShowDialog()
    Write-Log "Application closed normally (Result: $result)" -Level INFO
} catch {
    Write-Log "Error showing window: $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    [System.Windows.MessageBox]::Show(
        "Error showing window. Check error log at:`n$script:ErrorLogPath`n`nError: $($_.Exception.Message)",
        "Error - Window Display Failed",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
    exit 1
}

# ============================================================================
# CLEANUP AND EXIT
# ============================================================================
Write-Log "Application shutdown complete" -Level INFO
exit 0


# SIG # Begin signature block
# MIIcQwYJKoZIhvcNAQcCoIIcNDCCHDACAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU67aQHU9YBwD32Ewi7wdLix+j
# qgmgghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
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
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBT+yhToSV9phI/1
# kD2iE74H81PAwzANBgkqhkiG9w0BAQEFAASCAQBl1dmSmRAgts8sK/rlom2HzVCb
# lkbA1DaF6F91xDUCZBEMujBFCtIuxCZwkeYt005/c+BRkzX9JYEonkmHKGh891St
# ZpfoTWCY8PjlcGfKqsXQ4FwcH5VB4buhhwyaEVmEW1QJC0gf5zuEWkp68XiVARh8
# pAVMMIs6qDY4aQoruvLflGZFpebDhgJvovSA+0zpJ/j4PCMXtz3rxZoXjzLIckT0
# Q45QgtT+Raoya788cYHJ5p6CT0N5u2L6NQGzwtVk+0ER9hAj6zMZez3qenIdozT5
# 3zcccbCs6M84hd528/6sw5Wu3LzZZOfnWkuL6VeWtOtcj42BblTvXXoxxNQgoYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMzU1NlowLwYJKoZIhvcNAQkE
# MSIEINYfWssUfJoi19vmAAyOIRNhviephw1LGxMKrpYYL9L3MA0GCSqGSIb3DQEB
# AQUABIICALF2z8FJDm+wfXficcSsvhUSDiknneo8UXGz9iVIqxvh+k6QGE929HJG
# h1w1+kKun5nU9tp8B7Jb2gU1nd49tRtG6mEec3DgHQGYxuWCbCb0loKuZGj1FJLS
# lCajqu8yj0VZXk3Mj0cr3asdaRm0EdC4PhR5tOXCFRXJ8c3bTAT7xgps+teirNmC
# 0fZ4HKCLEDQmx5IwMemNM3kXVCmgNzXEHzizt8D1vWJArZXc0Ue7Oj/Z/M11EWne
# rGCekJrY4Z4Z3ZByje8H/Z1Nua5izVFBDTFg+450ZH19DWwjuCr+sWwzAe8i2ufA
# rmNOHFVw5xLKLq4GKPqH3A53NqJQ/ilxZEMWHML65RUj47zFcT/ffyNVyDCBd8Qq
# jpntA5Scihfl9d4VYvC4S9acOVfoXH/tQhA8SnNQakVbDC++sRrcsRdOYLxls06L
# 5v+jG3vXockABoUxn8CG7ZovlWXuZYmugrm1YkgUanQ4qz0dr3ibjTaUQp6cF2mb
# NvKlAOGKT6NRDlMGG/fgM9vFzOHDFkJ20PFP6CypszTEIiRcY9dQJX2TAVMpI+7H
# wRgh8cgjv3VD5941d5m7/rxtiGFwksIyIzLagw5o6Fdp4/Ku+jdl2E26ZhfY9SLb
# KFgaXRNz3Uujn+x+Oo3sIeGZfOY6JadPRR2eDYemLZgYvv3EKQKl
# SIG # End signature block
