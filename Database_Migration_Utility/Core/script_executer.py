from firebird.driver import connect, DatabaseError
import logging
import sys
import argparse
import tempfile
import subprocess
import os
import configparser
from pathlib import Path

# === Load Configuration ===
def load_config():
    """Load configuration from script_executer_config.ini"""
    script_path = Path(__file__).resolve().parent
    config_path = script_path / "script_executer_config.ini"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

# Load config
config = load_config()

# === Extract Configuration Values ===
# Paths
log_dir = config.get("Paths", "LOG_DIR")
db_path = config.get("Paths", "DB_PATH")

# Database
db_user = config.get("Database", "DB_USER")
db_password = config.get("Database", "DB_PASSWORD")
db_charset = config.get("Database", "DB_CHARSET")
admin_user = config.get("Database", "ADMIN_USER", fallback="").strip()

# Logging
log_file_name = config.get("Logging", "LOG_FILE_NAME")
log_level_str = config.get("Logging", "LOG_LEVEL", fallback="INFO")
log_format = config.get("Logging", "LOG_FORMAT")
log_file_mode = config.get("Logging", "LOG_FILE_MODE", fallback="a")

# PowerShell
ps_executable = config.get("PowerShell", "PS_EXECUTABLE", fallback="powershell")
execution_policy = config.get("PowerShell", "EXECUTION_POLICY", fallback="Bypass")
delete_temp_scripts = config.getboolean("PowerShell", "DELETE_TEMP_SCRIPTS", fallback=True)

# Execution
continue_on_error = config.getboolean("Execution", "CONTINUE_ON_ERROR", fallback=False)

# Database Queries
master_views_table = config.get("Database_Queries", "MASTER_VIEWS_TABLE", fallback="repository_powershell_master_views")
python_script_table = config.get("Database_Queries", "PYTHON_SCRIPT_TABLE", fallback="repository_python_script_detail")
workflows_table = config.get("Database_Queries", "WORKFLOWS_TABLE", fallback="repository_workflows")
master_view_id_column = config.get("Database_Queries", "MASTER_VIEW_ID_COLUMN", fallback="powershellmasterviewsid")
python_script_id_column = config.get("Database_Queries", "PYTHON_SCRIPT_ID_COLUMN", fallback="pythonscriptsummaryid")
workflow_id_column = config.get("Database_Queries", "WORKFLOW_ID_COLUMN", fallback="workflowssummaryid")

# Advanced
validate_syntax = config.getboolean("Advanced", "VALIDATE_SYNTAX", fallback=True)
script_encoding = config.get("Advanced", "SCRIPT_ENCODING", fallback="utf-8")
temp_file_suffix = config.get("Advanced", "TEMP_FILE_SUFFIX", fallback=".ps1")

# === Ensure Logs Folder Exists ===
os.makedirs(log_dir, exist_ok=True)

# === Logging Configuration ===
log_file = os.path.join(log_dir, log_file_name)
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format=log_format,
    filemode=log_file_mode
)

# === Argument Parser ===
parser = argparse.ArgumentParser(description="Run dynamic script or master operation based on execution type.")
parser.add_argument("execution_id", type=int, help="The execution_id to execute")
parser.add_argument("execution_type", choices=["script", "master", "workflow"], help="Execution type: 'script', 'master', 'workflow'")
parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments to pass to the script (only for 'script')")

args = parser.parse_args()
execution_id = args.execution_id
execution_type = args.execution_type
script_args = args.script_args

logging.info(f"Running from Python: {sys.executable}")
logging.info(f"Using execution_id: {execution_id}")
logging.info(f"Execution type: {execution_type}")
logging.info(f"Script arguments: {script_args}")

try:
    # For local database file, simply use the file path
    # The firebird-driver will use embedded server by default
    conn = connect(
        database=db_path,
        user=db_user,
        password=db_password,
        charset=db_charset
    )

    # If using admin user, activate the admin role
    if admin_user and db_user.lower() == admin_user.lower():
        conn.execute_immediate("SET ROLE RDB$ADMIN")
        conn.commit()

    cursor = conn.cursor()
