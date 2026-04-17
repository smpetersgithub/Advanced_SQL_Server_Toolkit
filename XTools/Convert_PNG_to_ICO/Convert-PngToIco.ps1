<#
.SYNOPSIS
    Centralized PNG to ICO converter for Advanced SQL Server Toolkit

.DESCRIPTION
    This script converts PNG images to ICO format using configuration from convert-config.json.
    It can convert a single file or all files defined in the configuration.

.PARAMETER PngPath
    Path to the PNG file to convert (optional - overrides config)

.PARAMETER IcoPath
    Path where the ICO file should be saved (optional - overrides config)

.PARAMETER ConvertAll
    Convert all files defined in the configuration file

.PARAMETER ConfigPath
    Path to the configuration file (default: convert-config.json in script directory)

.EXAMPLE
    .\Convert-PngToIco.ps1 -ConvertAll
    Converts all PNG files defined in the configuration

.EXAMPLE
    .\Convert-PngToIco.ps1 -PngPath "C:\path\to\image.png" -IcoPath "C:\path\to\output.ico"
    Converts a single PNG file to ICO

.NOTES
    Author: Advanced SQL Server Toolkit
    Date: 2026-03-15
#>

param(
    [string]$PngPath,
    [string]$IcoPath,
    [switch]$ConvertAll,
    [string]$ConfigPath
)

# Set default config path if not provided
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ConfigPath = Join-Path $scriptDir "convert-config.json"
}

function Convert-PngToIcoFile {
    param(
        [string]$PngFilePath,
        [string]$IcoFilePath,
        [string]$Name = ""
    )

    Write-Host ""
    if (-not [string]::IsNullOrWhiteSpace($Name)) {
        Write-Host "Converting: $Name" -ForegroundColor Cyan
    }
    Write-Host "Input:  $PngFilePath"
    Write-Host "Output: $IcoFilePath"

    try {
        # Validate input file exists
        if (-not (Test-Path $PngFilePath)) {
            Write-Host "ERROR: PNG file not found: $PngFilePath" -ForegroundColor Red
            return $false
        }

        # Create output directory if it doesn't exist
        $outputDir = Split-Path -Parent $IcoFilePath
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }

        Add-Type -AssemblyName System.Drawing
        
        # Load the PNG image
        $png = [System.Drawing.Image]::FromFile($PngFilePath)
        
        # Create a bitmap from the image
        $bitmap = New-Object System.Drawing.Bitmap $png
        
        # Get the icon handle
        $iconHandle = $bitmap.GetHicon()
        
        # Create an icon from the handle
        $icon = [System.Drawing.Icon]::FromHandle($iconHandle)
        
        # Save the icon to a file
        $fileStream = [System.IO.File]::Create($IcoFilePath)
        $icon.Save($fileStream)
        $fileStream.Close()
        
        # Clean up
        $png.Dispose()
        $bitmap.Dispose()
        
        Write-Host "SUCCESS: ICO file created!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PNG to ICO Converter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$successCount = 0
$failCount = 0

if ($ConvertAll) {
    # Load configuration file
    Write-Host "`nLoading configuration from: $ConfigPath"
    
    if (-not (Test-Path $ConfigPath)) {
        Write-Host "ERROR: Configuration file not found: $ConfigPath" -ForegroundColor Red
        exit 1
    }

    try {
        $config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
        
        Write-Host "Found $($config.conversions.Count) conversion(s) in configuration`n"
        
        foreach ($conversion in $config.conversions) {
            $result = Convert-PngToIcoFile -PngFilePath $conversion.png_path -IcoFilePath $conversion.ico_path -Name $conversion.name
            if ($result) {
                $successCount++
            } else {
                $failCount++
            }
        }
        
    } catch {
        Write-Host "ERROR: Failed to load configuration: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
} elseif (-not [string]::IsNullOrWhiteSpace($PngPath) -and -not [string]::IsNullOrWhiteSpace($IcoPath)) {
    # Convert single file
    $result = Convert-PngToIcoFile -PngFilePath $PngPath -IcoFilePath $IcoPath
    if ($result) {
        $successCount++
    } else {
        $failCount++
    }
    
} else {
    Write-Host "ERROR: Invalid parameters" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  Convert all files from config:  .\Convert-PngToIco.ps1 -ConvertAll"
    Write-Host "  Convert single file:            .\Convert-PngToIco.ps1 -PngPath <path> -IcoPath <path>"
    exit 1
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Conversion Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed:     $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

exit $(if ($failCount -gt 0) { 1 } else { 0 })

