"""
SQL Server System Catalog Extractor - Unified Configuration Utility

This utility manages both DMVs and Custom Queries as a unified configuration.
"""

import json
import os
import subprocess
import sys
import shutil
from pathlib import Path
from collections import defaultdict

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Script directory
SCRIPT_DIR = Path(__file__).parent





def display_ascii_art():
    """Display ASCII art from file at startup"""
    ascii_art_file = Path('Core/ascii_art.txt')
    if ascii_art_file.exists():
        try:
            with open(ascii_art_file, 'r', encoding='utf-8') as f:
                ascii_art = f.read()
            print(ascii_art)
        except Exception as e:
            # If we can't read the file, just continue without it
            pass


def load_dmv_config():
    """Load the DMV configuration file"""
    config_path = 'config/data_management_views_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def save_dmv_config(data):
    """Save the DMV configuration file"""
    config_path = 'config/data_management_views_config.json'
    with open(config_path, 'w') as f:
        json.dump(data, f, indent='\t')


def load_custom_queries_config():
    """Load the custom queries configuration file"""
    config_path = 'config/custom_queries.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_custom_queries_config(data):
    """Save the custom queries configuration file"""
    config_path = 'config/custom_queries.json'
    with open(config_path, 'w') as f:
        json.dump(data, f, indent='\t')


def load_server_config():
    """Load the SQL Server configuration file"""
    config_path = 'config/sql_server_connections.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def get_all_categories(dmv_data, cq_data):
    """Get all unique categories from both DMV and Custom Queries configs"""
    categories = set()
    
    # Get categories from DMVs
    for obj in dmv_data['data_management_objects']:
        cats = obj.get('category', [])
        if cats:
            for cat in cats:
                if cat:
                    categories.add(cat)
    
    # Get categories from Custom Queries
    if cq_data:
        for query in cq_data.get('custom_queries', []):
            cats = query.get('category', [])
            if cats:
                for cat in cats:
                    if cat:
                        categories.add(cat)
    
    return sorted(categories)


def get_items_by_category(dmv_data, cq_data):
    """Group both DMVs and Custom Queries by category (excludes DMFs)"""
    category_items = defaultdict(lambda: {'dmvs': [], 'queries': []})

    # Add DMVs (exclude DMFs - they require parameters and can't be extracted)
    for obj in dmv_data['data_management_objects']:
        # Skip DMFs
        if obj.get('object_type') == 'dmf':
            continue

        cats = obj.get('category', [])
        if cats:
            for cat in cats:
                if cat:
                    category_items[cat]['dmvs'].append(obj)

    # Add Custom Queries
    if cq_data:
        for query in cq_data.get('custom_queries', []):
            cats = query.get('category', [])
            if cats:
                for cat in cats:
                    if cat:
                        category_items[cat]['queries'].append(query)

    return category_items


def list_all_categories(dmv_data, cq_data):
    """List all available categories with item counts"""
    print('\n' + '=' * 80)
    print('📋 ALL CATEGORIES (DMVs + Custom Queries)')
    print('=' * 80)

    # Count DMFs for informational message
    dmf_count = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('object_type') == 'dmf')
    if dmf_count > 0:
        print(f'\nℹ️  Note: {dmf_count} DMFs (Dynamic Management Functions) are excluded.')
        print('   DMFs require parameters and cannot be extracted automatically.\n')

    category_items = get_items_by_category(dmv_data, cq_data)

    for i, (category, items) in enumerate(sorted(category_items.items()), 1):
        dmvs = items['dmvs']
        queries = items['queries']

        dmv_active = sum(1 for d in dmvs if d.get('isactive', False))
        query_active = sum(1 for q in queries if q.get('isactive', False))

        total_items = len(dmvs) + len(queries)
        total_active = dmv_active + query_active

        dmv_str = f"{len(dmvs)} DMVs" if dmvs else ""
        query_str = f"{len(queries)} Queries" if queries else ""

        if dmv_str and query_str:
            item_str = f"{dmv_str}, {query_str}"
        else:
            item_str = dmv_str or query_str

        print(f'{i:3}. {category:35} ({total_active}/{total_items} active - {item_str})')

    print('=' * 80)


