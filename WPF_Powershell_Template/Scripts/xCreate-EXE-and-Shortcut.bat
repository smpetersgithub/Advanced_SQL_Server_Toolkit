@echo off
setlocal

echo Cleaning up old builds...

:: --- Config ---
set "PS_SCRIPT=C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Scripts\Main.ps1"
set "OUTPUT_EXE=C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Scripts\My Application.exe"
set "ICON_PATH=C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Assets\icon8-satellite-50-icon.ico"

set "SHORTCUT_NAME=My Application.lnk"
set "SHORTCUT_SOURCE=C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Scripts\%SHORTCUT_NAME%"
set "SHORTCUT_DEST=C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\%SHORTCUT_NAME%"

:: --- Kill EXE if running ---
taskkill /IM "My Application.exe" /F >nul 2>&1
timeout /t 1 >nul

:: --- Delete the old EXE ---
if exist "%OUTPUT_EXE%" (
    echo Deleting old EXE...
    del "%OUTPUT_EXE%" /f >nul 2>&1
)

:: --- Delete old shortcuts ---
if exist "%SHORTCUT_SOURCE%" (
    echo Deleting shortcut in Scripts folder...
    del "%SHORTCUT_SOURCE%" /f >nul 2>&1
)

if exist "%SHORTCUT_DEST%" (
    echo Deleting shortcut in root folder...
    del "%SHORTCUT_DEST%" /f >nul 2>&1
)

echo Cleanup complete.

:: --- Compile PowerShell to EXE ---
echo.
echo === Compiling PowerShell to EXE ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Invoke-PS2EXE -InputFile '%PS_SCRIPT%' -OutputFile '%OUTPUT_EXE%' -iconFile '%ICON_PATH%' -noConsole -noOutput"



if errorlevel 1 (
    echo [ERROR] Failed to compile PowerShell script to EXE.
    pause
    exit /b 1
)

:: --- Create shortcut in Scripts folder ---
echo.
echo === Creating Shortcut in Scripts Folder ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT_SOURCE%');" ^
  "$s.TargetPath = '%OUTPUT_EXE%';" ^
  "$s.IconLocation = '%ICON_PATH%';" ^
  "$s.WorkingDirectory = 'C:\Advanced_SQL_Server_Toolkit\WPF_Powershell_Template\Scripts\';" ^
  "$s.Save();"

if not exist "%SHORTCUT_SOURCE%" (
    echo [ERROR] Failed to create shortcut in Scripts folder.
    pause
    exit /b 1
)

:: --- Copy shortcut to root folder ---
echo.
echo === Copying Shortcut to Root Folder ===
copy /Y "%SHORTCUT_SOURCE%" "%SHORTCUT_DEST%" >nul

if errorlevel 1 (
    echo [ERROR] Failed to copy shortcut to root folder.
    pause
    exit /b 1
)

echo.
echo Shortcut copied to: %SHORTCUT_DEST%
echo Build complete!
pause
