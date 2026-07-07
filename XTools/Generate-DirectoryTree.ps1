<#
.SYNOPSIS
    Generate a visual directory tree structure for documentation

.DESCRIPTION
    This script creates a text-based directory tree visualization similar to the Unix 'tree' command.
    It can be used to document project structure in README files.

.PARAMETER Path
    The root path to generate the tree from (default: current directory)

.PARAMETER MaxDepth
    Maximum depth to traverse (default: 3)

.PARAMETER ExcludeFolders
    Array of folder names to exclude (default: node_modules, .git, bin, obj, __pycache__)

.PARAMETER ExcludeFiles
    Array of file patterns to exclude (default: *.pyc, *.pyo, .DS_Store)

.PARAMETER OutputFile
    Optional file path to save the output (default: console only)

.PARAMETER IncludeFiles
    Include files in the tree (default: true)

.PARAMETER IncludeHidden
    Include hidden files and folders (default: false)

.PARAMETER AddComments
    Add comment placeholders after each item (default: false)

.EXAMPLE
    .\Generate-DirectoryTree.ps1
    Generates tree for current directory

.EXAMPLE
    .\Generate-DirectoryTree.ps1 -Path "C:\MyProject" -MaxDepth 2
    Generates tree for specified path with max depth of 2

.EXAMPLE
    .\Generate-DirectoryTree.ps1 -Path "." -OutputFile "tree.txt" -AddComments
    Generates tree with comment placeholders and saves to file

.NOTES
    Author: Advanced SQL Server Toolkit
    Date: 2026-03-15
#>

param(
    [string]$Path = ".",
    [int]$MaxDepth = 3,
    [string[]]$ExcludeFolders = @("node_modules", ".git", "bin", "obj", "__pycache__", ".vs", "venv", "env"),
    [string[]]$ExcludeFiles = @("*.pyc", "*.pyo", ".DS_Store", "Thumbs.db"),
    [string]$OutputFile,
    [switch]$IncludeFiles = $true,
    [switch]$IncludeHidden = $false,
    [switch]$AddComments = $false
)

function Get-DirectoryTree {
    param(
        [string]$CurrentPath,
        [int]$CurrentDepth,
        [string]$Prefix = "",
        [bool]$IsLast = $true
    )

    if ($CurrentDepth -gt $MaxDepth) {
        return
    }

    $items = Get-ChildItem -Path $CurrentPath -Force:$IncludeHidden | Where-Object {
        # Exclude hidden items if not requested
        if (-not $IncludeHidden -and $_.Attributes -match "Hidden") {
            return $false
        }
        
        # Exclude folders
        if ($_.PSIsContainer -and $ExcludeFolders -contains $_.Name) {
            return $false
        }
        
        # Exclude files if not requested
        if (-not $_.PSIsContainer -and -not $IncludeFiles) {
            return $false
        }
        
        # Exclude file patterns
        if (-not $_.PSIsContainer) {
            foreach ($pattern in $ExcludeFiles) {
                if ($_.Name -like $pattern) {
                    return $false
                }
            }
        }
        
        return $true
    } | Sort-Object { $_.PSIsContainer }, Name -Descending

    $itemCount = $items.Count
    $currentIndex = 0

    foreach ($item in $items) {
        $currentIndex++
        $isLastItem = ($currentIndex -eq $itemCount)
        
        # Determine the tree characters
        if ($isLastItem) {
            $connector = "+-- "
            $extension = "    "
        } else {
            $connector = "|-- "
            $extension = "|   "
        }

        # Build the line
        $line = $Prefix + $connector + $item.Name
        
        # Add folder indicator
        if ($item.PSIsContainer) {
            $line += "/"
        }
        
        # Add comment placeholder
        if ($AddComments) {
            $line += "    # "
        }
        
        # Output the line
        Write-Output $line

        # Recurse into directories
        if ($item.PSIsContainer -and $CurrentDepth -lt $MaxDepth) {
            Get-DirectoryTree -CurrentPath $item.FullName `
                            -CurrentDepth ($CurrentDepth + 1) `
                            -Prefix ($Prefix + $extension) `
                            -IsLast $isLastItem
        }
    }
}

# Main execution
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Directory Tree Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Resolve the path
$resolvedPath = Resolve-Path -Path $Path -ErrorAction Stop
Write-Host "Generating tree for: $resolvedPath" -ForegroundColor Green
Write-Host "Max depth: $MaxDepth" -ForegroundColor Green
Write-Host "Include files: $IncludeFiles" -ForegroundColor Green
Write-Host "Include hidden: $IncludeHidden" -ForegroundColor Green
Write-Host ""

# Generate the tree
$output = @()
$output += (Split-Path -Leaf $resolvedPath) + "/"
$treeOutput = Get-DirectoryTree -CurrentPath $resolvedPath -CurrentDepth 0
$output += $treeOutput

# Display to console
$output | ForEach-Object { Write-Host $_ }

# Save to file if requested
if ($OutputFile) {
    $output | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Tree saved to: $OutputFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total lines: $($output.Count)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