def list_items_by_category(dmv_data, cq_data):
    """List all DMVs and Custom Queries grouped by category with descriptions"""
    print('\n' + '=' * 80)
    print('📋 ITEMS BY CATEGORY (DMVs + Custom Queries)')
    print('=' * 80)

    # Count DMFs for informational message
    dmf_count = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('object_type') == 'dmf')
    if dmf_count > 0:
        print(f'\nℹ️  Note: {dmf_count} DMFs are excluded from this list.')
        print('   DMFs require parameters and cannot be extracted automatically.')

    category_items = get_items_by_category(dmv_data, cq_data)
    categories = sorted(category_items.keys())
    
    print('\nAvailable categories:')
    for i, cat in enumerate(categories, 1):
        items = category_items[cat]
        total = len(items['dmvs']) + len(items['queries'])
        print(f'{i:3}. {cat} ({total} items)')
    
    print(f'{len(categories) + 1:3}. ALL CATEGORIES')
    
    choice = input('\nEnter category number (or press Enter to cancel): ').strip()
    
    if not choice:
        return
    
    try:
        choice_num = int(choice)
        
        if choice_num == len(categories) + 1:
            selected_categories = categories
        elif 1 <= choice_num <= len(categories):
            selected_categories = [categories[choice_num - 1]]
        else:
            print('❌ Invalid choice')
            return
    except ValueError:
        print('❌ Invalid input')
        return
    
    # Display items for selected categories
    for category in selected_categories:
        items = category_items[category]
        dmvs = sorted(items['dmvs'], key=lambda x: x['data_management_view'])
        queries = sorted(items['queries'], key=lambda x: x['query_name'])
        
        print(f'\n{"=" * 80}')
        print(f'Category: {category}')
        print(f'  DMVs: {len(dmvs)} | Custom Queries: {len(queries)}')
        print('=' * 80)
        
        # Display DMVs
        if dmvs:
            print('\n📊 DMVs:')
            print('-' * 80)
            for dmv in dmvs:
                status = '✓' if dmv.get('isactive', False) else '✗'
                obj_type = dmv.get('object_type', 'dmv').upper()
                print(f'  [{status}] {dmv["data_management_view"]} ({obj_type})')
                desc = dmv.get('description', 'No description')
                if len(desc) > 74:
                    desc = desc[:71] + '...'
                print(f'      {desc}')

        # Display Custom Queries
        if queries:
            print('\n📋 Custom Queries:')
            print('-' * 80)
            for query in queries:
                status = '✓' if query.get('isactive', False) else '✗'
                scope = query.get('execution_scope', 'unknown').upper()
                print(f'  [{status}] {query["query_name"]} (Scope: {scope})')
                print(f'      {query.get("description", "No description")}')
                print(f'      Table: {query.get("sqlite_table_name", "N/A")}')
    
    print('\n' + '=' * 80)


