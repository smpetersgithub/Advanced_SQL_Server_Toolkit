# --- Ensure STA (WPF requires it) ---
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    $self = $MyInvocation.MyCommand.Path
    if (-not $self) { $self = $PSCommandPath }  # fallback
    Start-Process powershell -ArgumentList @(
        '-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',"`"$self`""
    )
    exit
}

# --- Load WPF Assemblies ---
Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase, System.Xaml | Out-Null

# ============================================================================
# HARDCODED PATHS - Update these paths for your environment
# ============================================================================
$ScriptDir = "C:\Advanced_SQL_Server_Toolkit\Execution_Plan_Analysis_Utility\Core\WPF\Scripts"

Write-Host "[INFO] Scripts  : $ScriptDir"

# Import Functions from the Scripts Directory
$FunctionFiles = @(
    "ExecutionPlanAnalysisFunctions.ps1"
)

foreach ($File in $FunctionFiles) {
    $FilePath = Join-Path -Path $ScriptDir -ChildPath $File
    if (Test-Path $FilePath) {
        . $FilePath
        Write-Host "[INFO] Loaded functions from $File"
    } else {
        Write-Host "[ERROR] Missing function file: $FilePath"
    }
}

# --- Helperless XAML loader (inline) ---
$loadXaml = {
    param([string]$relativePath)
    $full = Join-Path $ScriptDir $relativePath
    if (-not (Test-Path $full)) {
        Write-Host "[ERROR] XAML not found: $full"
        return $null
    }
    try {
        $xr = [System.Xml.XmlReader]::Create($full)
        [System.Windows.Markup.XamlReader]::Load($xr)
    } catch {
        Write-Host "[ERROR] Failed to load $full : $($_.Exception.Message)"
        $null
    }
}

# --- Load Main Window ---
Write-Host "[INFO] Loading MainWindow.xaml..."
$MainWindow = & $loadXaml 'MainWindow.xaml'
if (-not $MainWindow) { throw "Failed to load MainWindow.xaml" }

# --- Initialize the main window (no tabs) ---
try {
    Initialize-ExecutionPlanAnalysis -MainWindow $MainWindow
    Write-Host "[INFO] Main window initialized successfully"
} catch {
    Write-Host "[ERROR] Initialize-ExecutionPlanAnalysis failed: $($_.Exception.Message)"
}


# --- Show the window (modal) ---
Write-Host "[INFO] Showing window..."
[void]$MainWindow.ShowDialog()
Write-Host "[INFO] UI closed."

# SIG # Begin signature block
# MIIcQwYJKoZIhvcNAQcCoIIcNDCCHDACAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUcHXXpbhCSFC73JwFv+47g4BG
# trSgghaOMIIDUDCCAjigAwIBAgIQJDAhS7ot/IdFcBXskCRUAjANBgkqhkiG9w0B
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
# gjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBT1Bas58p7B3ZOJ
# N2rJqx7zcGwUgzANBgkqhkiG9w0BAQEFAASCAQBFsAoV0/s8hJp4pQI5+HCeEcF/
# 6b0i8DIlHGXFFE7aQ8C1SHRHYIl8bltCJHI0ek4nf2UsLkJk/tjZ03e17Isnb4D1
# RQ4ygWgyMeLHO1ereRMe/jLP3rjiawgZ6vlJ64Kr5U8SOk3yv5oFLx085I6ViIJB
# C0m+5VLlSXvQ/gYGIYS6uJbme3sHNT2A4IXbGigT11n0umYmY4cVlOBqsr2kq91R
# FuKz9MBmQCay6a9C4PNu9OCx8ax635CSrGSvZxJuRrdm1at2TnTtDfERAeJEo64O
# 4DObR/f9xItXSfxP9jmxXy0Vdsp6M1wJ6QLPe5MniXij9vjqGnWJ4+PbamI3oYID
# JjCCAyIGCSqGSIb3DQEJBjGCAxMwggMPAgEBMH0waTELMAkGA1UEBhMCVVMxFzAV
# BgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVk
# IEc0IFRpbWVTdGFtcGluZyBSU0E0MDk2IFNIQTI1NiAyMDI1IENBMQIQCoDvGEuN
# 8QWC0cR2p5V0aDANBglghkgBZQMEAgEFAKBpMBgGCSqGSIb3DQEJAzELBgkqhkiG
# 9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDMyNjEzMTAzNlowLwYJKoZIhvcNAQkE
# MSIEIAdPZx5hobd6bsb0B+Q1PSlBayIj9s6lGpPy+9gFVwzTMA0GCSqGSIb3DQEB
# AQUABIICAJ9EVWID6MY4PiOOBQwxAq9iBFtBpKMiZ9i+6CNTcQw2EyJY2D1wD91i
# bstEAqQD+/9h6ow21nThWOn+cFudfeHN+q6PSP3laycLNEsFSrMgsJ6AvfFQnoQz
# DfOgKgL19avuiTzzZPwfH181eT6BuuwEFoKm7LiRZ0YbzryIZQw2bstJQSXS4d07
# Gc6nVdSxB9knQha/bz0BJVZ+QSSSv07278aCUZQ5jfFK9t9bYKcwFsbJL5h9VKXa
# X71bzK+MqDxA1q6khEYYMbg1z7xbflCC8MsuLiggKeNcJhPvmD7cwhEG0aErEt0U
# wvbakTI7xQmFIUR3NlVflAed+ReSn3xb8BlhuzK7RtAheYGaghc+X7+bxSjo33d+
# l1mT9x1HpUdMVbrZeqN1/XKl48ihhjqn1pAiAGwpNyNNiGOqV92siqUplFeI1LjF
# HRaaWi2QU1dZmhXdw3Lb/Xqzk9XJ0pggdm3gIsojxeUzN+hZ9oLgWESogqfG2i8U
# jzyunWmb7Ni1TD+wCayeMF95wqlNW+YhjQ9GtKfHY4UqVr472oKHMDZekTgcxkbM
# bna3Ye5zuXbQKq9sgJHUnbBsr7cEF1lh6H2TOvYQdcQjG3FmkY+QMe2N/rgAB7Xz
# FgpG37Cz1NwLDhzJYax/X5CwtbBwEoGKvgHShRxJJ9Q+TRrfxAO/
# SIG # End signature block
