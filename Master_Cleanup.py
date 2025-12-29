"""
Master Cleanup Script for Advanced SQL Server Toolkit
Finds and executes all cleanup_config.json files across utilities
"""

import json
import shutil
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def find_cleanup_configs():
    """Find all cleanup_config.json files in the toolkit."""
    base_dir = Path(__file__).parent
    cleanup_configs = []
    
    # Define the utilities to search
    utilities = [
        'BabelfishCompass_Utility',
        'DDL_Generator_Utility',
        'Execution_Plan_Analysis_Utility',
        'System_Catalog_Extractor_Utility'
    ]
    
    for utility in utilities:
        config_file = base_dir / utility / 'Config' / 'cleanup_config.json'
        if config_file.exists():
            cleanup_configs.append({
                'utility': utility,
                'config_file': config_file
            })
    
    return cleanup_configs


def load_cleanup_config(config_file):
    """Load a cleanup configuration file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}❌ Error loading {config_file}: {e}{Colors.RESET}")
        return None


def display_all_operations(cleanup_configs):
    """Display all cleanup operations from all utilities."""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  WARNING: The following will be deleted:{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    total_operations = 0
    
    for config_info in cleanup_configs:
        utility = config_info['utility']
        config_data = load_cleanup_config(config_info['config_file'])
        
        if not config_data:
            continue
        
        operations = config_data.get('cleanup_operations', [])
        
        if operations:
            print(f"{Colors.BLUE}📦 {utility}{Colors.RESET}")
            print(f"{Colors.CYAN}{'-'*80}{Colors.RESET}")
            
            for operation in operations:
                path = operation.get('path', '')
                description = operation.get('description', '')
                action = operation.get('action', '')
                
                if action == 'delete_folder':
                    print(f"  {Colors.RED}🗑️  DELETE ENTIRE FOLDER:{Colors.RESET} {path}")
                elif action == 'delete_contents':
                    print(f"  {Colors.YELLOW}📂 DELETE CONTENTS ONLY:{Colors.RESET} {path}")
                
                print(f"     {description}")
                print()
                total_operations += 1
            
            print()
    
    return total_operations


def perform_cleanup(cleanup_configs):
    """Execute cleanup operations for all utilities."""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}🗑️  PERFORMING CLEANUP...{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    total_deleted = 0
    total_errors = 0
    
    for config_info in cleanup_configs:
        utility = config_info['utility']
        config_data = load_cleanup_config(config_info['config_file'])
        
        if not config_data:
            continue
        
        operations = config_data.get('cleanup_operations', [])
        
        if operations:
            print(f"{Colors.BLUE}📦 Processing {utility}...{Colors.RESET}")
            
            for operation in operations:
                path_str = operation.get('path', '')
                action = operation.get('action', '')
                path = Path(path_str)
                
                try:
                    if action == 'delete_folder':
                        # Delete entire folder
                        if path.exists():
                            shutil.rmtree(path)
                            print(f"  {Colors.GREEN}✅ Deleted folder: {path}{Colors.RESET}")
                            total_deleted += 1
                        else:
                            print(f"  {Colors.YELLOW}ℹ️  Folder does not exist (already deleted): {path}{Colors.RESET}")
                    
                    elif action == 'delete_contents':
                        # Delete only contents
                        if path.exists():
                            items_deleted = 0
                            for item in path.iterdir():
                                if item.is_file():
                                    item.unlink()
                                    items_deleted += 1
                                elif item.is_dir():
                                    shutil.rmtree(item)
                                    items_deleted += 1
                            print(f"  {Colors.GREEN}✅ Deleted {items_deleted} item(s) from: {path}{Colors.RESET}")
                            total_deleted += items_deleted
                        else:
                            print(f"  {Colors.YELLOW}ℹ️  Folder does not exist: {path}{Colors.RESET}")
                
                except Exception as e:
                    print(f"  {Colors.RED}❌ Error processing {path}: {e}{Colors.RESET}")
                    total_errors += 1
            
            print()
    
    return total_deleted, total_errors


def main():
    """Main function."""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}MASTER CLEANUP - ADVANCED SQL SERVER TOOLKIT{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
    
    # Find all cleanup configurations
    cleanup_configs = find_cleanup_configs()
    
    if not cleanup_configs:
        print(f"\n{Colors.RED}❌ No cleanup configuration files found{Colors.RESET}")
        return
    
    print(f"\n{Colors.GREEN}✅ Found {len(cleanup_configs)} cleanup configuration(s):{Colors.RESET}")
    for config_info in cleanup_configs:
        print(f"   • {config_info['utility']}")
    
    # Display all operations
    total_operations = display_all_operations(cleanup_configs)
    
    if total_operations == 0:
        print(f"\n{Colors.YELLOW}⚠️  No cleanup operations configured{Colors.RESET}")
        return
    
    # Confirm
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
    confirm = input(f'\n{Colors.YELLOW}⚠️  Are you sure you want to proceed? (yes/no): {Colors.RESET}').strip().lower()
    
    if confirm not in ['yes', 'y']:
        print(f'\n{Colors.RED}❌ Operation cancelled.{Colors.RESET}')
        return
    
    # Perform cleanup
    total_deleted, total_errors = perform_cleanup(cleanup_configs)
    
    # Summary
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ Cleanup completed!{Colors.RESET}")
    print(f"   Items deleted: {total_deleted}")
    if total_errors > 0:
        print(f"   {Colors.RED}Errors: {total_errors}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    input("Press any key to continue...")


if __name__ == "__main__":
    main()

