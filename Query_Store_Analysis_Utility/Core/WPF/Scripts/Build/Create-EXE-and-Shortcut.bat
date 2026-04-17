@echo off
setlocal

echo Cleaning up old builds...

:: --- Calculate paths relative to this batch file ---
:: This batch file is in: ProjectRoot\Core\WPF\Scripts\Build\Create-EXE-and-Shortcut.bat
:: %~dp0 gives us the directory where this batch file is located

set "BUILD_DIR=%~dp0"
set "SCRIPTS_DIR=%BUILD_DIR%.."
set "WPF_DIR=%SCRIPTS_DIR%\.."
set "CORE_DIR=%WPF_DIR%\.."
set "PROJECT_ROOT=%CORE_DIR%\.."

:: Resolve to absolute paths (removes ..)
for %%i in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fi"
for %%i in ("%SCRIPTS_DIR%") do set "SCRIPTS_DIR=%%~fi"
for %%i in ("%WPF_DIR%") do set "WPF_DIR=%%~fi"
for %%i in ("%BUILD_DIR%") do set "BUILD_DIR=%%~fi"

:: --- Config (now using relative paths) ---
set "PS_SCRIPT=%SCRIPTS_DIR%\Main.ps1"
set "OUTPUT_EXE=%BUILD_DIR%\Query Store Analysis Utility.exe"
set "ICON_PATH=%WPF_DIR%\Assets\icons8-monster-ico.ico"
set "XAML_FILE=%SCRIPTS_DIR%\MainWindow.xaml"

set "SHORTCUT_NAME=Query Store Analysis Utility.lnk"
set "SHORTCUT_SOURCE=%BUILD_DIR%\%SHORTCUT_NAME%"
set "SHORTCUT_DEST=%PROJECT_ROOT%\%SHORTCUT_NAME%"

:: --- Kill EXE if running ---
taskkill /IM "Query Store Analysis Utility.exe" /F >nul 2>&1
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

:: --- Update Last Updated timestamp in XAML ---
echo.
echo === Updating Last Updated Timestamp ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$currentDate = Get-Date -Format 'yyyy-MM-dd';" ^
  "$xamlPath = '%XAML_FILE%';" ^
  "$content = Get-Content $xamlPath -Raw;" ^
  "$pattern = 'Last Updated: \d{4}-\d{2}-\d{2}';" ^
  "$replacement = \"Last Updated: $currentDate\";" ^
  "$newContent = $content -replace $pattern, $replacement;" ^
  "Set-Content -Path $xamlPath -Value $newContent -NoNewline;" ^
  "Write-Host \"Updated timestamp to: $currentDate\""

if errorlevel 1 (
    echo [WARNING] Failed to update timestamp in XAML file.
)

:: --- Compile PowerShell to EXE ---
echo.
echo === Compiling PowerShell to EXE ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Invoke-PS2EXE -InputFile '%PS_SCRIPT%' -OutputFile '%OUTPUT_EXE%' -iconFile '%ICON_PATH%' -noConsole -noOutput -STA"



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
  "$s.WorkingDirectory = '%BUILD_DIR%';" ^
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

:: --- Clear Windows Icon Cache ---
echo.
echo === Clearing Windows Icon Cache ===
echo Deleting icon cache to refresh EXE icon...
del /a /q "%localappdata%\IconCache.db" >nul 2>&1
del /a /q "%localappdata%\Microsoft\Windows\Explorer\iconcache_*.db" >nul 2>&1
echo Icon cache cleared. You may need to restart Explorer to see the new icon.

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo EXE Location: %OUTPUT_EXE%
echo Shortcut Location: %SHORTCUT_DEST%
echo.
echo NOTE: If the EXE icon doesn't update immediately:
echo   1. Close this window
echo   2. Run: Clear-Icon-Cache.bat
echo   3. Or restart Windows Explorer
echo.
pause
