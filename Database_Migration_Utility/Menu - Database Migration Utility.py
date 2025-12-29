import os
import subprocess
import sys
from colorama import init, Fore, Style
from pathlib import Path

init(autoreset=True)

# Constants
PYTHON_EXE = sys.executable
SCRIPT_PATH = r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\script_executer.py"
LOG_PATH = r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Logs"
ASCII_ART_PATH = r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\ascii_art.txt"

DELETE_PATHS = [
    r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Generated_Scripts",
    r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Logs",
    r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Output_Files",
    r"C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\SQL_Scripts"
]

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_ascii_art():
    if Path(ASCII_ART_PATH).exists():
        with open(ASCII_ART_PATH, 'r', encoding='utf-8') as file:
            print('')
            print('')
            print(Fore.CYAN + file.read())
    else:
        print(Fore.RED + "[ASCII ART NOT FOUND]\n")

def print_header():
    print_ascii_art()
    print(Fore.CYAN + "=" * 60)
    print("🚀  Welcome to the Database Migration Utility")
    print(Fore.CYAN + "=" * 60 + "\n")
    print(Fore.CYAN + "⚙️  Configuration Info:")
    print(Fore.WHITE + "   Insert source/target server details and credentials in the following Firebird DB:")
    print(Fore.WHITE + "   C:\Advanced_SQL_Server_Toolkit\Database_Migration_Utility\Core\Databases\DATABASE_MIGRATION_UTILITY_CONFIGURATION_DATABASE.FDB\n")

def print_contact_info():
    print(Fore.CYAN + "\n👤 Author: Scott Peters")
    print(Fore.CYAN + "📧 Email:  scottpeters1188@outlook.com")
    print(Fore.CYAN + "🌐 Site:   https://advancedsqlpuzzles.com")
    print(Fore.RED + "📖 Instructions coming soon...")
    
def run_script(arg, mode):
    print(Fore.CYAN + "🔧 Running script...\n")
    try:
        subprocess.run([PYTHON_EXE, SCRIPT_PATH, str(arg), mode])
    except Exception as e:
        print(Fore.RED + f"❌ Error running script: {e}")
    print(Fore.CYAN + f"\n📄 Logs available at: {LOG_PATH}\n")

def delete_folders():
    print(Fore.RED + "🗑️  Deleting generated folders...\n")
    for path in DELETE_PATHS:
        if os.path.exists(path):
            try:
                subprocess.run(['rmdir', '/s', '/q', path], shell=True)
                print(Fore.CYAN + f"✔ Deleted: {path}")
            except Exception as e:
                print(Fore.RED + f"❌ Failed to delete {path}: {e}")
        else:
            print(Fore.LIGHTBLACK_EX + f"(Skipped - Not Found): {path}")
    print()

def show_menu():
    print(Fore.CYAN + "📋 Menu Options:")
    print(Fore.WHITE + """
    🟦 First, identify the source system databases. 
    🟦 After importing, blacklist any databases listed in the IMPORT_DATABASE_INFORMATION table.
      ⚡ Databases  - Imports a list of the source system databases

    🟦 To generate only the DDL, run the following command.
      ⚡ DDL        - Generate DDL from source system

    🟦 Start the migration by executing the BUILD process.
      ⚡ Build      - Pre-deployment operations

    🟦 Once the BUILD process is complete, the objects can be deployed through the following methods:
      ⚡ Tables     - Deploy table DDL to the target system
      ⚡ Elements   - Deploy table elements (FKs, indexes, etc.)
      ⚡ All        - Deploy views, procedures, and functions

    🟦 Additional Options
      ⚡ Full       - Execute a build and deploy operation to the target system (useful for testing)
      ⚡ Delete     - Remove any folders created during the tool’s execution.

    Type 'exit' to quit the tool.
    """)
def main():
    while True:
        clear()
        print_contact_info()
        print_header()
        show_menu()
        choice = input(Fore.CYAN + "➡️  Enter your choice: ").strip().lower()
        print('')

        if choice == 'exit':
            print(Fore.MAGENTA + "\n👋 Exiting Database Migration Utility...")
            break
        elif choice == 'build':
            run_script(1, 'workflow')
        elif choice == 'ddl':
            run_script(6, 'workflow')
        elif choice == 'full':
            run_script(5, 'workflow')
        elif choice == 'delete':
            delete_folders()
        elif choice == 'tables':
            run_script(5, 'master')
        elif choice == 'elements':
            run_script(6, 'master')
        elif choice == 'all':
            run_script(7, 'master')
        elif choice == 'databases':
            run_script(7, 'workflow')  # ✅ new option added
        else:
            print(Fore.RED + f"❗ Invalid choice: {choice}")

        input(Fore.CYAN + "\n🔁 Press Enter to return to the menu...")


if __name__ == "__main__":
    main()
