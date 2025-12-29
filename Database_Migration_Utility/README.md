# Basic Instructions

1) Install Python
    python -m pip install --upgrade pip
    python -m pip install colorama chardet firebird-driver psycopg2-binary

2) Install Firebird DB.
    Set the login and password in the following config after installing: "C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\script_executer_config.ini"

3) Install mssql-scripter
    https://github.com/microsoft/mssql-scripter




You may need to download the installation executable via Powershell, as I have had issues of it not downloading properly.

New-Item -ItemType Directory C:\Temp -Force | Out-Null
curl.exe -L "https://sourceforge.net/projects/firebird/files/v5.0.3/Firebird-5.0.3.1683-0-windows-x64.exe/download" `
  -o "C:\Temp\Firebird-5.0.3.1683-0-windows-x64.exe"

