"""
Find Folders Script - Advanced SQL Server Toolkit
==================================================
This script searches for specific folder names (Output, Logs, .idea) 
and prints their paths to the console.

Author: Advanced SQL Server Toolkit
Last Modified: 2026-03-21
"""

import logging
import sys
import shutil
from pathlib import Path
from typing import List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def find_folders(root_dir: Path, folder_names: Set[str]) -> List[Path]:
    """
    Recursively find all folders with specific names.
    
    Args:
        root_dir: Root directory to start searching from
        folder_names: Set of folder names to search for
        
    Returns:
        List of paths to matching folders
    """
    found_folders = []
    
    logger.info(f"Searching for folders: {', '.join(folder_names)}")
    logger.info(f"Starting from: {root_dir}")
    logger.info("=" * 70)
    
    try:
        for item in root_dir.rglob('*'):
            if item.is_dir() and item.name in folder_names:
                found_folders.append(item)
                logger.info(f"Found: {item}")
    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Error during search: {e}")
    
    return found_folders


def delete_folders(folders: List[Path]) -> tuple[int, int]:
    """
    Delete the specified folders.

    Args:
        folders: List of folder paths to delete

    Returns:
        Tuple of (successful_deletions, failed_deletions)
    """
    successful = 0
    failed = 0

    logger.info("")
    logger.info(f"{Colors.YELLOW}Starting deletion process...{Colors.RESET}")
    logger.info("")

    for i, folder in enumerate(folders, 1):
        try:
            logger.info(f"[{i}/{len(folders)}] Deleting: {folder}")
            shutil.rmtree(folder)
            logger.info(f"{Colors.GREEN}✓ Successfully deleted: {folder.name}{Colors.RESET}")
            successful += 1
        except PermissionError:
            logger.error(f"{Colors.RED}✗ Permission denied: {folder}{Colors.RESET}")
            failed += 1
        except Exception as e:
            logger.error(f"{Colors.RED}✗ Failed to delete {folder}: {e}{Colors.RESET}")
            failed += 1

    return successful, failed


def main() -> None:
    """Main function to find and display folder paths."""
    logger.info("=" * 70)
    logger.info("Advanced SQL Server Toolkit - Find Folders")
    logger.info("=" * 70)
    logger.info("")

    # Define the toolkit root directory (parent of XTools)
    toolkit_root = Path(__file__).parent.parent

    # Define folder names to search for
    target_folders = {'Output', 'Logs', '.idea', '__pycache__'}

    # Find all matching folders
    found_folders = find_folders(toolkit_root, target_folders)

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("Search Summary")
    logger.info("=" * 70)
    logger.info(f"Total folders found: {len(found_folders)}")

    # Group by folder name
    for folder_name in target_folders:
        count = sum(1 for f in found_folders if f.name == folder_name)
        logger.info(f"  - {folder_name}: {count}")

    # Ask user if they want to delete
    if found_folders:
        logger.info("")
        logger.info(f"{Colors.BOLD}{Colors.YELLOW}{'=' * 70}{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{Colors.RED}WARNING: This will permanently delete {len(found_folders)} folder(s)!{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{Colors.YELLOW}{'=' * 70}{Colors.RESET}")
        logger.info("")

        response = input(f"{Colors.YELLOW}Do you want to delete these folders? (yes/no): {Colors.RESET}").strip().lower()

        if response in ['yes', 'y']:
            successful, failed = delete_folders(found_folders)

            # Deletion summary
            logger.info("")
            logger.info("=" * 70)
            logger.info("Deletion Summary")
            logger.info("=" * 70)
            logger.info(f"{Colors.GREEN}Successfully deleted: {successful}{Colors.RESET}")
            if failed > 0:
                logger.info(f"{Colors.RED}Failed to delete:     {failed}{Colors.RESET}")
            logger.info(f"Total processed:      {len(found_folders)}")
        else:
            logger.info(f"{Colors.CYAN}Deletion cancelled by user.{Colors.RESET}")
    else:
        logger.info(f"{Colors.CYAN}No folders to delete.{Colors.RESET}")

    logger.info("")
    input("Press Enter to exit...")


if __name__ == '__main__':
    main()

