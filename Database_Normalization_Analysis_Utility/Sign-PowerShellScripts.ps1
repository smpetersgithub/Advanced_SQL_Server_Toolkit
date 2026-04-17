# Sign-PowerShellScripts.ps1
# This script creates a self-signed certificate (if needed) and signs all PowerShell scripts
# in the Database_Normalization_Analysis_Utility directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PowerShell Script Signing Utility" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$ScriptRoot = $PSScriptRoot
if (-not $ScriptRoot) {
    $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Write-Host "[INFO] Script Root: $ScriptRoot" -ForegroundColor Green
Write-Host ""

# Check for existing code signing certificates
Write-Host "[INFO] Checking for existing code signing certificates..." -ForegroundColor Yellow
$existingCert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Where-Object {
    $_.NotAfter -gt (Get-Date) -and
    $_.Subject -like "*Advanced SQL Server Toolkit*"
} | Select-Object -First 1

if ($existingCert) {
    Write-Host "[INFO] Found existing code signing certificate:" -ForegroundColor Green
    Write-Host "       Subject: $($existingCert.Subject)" -ForegroundColor Cyan
    Write-Host "       Thumbprint: $($existingCert.Thumbprint)" -ForegroundColor Cyan
    Write-Host "       Expires: $($existingCert.NotAfter)" -ForegroundColor Cyan
    Write-Host "[INFO] Using existing certificate automatically" -ForegroundColor Green
    Write-Host ""
    $cert = $existingCert
} else {
    $cert = $null
}

# Create a new self-signed certificate if needed
if (-not $cert) {
    Write-Host "[INFO] Creating new self-signed code signing certificate..." -ForegroundColor Yellow
    
    try {
        # Create the certificate
        $cert = New-SelfSignedCertificate `
            -Type CodeSigningCert `
            -Subject "CN=PowerShell Code Signing - Advanced SQL Server Toolkit" `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -NotAfter (Get-Date).AddYears(5)
        
        Write-Host "[SUCCESS] Certificate created successfully!" -ForegroundColor Green
        Write-Host "          Subject: $($cert.Subject)" -ForegroundColor Cyan
        Write-Host "          Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
        Write-Host "          Expires: $($cert.NotAfter)" -ForegroundColor Cyan
        Write-Host ""
        
        # Add certificate to Trusted Root (required for self-signed certs)
        Write-Host "[INFO] Adding certificate to Trusted Root store..." -ForegroundColor Yellow
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        Write-Host "[SUCCESS] Certificate added to Trusted Root store" -ForegroundColor Green
        Write-Host ""
        
    } catch {
        Write-Host "[ERROR] Failed to create certificate: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Find all PowerShell scripts in the directory
Write-Host "[INFO] Finding PowerShell scripts to sign..." -ForegroundColor Yellow
$scripts = Get-ChildItem -Path $ScriptRoot -Filter "*.ps1" -Recurse | Where-Object { $_.Name -ne "Sign-PowerShellScripts.ps1" }

Write-Host "[INFO] Found $($scripts.Count) script(s) to sign:" -ForegroundColor Green
foreach ($script in $scripts) {
    Write-Host "       - $($script.FullName.Replace($ScriptRoot, '.'))" -ForegroundColor Cyan
}
Write-Host ""

# Sign each script
$successCount = 0
$failCount = 0

foreach ($script in $scripts) {
    try {
        Write-Host "[INFO] Signing: $($script.Name)..." -ForegroundColor Yellow
        
        # Sign the script
        $result = Set-AuthenticodeSignature -FilePath $script.FullName -Certificate $cert -TimestampServer "http://timestamp.digicert.com"
        
        if ($result.Status -eq 'Valid') {
            Write-Host "[SUCCESS] Signed: $($script.Name)" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "[WARNING] Signature status: $($result.Status) for $($script.Name)" -ForegroundColor Yellow
            $failCount++
        }
        
    } catch {
        Write-Host "[ERROR] Failed to sign $($script.Name): $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Signing Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successfully signed: $successCount script(s)" -ForegroundColor Green
Write-Host "Failed to sign: $failCount script(s)" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "[INFO] Certificate Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
Write-Host ""