def activate_items_by_category(dmv_data, cq_data):
    """Activate or deactivate both DMVs and Custom Queries by category"""
    print('\n' + '=' * 80)
    print('⚙️  ACTIVATE/DEACTIVATE ITEMS BY CATEGORY')
    print('=' * 80)

    # Count DMFs for informational message
    dmf_count = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('object_type') == 'dmf')
    if dmf_count > 0:
        print(f'\nℹ️  Note: {dmf_count} DMFs will be excluded from activation.')
        print('   DMFs require parameters and cannot be extracted automatically.')

    category_items = get_items_by_category(dmv_data, cq_data)
    categories = sorted(category_items.keys())
    
    # Show categories
    print('\nAvailable categories:')
    for i, (cat, items) in enumerate(sorted(category_items.items()), 1):
        dmv_active = sum(1 for d in items['dmvs'] if d.get('isactive', False))
        query_active = sum(1 for q in items['queries'] if q.get('isactive', False))
        total_active = dmv_active + query_active
        total_items = len(items['dmvs']) + len(items['queries'])
        
        print(f'{i:3}. {cat:35} ({total_active}/{total_items} active)')
    
    print(f'\n{len(categories) + 1}. ALL CATEGORIES')
    print(f'{len(categories) + 2}. ALL ITEMS (ignore categories)')
    
    choice = input('\nEnter category number to activate/deactivate (or press Enter to cancel): ').strip()
    
    if not choice:
        return
    
    try:
        choice_num = int(choice)
        
        if choice_num == len(categories) + 1:
            selected_category = 'ALL_CATEGORIES'
        elif choice_num == len(categories) + 2:
            selected_category = 'ALL_ITEMS'
        elif 1 <= choice_num <= len(categories):
            selected_category = categories[choice_num - 1]
        else:
            print('❌ Invalid choice')
            return
    except ValueError:
        print('❌ Invalid input')
        return
    
    # Ask for action
    print('\nWhat would you like to do?')
    print('1. Activate (set isactive = true)')
    print('2. Deactivate (set isactive = false)')
    
    action = input('\nEnter choice (1 or 2): ').strip()
    
    if action not in ['1', '2']:
        print('❌ Invalid choice')
        return
    
    new_status = True if action == '1' else False
    status_text = 'ACTIVE' if new_status else 'INACTIVE'
    
    # Count affected items
    if selected_category == 'ALL_ITEMS':
        total_dmvs = len(dmv_data['data_management_objects'])
        total_queries = len(cq_data.get('custom_queries', [])) if cq_data else 0
        confirm_msg = f'Set ALL {total_dmvs} DMVs and {total_queries} Custom Queries to {status_text}?'
    elif selected_category == 'ALL_CATEGORIES':
        # Count items with categories
        dmv_count = sum(1 for obj in dmv_data['data_management_objects'] 
                       if obj.get('category') and any(c for c in obj.get('category', []) if c))
        query_count = 0
        if cq_data:
            query_count = sum(1 for q in cq_data.get('custom_queries', [])
                            if q.get('category') and any(c for c in q.get('category', []) if c))
        confirm_msg = f'Set {dmv_count} DMVs and {query_count} Custom Queries in ALL categories to {status_text}?'
    else:
        items = category_items.get(selected_category, {'dmvs': [], 'queries': []})
        dmv_count = len(items['dmvs'])
        query_count = len(items['queries'])
        confirm_msg = f'Set {dmv_count} DMVs and {query_count} Custom Queries in category "{selected_category}" to {status_text}?'
    
    confirm = input(f'\n{confirm_msg} (yes/no): ').strip().lower()
    
    if confirm not in ['yes', 'y']:
        print('❌ Operation cancelled.')
        return
    
    # Update DMVs and Custom Queries
    dmv_updated = 0
    query_updated = 0
    dmf_skipped = 0

    if selected_category == 'ALL_ITEMS':
        # Update all DMVs (skip DMFs)
        for obj in dmv_data['data_management_objects']:
            # Skip DMFs - they require parameters
            if obj.get('object_type') == 'dmf':
                dmf_skipped += 1
                continue

            obj['isactive'] = new_status
            dmv_updated += 1

        # Update all Custom Queries
        if cq_data:
            for query in cq_data.get('custom_queries', []):
                query['isactive'] = new_status
                query_updated += 1

    elif selected_category == 'ALL_CATEGORIES':
        # Update DMVs with categories (skip DMFs)
        for obj in dmv_data['data_management_objects']:
            # Skip DMFs - they require parameters
            if obj.get('object_type') == 'dmf':
                dmf_skipped += 1
                continue

            cats = obj.get('category', [])
            if cats and any(c for c in cats if c):
                obj['isactive'] = new_status
                dmv_updated += 1

        # Update Custom Queries with categories
        if cq_data:
            for query in cq_data.get('custom_queries', []):
                cats = query.get('category', [])
                if cats and any(c for c in cats if c):
                    query['isactive'] = new_status
                    query_updated += 1

    else:
        # Update DMVs in selected category (skip DMFs)
        for obj in dmv_data['data_management_objects']:
            # Skip DMFs - they require parameters
            if obj.get('object_type') == 'dmf':
                cats = obj.get('category', [])
                if selected_category in cats:
                    dmf_skipped += 1
                continue

            cats = obj.get('category', [])
            if selected_category in cats:
                obj['isactive'] = new_status
                dmv_updated += 1

        # Update Custom Queries in selected category
        if cq_data:
            for query in cq_data.get('custom_queries', []):
                cats = query.get('category', [])
                if selected_category in cats:
                    query['isactive'] = new_status
                    query_updated += 1

    # Save changes
    save_dmv_config(dmv_data)
    if cq_data and query_updated > 0:
        save_custom_queries_config(cq_data)

    print(f'\n✅ Configuration saved!')
    print(f'   - Updated {dmv_updated} DMVs to {status_text}')
    print(f'   - Updated {query_updated} Custom Queries to {status_text}')
    if dmf_skipped > 0:
        print(f'   - Skipped {dmf_skipped} DMFs (require parameters, cannot be activated)')


