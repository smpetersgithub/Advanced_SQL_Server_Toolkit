<#
.SYNOPSIS
    Copy all README files to a centralized xReadMe directory

.DESCRIPTION
    This script finds all README.md files in the Advanced SQL Server Toolkit and copies them
    to a centralized xReadMe directory with names corresponding to their source utility.

.PARAMETER SourcePath
    The root path to search for README files (default: C:\Advanced_SQL_Server_Toolkit)

.PARAMETER DestinationPath
    The destination directory for copied README files (default: C:\Advanced_SQL_Server_Toolkit\xReadMe)

.PARAMETER ExcludeFolders
    Array of folder names to exclude from search (default: node_modules, .git, bin, obj)

.PARAMETER Force
    Overwrite existing files in destination (default: true)

.PARAMETER WhatIf
    Show what would be copied without actually copying

.EXAMPLE
    .\Copy-ReadmeFiles.ps1
    Copies all README files to xReadMe directory

.EXAMPLE
    .\Copy-ReadmeFiles.ps1 -WhatIf
    Shows what would be copied without actually copying

.EXAMPLE
    .\Copy-ReadmeFiles.ps1 -SourcePath "C:\MyProject" -DestinationPath "C:\MyProject\Docs"
    Copies README files from custom source to custom destination

.NOTES
    Author: Advanced SQL Server Toolkit
    Date: 2026-03-15
#>

param(
    [string]$SourcePath = "C:\Advanced_SQL_Server_Toolkit",
    [string]$DestinationPath = "C:\Advanced_SQL_Server_Toolkit\xReadMe",
    [string[]]$ExcludeFolders = @("node_modules", ".git", "bin", "obj", "__pycache__", ".vs", "venv", "env"),
    [switch]$Force = $true,
    [switch]$WhatIf = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "README File Copier" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate source path
if (-not (Test-Path $SourcePath)) {
    Write-Host "ERROR: Source path not found: $SourcePath" -ForegroundColor Red
    exit 1
}

# Create destination directory if it doesn't exist
if (-not (Test-Path $DestinationPath)) {
    if ($WhatIf) {
        Write-Host "[WHATIF] Would create directory: $DestinationPath" -ForegroundColor Yellow
    } else {
        Write-Host "Creating destination directory: $DestinationPath" -ForegroundColor Green
        New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
    }
}

Write-Host "Source Path:      $SourcePath" -ForegroundColor Cyan
Write-Host "Destination Path: $DestinationPath" -ForegroundColor Cyan
Write-Host ""

# Find all README.md files
Write-Host "Searching for README.md files..." -ForegroundColor Yellow
$readmeFiles = Get-ChildItem -Path $SourcePath -Filter "README.md" -Recurse -File | Where-Object {
    $exclude = $false
    foreach ($folder in $ExcludeFolders) {
        if ($_.FullName -like "*\$folder\*") {
            $exclude = $true
            break
        }
    }
    -not $exclude
}

Write-Host "Found $($readmeFiles.Count) README.md file(s)" -ForegroundColor Green
Write-Host ""

$copiedCount = 0
$skippedCount = 0
$errorCount = 0

foreach ($readme in $readmeFiles) {
    try {
        # Determine the relative path from source
        $relativePath = $readme.FullName.Substring($SourcePath.Length).TrimStart('\')
        
        # Generate a friendly name based on the directory structure
        $pathParts = $relativePath.Split('\')
        
        # Determine the new filename
        if ($pathParts.Count -eq 1) {
            # Root README
            $newName = "00_Main_Toolkit_README.md"
        } else {
            # Utility README - use the first directory name
            $utilityName = $pathParts[0]
            
            # Check if it's in a subdirectory (like AI_Prompt\backup)
            if ($pathParts.Count -gt 2) {
                $subPath = ($pathParts[0..($pathParts.Count - 2)] -join "_")
                $newName = "${subPath}_README.md"
            } else {
                $newName = "${utilityName}_README.md"
            }
        }
        
        $destinationFile = Join-Path $DestinationPath $newName
        
        # Display the copy operation
        $displaySource = $relativePath
        $displayDest = $newName
        
        if ($WhatIf) {
            Write-Host "[WHATIF] $displaySource" -ForegroundColor Yellow
            Write-Host "      -> $displayDest" -ForegroundColor Yellow
            $copiedCount++
        } else {
            # Check if file exists
            if ((Test-Path $destinationFile) -and -not $Force) {
                Write-Host "[SKIP] $displaySource (file exists)" -ForegroundColor DarkYellow
                Write-Host "    -> $displayDest" -ForegroundColor DarkYellow
                $skippedCount++
            } else {
                Copy-Item -Path $readme.FullName -Destination $destinationFile -Force
                Write-Host "[COPY] $displaySource" -ForegroundColor Green
                Write-Host "    -> $displayDest" -ForegroundColor Green
                $copiedCount++
            }
        }
        
    } catch {
        Write-Host "[ERROR] Failed to copy: $($readme.FullName)" -ForegroundColor Red
        Write-Host "        $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Copy Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host "Would copy: $copiedCount file(s)" -ForegroundColor Yellow
} else {
    Write-Host "Copied:  $copiedCount file(s)" -ForegroundColor Green
    Write-Host "Skipped: $skippedCount file(s)" -ForegroundColor DarkYellow
    Write-Host "Errors:  $errorCount file(s)" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
}

Write-Host ""

exit $(if ($errorCount -gt 0) { 1 } else { 0 })

