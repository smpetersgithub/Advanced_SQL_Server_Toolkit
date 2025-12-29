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
set "OUTPUT_EXE=%BUILD_DIR%\Execution Plan Analysis Utility.exe"
set "ICON_PATH=%WPF_DIR%\Assets\icons8-communication-64.ico"
set "XAML_FILE=%SCRIPTS_DIR%\MainWindow.xaml"

set "SHORTCUT_NAME=Execution Plan Analysis Utility.lnk"
set "SHORTCUT_SOURCE=%BUILD_DIR%\%SHORTCUT_NAME%"
set "SHORTCUT_DEST=%PROJECT_ROOT%\%SHORTCUT_NAME%"

:: --- Kill EXE if running ---
taskkill /IM "Execution Plan Analysis Utility.exe" /F >nul 2>&1
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
echo Build complete!
pause