def list_sql_servers():
    """List all SQL Server configurations"""
    print('\n' + '=' * 80)
    print('📋 SQL SERVER CONFIGURATIONS')
    print('=' * 80)

    server_data = load_server_config()
    servers = server_data.get('servers', [])

    for i, server in enumerate(servers, 1):
        is_active = server.get('active', False)
        if is_active:
            status = f'{Colors.GREEN}✓ ACTIVE{Colors.RESET}'
        else:
            status = f'{Colors.RED}✗ INACTIVE{Colors.RESET}'

        print(f'\n🖥️ {server.get("servername", "Unknown")} [{status}]')
        print(f'   Port: {server.get("port", "N/A")}')
        print(f'   Username: {server.get("username", "N/A")}')
        print(f'   Password: {"*" * len(server.get("password", ""))}')

        databases_include = server.get('databases_include', [])
        if databases_include:
            print(f'   Databases: {", ".join(databases_include)}')
        else:
            print(f'   Databases: ALL (no filter)')

    print('\n' + '=' * 80)
    input('\nPress any key to continue...')


def show_statistics(dmv_data, cq_data):
    """Show combined statistics about DMV and Custom Queries configuration"""
    print('\n' + '=' * 80)
    print('📊 CONFIGURATION STATISTICS')
    print('=' * 80)

    # DMV Statistics
    total_dmvs = len(dmv_data['data_management_objects'])
    active_dmvs = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('isactive', False))
    inactive_dmvs = total_dmvs - active_dmvs

    dmv_count = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('object_type') == 'dmv')
    dmf_count = sum(1 for obj in dmv_data['data_management_objects'] if obj.get('object_type') == 'dmf')

    # DMF-specific statistics
    active_dmfs = sum(1 for obj in dmv_data['data_management_objects']
                     if obj.get('object_type') == 'dmf' and obj.get('isactive', False))

    # Custom Queries Statistics
    total_queries = 0
    active_queries = 0
    server_scope = 0
    database_scope = 0

    if cq_data:
        queries = cq_data.get('custom_queries', [])
        total_queries = len(queries)
        active_queries = sum(1 for q in queries if q.get('isactive', False))
        server_scope = sum(1 for q in queries if q.get('execution_scope') == 'server')
        database_scope = sum(1 for q in queries if q.get('execution_scope') == 'database')

    # Category Statistics
    categories = get_all_categories(dmv_data, cq_data)

    # Display
    print('\n📊 DMVs:')
    print(f'   Total Objects: {total_dmvs}')
    print(f'     - DMVs (Dynamic Management Views): {dmv_count}')
    print(f'     - DMFs (Dynamic Management Functions): {dmf_count}')
    if dmf_count > 0:
        print(f'       ⚠️  {active_dmfs} DMFs are currently active but will be skipped during extraction')
        print(f'       ℹ️  DMFs require parameters and cannot be extracted automatically')
    print(f'   Activation Status:')
    print(f'     - Active: {active_dmvs} ({active_dmvs/total_dmvs*100:.1f}%)')
    print(f'     - Inactive: {inactive_dmvs} ({inactive_dmvs/total_dmvs*100:.1f}%)')

    print('\n📋 Custom Queries:')
    print(f'   Total Queries: {total_queries}')
    if total_queries > 0:
        print(f'   Execution Scope:')
        print(f'     - Server-level: {server_scope}')
        print(f'     - Database-level: {database_scope}')
        print(f'   Activation Status:')
        print(f'     - Active: {active_queries} ({active_queries/total_queries*100:.1f}%)')
        print(f'     - Inactive: {total_queries - active_queries} ({(total_queries - active_queries)/total_queries*100:.1f}%)')

    print(f'\n📂 Categories:')
    print(f'   Total Categories: {len(categories)}')
    print(f'   Total Items: {total_dmvs + total_queries}')
    print(f'   Total Active: {active_dmvs + active_queries}')

    print('\n' + '=' * 80)






