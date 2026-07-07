@echo off
echo ========================================
echo Clear Windows Icon Cache
echo ========================================
echo.
echo This will clear the Windows icon cache to refresh EXE icons.
echo You may need to restart Explorer or log off/on to see changes.
echo.
pause

echo.
echo Stopping Windows Explorer...
taskkill /f /im explorer.exe

echo.
echo Deleting icon cache files...

:: Delete icon cache database files
del /a /q "%localappdata%\IconCache.db" 2>nul
del /a /q "%localappdata%\Microsoft\Windows\Explorer\iconcache_*.db" 2>nul

echo.
echo Restarting Windows Explorer...
start explorer.exe

echo.
echo ========================================
echo Icon cache cleared successfully!
echo ========================================
echo.
echo If the icon still doesn't update, try:
echo 1. Log off and log back on
echo 2. Restart your computer
echo.
pause

