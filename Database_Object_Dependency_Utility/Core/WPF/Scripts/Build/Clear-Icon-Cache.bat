@echo off
echo Clearing Windows Icon Cache...
echo.

:: Stop Windows Explorer
taskkill /f /im explorer.exe

:: Delete icon cache files
del /a /q "%localappdata%\IconCache.db" 2>nul
del /a /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*" 2>nul

:: Wait a moment
timeout /t 2 /nobreak >nul

:: Restart Windows Explorer
start explorer.exe

echo.
echo Icon cache cleared! Please rebuild your EXE now.
echo.
pause