def execute_cleanup():
    """Execute cleanup based on cleanup configuration."""
    cleanup_config_file = SCRIPT_DIR / 'Config' / 'cleanup_config.json'

    if not cleanup_config_file.exists():
        print(f"\n❌ ERROR: Cleanup configuration file not found: {cleanup_config_file}")
        input("\nPress any key to continue...")
        return

    print("\n" + "="*80)
    print(f"🗑  EXECUTE CLEANUP")
    print("="*80)

    # Load cleanup configuration
    try:
        with open(cleanup_config_file, 'r', encoding='utf-8') as f:
            cleanup_config = json.load(f)
    except Exception as e:
        print(f"\n❌ ERROR: Could not read cleanup configuration: {e}")
        input("\nPress any key to continue...")
        return

    operations = cleanup_config.get('cleanup_operations', [])

    if not operations:
        print(f"\n⚠️  WARNING: No cleanup operations configured")
        input("\nPress any key to continue...")
        return

    # Show what will be deleted
    print("\n" + "="*80)
    print(f"⚠️  WARNING: The following will be deleted:")
    print("="*80)

    for operation in operations:
        path = operation.get('path', '')
        description = operation.get('description', '')
        action = operation.get('action', '')

        if action == 'delete_folder':
            print(f"\n📁️ DELETE ENTIRE FOLDER: {path}")
        elif action == 'delete_contents':
            print(f"\n📁 DELETE CONTENTS ONLY: {path}")

        print(f"   {description}")

    # Confirm
    print("\n" + "="*80)
    confirm = input(f'\n⚠️  Are you sure you want to proceed? (yes/no): ').strip().lower()

    if confirm not in ['yes', 'y']:
        print(f'\n❌ Operation cancelled.')
        input("\nPress any key to continue...")
        return

    # Perform cleanup
    print("\n" + "="*80)
    print(f"🗑️ PERFORMING CLEANUP...")
    print("="*80)

    deleted_count = 0
    error_count = 0

    for operation in operations:
        path_str = operation.get('path', '')
        action = operation.get('action', '')

        path = Path(path_str)

        try:
            if action == 'delete_folder':
                # Delete entire folder
                if path.exists():
                    shutil.rmtree(path)
                    print(f"✅ Deleted folder: {path}")
                    deleted_count += 1
                else:
                    print(f"ℹ️  Folder does not exist (already deleted): {path}")

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
                    print(f"✅ Deleted {items_deleted} item(s) from: {path}")
                    deleted_count += items_deleted
                else:
                    print(f"ℹ️  Folder does not exist: {path}")

        except Exception as e:
            print(f"❌ Error processing {path}: {e}")
            error_count += 1

    print("\n" + "="*80)
    print(f"✅ Cleanup completed!")
    print(f"   Items deleted: {deleted_count}")
    if error_count > 0:
        print(f"   ⚠️  Errors: {error_count}")
    print("="*80)

    input("\nPress any key to continue...")


