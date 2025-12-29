import os
from pathlib import Path

try:
    import pyperclip
except ImportError:
    print("Installing required package 'pyperclip'...")
    os.system(f"{os.sys.executable} -m pip install pyperclip")
    import pyperclip

def prompt_directory():
    while True:
        user_input = input("Enter the full path to a directory: ").strip().strip('"')
        dir_path = Path(user_input).expanduser()
        if dir_path.is_dir():
            return dir_path
        print(f"❌ '{dir_path}' is not a valid directory. Please try again.\n")

def list_files_recursively(directory: Path):
    print(f"\n📂 Listing all files in: {directory}\n")
    file_paths = []
    for path in directory.rglob("*"):
        if path.is_file():
            print(path)
            file_paths.append(str(path))

    print(f"\n✅ Done. {len(file_paths)} file(s) found.")
    return file_paths

def copy_to_clipboard(file_list):
    text = "\n".join(file_list)
    pyperclip.copy(text)
    print("📋 File paths copied to clipboard.")

def main():
    dir_path = prompt_directory()
    files = list_files_recursively(dir_path)
    if files:
        copy_to_clipboard(files)
    else:
        print("⚠️ No files found. Nothing copied.")

if __name__ == "__main__":
    main()

    print('')
    print('')
    input('Press any key to continue')
    
    
    
    
