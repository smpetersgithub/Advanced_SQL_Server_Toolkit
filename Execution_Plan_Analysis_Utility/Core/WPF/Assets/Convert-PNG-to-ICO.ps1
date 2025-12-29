# Convert PNG to ICO
# This script converts a PNG file to ICO format for use with the EXE builder

Add-Type -AssemblyName System.Drawing

# Calculate paths relative to this script
# This script is in: ProjectRoot\Core\WPF\Assets\Convert-PNG-to-ICO.ps1
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$pngPath = Join-Path $ScriptDir "icons8-communication-64.png"
$icoPath = Join-Path $ScriptDir "icons8-communication-64.ico"

Write-Host "Converting PNG to ICO..."
Write-Host "Source: $pngPath"
Write-Host "Destination: $icoPath"

try {
    # Load the PNG image
    $png = [System.Drawing.Image]::FromFile($pngPath)
    
    # Create icon from the image
    $bitmap = New-Object System.Drawing.Bitmap $png
    $icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
    
    # Save as ICO file
    $fileStream = [System.IO.FileStream]::new($icoPath, [System.IO.FileMode]::Create)
    $icon.Save($fileStream)
    $fileStream.Close()
    
    # Cleanup
    $png.Dispose()
    $bitmap.Dispose()
    
    Write-Host ""
    Write-Host "SUCCESS! Icon file created at:" -ForegroundColor Green
    Write-Host $icoPath -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to convert PNG to ICO" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
}

pause

