"""
Launch All UIs - Advanced SQL Server Toolkit
=============================================
This script launches all WPF UI applications in the Advanced SQL Server Toolkit.

Author: Advanced SQL Server Toolkit
Last Modified: 2026-03-21
"""

import subprocess
import sys
import logging
from pathlib import Path
import time
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def launch_ui(name: str, script_path: Path) -> bool:
    """
    Launch a WPF UI application.

    Args:
        name: Display name of the utility
        script_path: Path to the Main.ps1 script

    Returns:
        bool: True if launch was successful, False otherwise
    """
    logger.info(f"Launching {name}...")

    try:
        # Launch PowerShell script in a new window
        subprocess.Popen(
            [
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-NoProfile',
                '-File', str(script_path)
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        logger.info(f"✓ {name} launched successfully")
        return True
    except FileNotFoundError:
        logger.error(f"✗ PowerShell not found. Is PowerShell installed?")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to launch {name}: {e}")
        return False

def main():
    """Main function to launch all UIs."""
    print("=" * 70)
    print("Advanced SQL Server Toolkit - Launch All UIs")
    print("=" * 70)
    print()
    
    # Define the toolkit root directory (parent of XTools)
    toolkit_root = Path(__file__).parent.parent
    
    # Define all WPF UI utilities
    utilities = [
        {
            'name': 'Database Normalization Analysis Utility',
            'path': toolkit_root / 'Database_Normalization_Analysis_Utility' / 'Core' / 'WPF' / 'Scripts' / 'Main.ps1'
        },
        {
            'name': 'Database Object Dependency Utility',
            'path': toolkit_root / 'Database_Object_Dependency_Utility' / 'Core' / 'WPF' / 'Scripts' / 'Main.ps1'
        },
        {
            'name': 'Execution Plan Analysis Utility',
            'path': toolkit_root / 'Execution_Plan_Analysis_Utility' / 'Core' / 'WPF' / 'Scripts' / 'Main.ps1'
        },
        {
            'name': 'Query Store Analysis Utility',
            'path': toolkit_root / 'Query_Store_Analysis_Utility' / 'Core' / 'WPF' / 'Scripts' / 'Main.ps1'
        }
    ]
    
    # Track results
    launched = 0
    failed = 0
    
    # Launch each utility
    for utility in utilities:
        if not utility['path'].exists():
            print(f"[ERROR] Script not found: {utility['path']}")
            failed += 1
            continue
        
        if launch_ui(utility['name'], utility['path']):
            launched += 1
            # Small delay between launches to avoid overwhelming the system
            time.sleep(1)
        else:
            failed += 1
    
    # Summary
    print()
    print("=" * 70)
    print("Launch Summary")
    print("=" * 70)
    print(f"Successfully launched: {launched}")
    print(f"Failed to launch:      {failed}")
    print(f"Total utilities:       {len(utilities)}")
    print()
    
    if launched > 0:
        print("[INFO] All UIs have been launched in separate windows.")
        print("[INFO] You can now interact with each utility independently.")
    
    if failed > 0:
        print("[WARN] Some utilities failed to launch. Check the error messages above.")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Launch cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

