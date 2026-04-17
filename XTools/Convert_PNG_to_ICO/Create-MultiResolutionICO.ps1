<#
.SYNOPSIS
    Create a multi-resolution ICO file from multiple PNG files

.DESCRIPTION
    This script combines multiple PNG files of different sizes into a single
    multi-resolution ICO file for better icon quality at different display sizes.

.PARAMETER PngFiles
    Array of PNG file paths to include in the ICO file (in order of size)

.PARAMETER OutputIco
    Path where the multi-resolution ICO file should be saved

.EXAMPLE
    .\Create-MultiResolutionICO.ps1 -PngFiles @("icon-16.png", "icon-32.png", "icon-48.png") -OutputIco "output.ico"

.NOTES
    Author: Advanced SQL Server Toolkit
    Date: 2026-03-23
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$PngFiles,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputIco
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Multi-Resolution ICO Creator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate all input files exist
foreach ($pngFile in $PngFiles) {
    if (-not (Test-Path $pngFile)) {
        Write-Host "ERROR: PNG file not found: $pngFile" -ForegroundColor Red
        exit 1
    }
    Write-Host "Input:  $pngFile" -ForegroundColor White
}

Write-Host "Output: $OutputIco" -ForegroundColor Cyan
Write-Host ""

try {
    Add-Type -AssemblyName System.Drawing
    
    # Create output directory if needed
    $outputDir = Split-Path -Parent $OutputIco
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    # Load all PNG images
    $images = @()
    foreach ($pngFile in $PngFiles) {
        $img = [System.Drawing.Image]::FromFile($pngFile)
        $images += $img
        Write-Host "Loaded: $($img.Width)x$($img.Height) - $pngFile" -ForegroundColor Green
    }
    
    # Create memory stream for ICO file
    $memoryStream = New-Object System.IO.MemoryStream
    $binaryWriter = New-Object System.IO.BinaryWriter($memoryStream)
    
    # Write ICO header
    $binaryWriter.Write([UInt16]0)           # Reserved (must be 0)
    $binaryWriter.Write([UInt16]1)           # Type (1 = ICO)
    $binaryWriter.Write([UInt16]$images.Count) # Number of images
    
    # Calculate offset for first image data (header + directory entries)
    $imageDataOffset = 6 + ($images.Count * 16)
    
    # Write directory entries and collect image data
    $imageDataList = @()
    
    foreach ($img in $images) {
        # Convert image to PNG format in memory
        $pngStream = New-Object System.IO.MemoryStream
        $img.Save($pngStream, [System.Drawing.Imaging.ImageFormat]::Png)
        $imageData = $pngStream.ToArray()
        $pngStream.Close()
        
        # Write directory entry
        $width = if ($img.Width -ge 256) { 0 } else { $img.Width }
        $height = if ($img.Height -ge 256) { 0 } else { $img.Height }
        
        $binaryWriter.Write([byte]$width)        # Width (0 = 256)
        $binaryWriter.Write([byte]$height)       # Height (0 = 256)
        $binaryWriter.Write([byte]0)             # Color palette (0 = no palette)
        $binaryWriter.Write([byte]0)             # Reserved
        $binaryWriter.Write([UInt16]1)           # Color planes
        $binaryWriter.Write([UInt16]32)          # Bits per pixel
        $binaryWriter.Write([UInt32]$imageData.Length) # Size of image data
        $binaryWriter.Write([UInt32]$imageDataOffset)  # Offset to image data
        
        $imageDataList += $imageData
        $imageDataOffset += $imageData.Length
    }
    
    # Write all image data
    foreach ($imageData in $imageDataList) {
        $binaryWriter.Write($imageData)
    }
    
    # Save to file
    $fileStream = [System.IO.File]::Create($OutputIco)
    $memoryStream.WriteTo($fileStream)
    $fileStream.Close()
    $memoryStream.Close()
    
    # Clean up
    foreach ($img in $images) {
        $img.Dispose()
    }
    
    Write-Host ""
    Write-Host "SUCCESS: Multi-resolution ICO file created!" -ForegroundColor Green
    Write-Host "Output: $OutputIco" -ForegroundColor Cyan
    Write-Host "Contains $($images.Count) resolution(s)" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception.StackTrace -ForegroundColor Red
    exit 1
}

Write-Host "Press any key to continue..." ; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


