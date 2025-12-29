import os
import shutil
import stat
from pathlib import Path

# List of folders to delete
FOLDERS_TO_DELETE = [
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Generated_Scripts"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Logs"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Output_Files"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\SQL_Scripts"),
    
    
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Utilities\Export_Scripts\Exported_Scripts"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Utilities\Export_Scripts\Generated_Firebird_DDL"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Utilities\Export_Scripts\Logs"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Utilities\Import_Scripts\Logs"),
    Path(r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Utilities\Import_Scripts\Output")
]


def _onerror_make_writable(func, path, exc_info):
    """
    onerror handler for shutil.rmtree to handle read-only files:
    try to chmod to writable, then retry the failed operation once.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # If it still fails, re-raise the original error
        raise

def delete_folder(p: Path):
    if p.exists():
        try:
            shutil.rmtree(p, onerror=_onerror_make_writable)
            print(f"Deleted: {p}")
        except Exception as e:
            print(f"Error deleting {p}: {e}")
    else:
        print(f"Folder not found: {p}")

def main():
    for folder in FOLDERS_TO_DELETE:
        delete_folder(folder)

    print('')
    print('')
    input("\nPress any key to continue...")

if __name__ == "__main__":
    main()