def execute_system_catalog_extractor():
    """Execute all Core scripts in order"""
    
    # Display active servers
    print('\n' + '=' * 80)
    print('📋 ACTIVE SQL SERVER CONFIGURATIONS')
    print('=' * 80)
    
    server_data = load_server_config()
    servers = server_data.get('servers', [])
    active_servers = [s for s in servers if s.get('active', False)]
    
    if not active_servers:
        print('\nNo active servers found.')
        input('\nPress any key to continue...')
        return
    
    for i, server in enumerate(active_servers, 1):
        print(f'\n🖥️ {server.get("servername", "Unknown")}')
        print(f'   Port: {server.get("port", "N/A")}')
        print(f'   Username: {server.get("username", "N/A")}')
        
        databases_include = server.get('databases_include', [])
        if databases_include:
            print(f'   Databases: {", ".join(databases_include)}')
        else:
            print(f'   Databases: ALL (no filter)')
    
    print('\n' + '=' * 80)

    # Ask for confirmation
    confirm = input('\n⚠️  Are you sure you want to proceed? (yes/no): ').strip().lower()

    if confirm not in ('yes', 'y'):
        print('\n❌ Operation cancelled.')
        input('\nPress any key to continue...')
        return

    # Define scripts in execution order
    scripts = [
        'Core/0100_delete_tables.py',
        'Core/0200_etl_system_catalog.py',
        'Core/0300_etl_custom_queries.py',
        'Core/0400_etl_summary_statistics.py',
    ]

    print(f'\n⏳ Processing...')

    # Execute each script
    for script in scripts:
        script_path = Path(script)
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f'Error executing {script}')
                input('\nPress any key to continue...')
                return
        except Exception as e:
            print(f'Error executing {script}: {e}')
            input('\nPress any key to continue...')
            return

    print('\n✅ Your SQLite database is ready at:')
    print('   C:\\Advanced_SQL_Server_Toolkit\\System_Catalog_Extractor\\SQLite\\sqlite_system_catalog_output.db')
    print('\n📋 Please check the log files for details')
    input('\nPress any key to continue...')


def main_menu():
    """Display main menu and handle user choices"""
    # Display ASCII art on first iteration
    first_run = True
    
    while True:
        if first_run:
            display_ascii_art()
            first_run = False
        

        print('\n' + '=' * 80)
        print(f'{Colors.BLUE}SQL SERVER SYSTEM CATALOG EXTRACTOR UTILITY{Colors.RESET}')
        print('=' * 80)
        print()
        print('\n❗  Modify the following JSON files to specify which tables should be imported.')
        print(r'   • C:\Advanced_SQL_Server_Toolkit\System_Catalog_Extractor\Config\data_management_views_config.json')
        print(r'   • C:\Advanced_SQL_Server_Toolkit\System_Catalog_Extractor\Config\custom_queries.json')
        print()
        print('\n1. 📝  List SQL Server Configurations')
        print('   • Lists the configurations specified in the sql_server_connections.json file')
        print('\n2. 🚀  Execute System Catalog Extractor')
        print('   • Executes the System Catalog Extractor and imports the results into an SQLite database')
        print(r'   • C:\Advanced_SQL_Server_Toolkit\System_Catalog_Extractor\SQLite\sqlite_system_catalog_output.db')
        print('\n3. 🗑️  Clean Workspace')
        print('   • Deletes folders and files as defined in the cleanup_config.json file')
        print('\n4. 🚪  Exit')
        print('   • Closes the application')
        print()

        choice = input('Enter your choice (1-4): ').strip()

        dmv_data = load_dmv_config()
        cq_data = load_custom_queries_config()

        if choice == '99':
            activate_items_by_category(dmv_data, cq_data)
        elif choice == '98':
            list_all_categories(dmv_data, cq_data)
        elif choice == '97':
            list_items_by_category(dmv_data, cq_data)
        elif choice == '96':
            show_statistics(dmv_data, cq_data)
        elif choice == '1':
            list_sql_servers()
        elif choice == '2':
            execute_system_catalog_extractor()
        elif choice == '3':
            execute_cleanup()
        elif choice == '4':
            print('\n👋 Goodbye!')
            break
        else:
            print('\n❌ Invalid choice. Please enter 1-8.')


if __name__ == '__main__':
    main_menu()


