"""
Print All Markdown Files
=========================
Finds all markdown (.md) files in the Advanced SQL Server Toolkit
and prints their contents to the screen.

Author: Advanced SQL Server Toolkit
"""

from pathlib import Path
import sys


def find_markdown_files(base_dir):
    """
    Find all markdown files in the toolkit.
    
    Args:
        base_dir: Base directory to search from
        
    Returns:
        List of Path objects for markdown files
    """
    markdown_files = []
    
    for md_file in base_dir.rglob('*.md'):
        # Skip files in node_modules, .git, etc.
        if any(part.startswith('.') or part == 'node_modules' for part in md_file.parts):
            continue
        markdown_files.append(md_file)
    
    return sorted(markdown_files)


def print_markdown_file(file_path, base_dir):
    """
    Print the contents of a markdown file.
    
    Args:
        file_path: Path to the markdown file
        base_dir: Base directory for relative path display
    """
    relative_path = file_path.relative_to(base_dir)
    
    print("\n" + "=" * 80)
    print(f"FILE: {relative_path}")
    print("=" * 80)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"ERROR: Failed to read file: {e}")
    
    print("\n" + "-" * 80)


def main():
    """Main function to find and print all markdown files."""

    # Get toolkit root directory (parent of XTools)
    toolkit_root = Path(__file__).parent.parent

    print("=" * 80)
    print("ADVANCED SQL SERVER TOOLKIT - MARKDOWN FILE PATHS")
    print("=" * 80)
    print(f"\nSearching for markdown files in: {toolkit_root}")
    print()

    # Find all markdown files
    markdown_files = find_markdown_files(toolkit_root)

    if not markdown_files:
        print("No markdown files found.")
        return

    print(f"Found {len(markdown_files)} markdown file(s):\n")

    # Print all file paths
    for i, md_file in enumerate(markdown_files, 1):
        relative_path = md_file.relative_to(toolkit_root)
        print(f"  {i}. {relative_path}")

    print("\n" + "=" * 80)
    print(f"COMPLETE - Found {len(markdown_files)} markdown file(s)")
    print("=" * 80)

    # Pause before closing
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