# summary_id
    if execution_type == "master":
        master_id = execution_id
        logging.info(f"Using master_id: {master_id}")
        cursor.execute(f"""
            SELECT viewname
            FROM {master_views_table}
            WHERE {master_view_id_column} = ?
        """, (master_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No view found for {master_view_id_column} = {master_id}")
        view_name = row[0]
        logging.info(f"Retrieved view name: {view_name}")
        cursor.execute(f"SELECT DISTINCT filename FROM {view_name}")
        filenames = cursor.fetchall()
        if not filenames:
            logging.info("No filenames found.")
            sys.exit(0)

        for (filename,) in filenames:
            logging.info(f"Processing filename: {filename}")
            cursor.execute(f"""
                SELECT command
                FROM {view_name}
                WHERE filename = ?
                ORDER BY filename, ordertype, rowid
            """, (filename,))
            command_rows = cursor.fetchall()
            if not command_rows:
                logging.info(f"No command found for {filename}")
                continue
            ps_script = "\n".join([row[0] for row in command_rows])
            with tempfile.NamedTemporaryFile(delete=False, suffix=temp_file_suffix, mode="w", encoding=script_encoding) as ps_file:
                ps_file.write(ps_script)
                temp_script_path = ps_file.name
            try:
                subprocess.run([ps_executable, "-ExecutionPolicy", execution_policy, "-File", temp_script_path], check=True)
                logging.info(f"Successfully executed PowerShell for {filename}")
            except subprocess.CalledProcessError as e:
                logging.error(f"PowerShell failed for {filename}: {e}")
                if not continue_on_error:
                    raise
            finally:
                if delete_temp_scripts:
                    os.remove(temp_script_path)
        sys.exit(0)

    elif execution_type == "script":
        script_id = execution_id
        logging.info(f"Using script_id: {script_id}")
        cursor.execute(f"""
            SELECT scripttext
            FROM {python_script_table}
            WHERE {python_script_id_column} = ?
            ORDER BY linenumber ASC
        """, (script_id,))
        rows = cursor.fetchall()
        if not rows:
            raise ValueError(f"No script found for {python_script_id_column} = {script_id}")
        script_lines = [row[0] for row in rows]
        full_script = "\n".join(script_lines)
        if validate_syntax:
            logging.info("Script retrieved. Checking syntax.")
            compiled = compile(full_script, '<dynamic_script>', 'exec')
        else:
            compiled = compile(full_script, '<dynamic_script>', 'exec')
        original_argv = sys.argv
        sys.argv = ['dynamic_script.py'] + script_args
        logging.info("Executing script.")
        exec(compiled)
        sys.argv = original_argv

    elif execution_type == "workflow":
        workflow_id = execution_id
        logging.info(f"Using workflow_id: {workflow_id}")
        cursor.execute(f"""
            SELECT viewname
            FROM {workflows_table}
            WHERE {workflow_id_column} = ?
                  AND isactive = 1
            ORDER BY workflowsequence ASC
        """, (workflow_id,))
        view_rows = cursor.fetchall()
        if not view_rows:
            raise ValueError(f"No workflow views found for {workflow_id_column} = {workflow_id}")

        for (view_name,) in view_rows:
            logging.info(f"Processing workflow view: {view_name}")
            cursor.execute(f"SELECT DISTINCT filename FROM {view_name}")
            filenames = cursor.fetchall()
            if not filenames:
                logging.info(f"No filenames found in view {view_name}")
                continue

            for (filename,) in filenames:
                logging.info(f"Processing filename: {filename}")
                cursor.execute(f"""
                    SELECT command
                    FROM {view_name}
                    WHERE filename = ?
                    ORDER BY filename, ordertype, rowid
                """, (filename,))
                command_rows = cursor.fetchall()
                if not command_rows:
                    logging.info(f"No Workflow command found for {filename} in view {view_name}")
                    continue
                wf_script = "\n".join([row[0] for row in command_rows])
                with tempfile.NamedTemporaryFile(delete=False, suffix=temp_file_suffix, mode="w", encoding=script_encoding) as ps_file:
                    ps_file.write(wf_script)
                    temp_script_path = ps_file.name
                try:
                    subprocess.run([ps_executable, "-ExecutionPolicy", execution_policy, "-File", temp_script_path], check=True)
                    logging.info(f"Successfully executed PowerShell for {filename} from view {view_name}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"PowerShell failed for {filename} from view {view_name}: {e}")
                    if not continue_on_error:
                        raise
                finally:
                    if delete_temp_scripts:
                        os.remove(temp_script_path)
        sys.exit(0)

except DatabaseError as db_err:
    logging.error(f"Firebird DB error: {db_err}")
except SyntaxError as syn_err:
    logging.error(f"Syntax error in script: {syn_err}")
    if syn_err.text:
        logging.error(f"Line {syn_err.lineno}: {syn_err.text.strip()}")
except Exception as e:
    logging.error(f"General error: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
        logging.info("Firebird connection closed.")