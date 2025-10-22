#!/usr/bin/env python3
"""
Simple Data Export Script for Hotel Management System

This script exports your current database to SQL files that can be imported
into your new Docker deployment.

Usage:
1. Make sure you have MySQL client installed
2. Set your database environment variables (or edit the script)
3. Run: python export_data.py
4. The script will create SQL dump files in the current directory
"""

import os
import subprocess
from datetime import datetime

def get_db_config():
    """Get database configuration - modify these values if needed"""
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '3306'),
        'name': os.environ.get('DB_NAME', 'temp'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),  # Set your password here if not using env var
    }

def export_database():
    """Export the complete database"""
    db_config = get_db_config()
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export complete database
    complete_filename = f"hotel_db_export_{timestamp}.sql"
    
    cmd = [
        'mysqldump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--user={db_config["user"]}',
        f'--password={db_config["password"]}' if db_config["password"] else f'--user={db_config["user"]}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--complete-insert',
        db_config['name']
    ]
    
    # Remove empty password argument if no password is set
    if not db_config["password"]:
        cmd = [arg for arg in cmd if not arg.startswith('--password')]
    
    try:
        with open(complete_filename, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
        print(f"✓ Database exported successfully to: {complete_filename}")
        return complete_filename
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export database: {e}")
        print("Make sure:")
        print("1. MySQL client is installed")
        print("2. Database credentials are correct")
        print("3. You can connect to the database")
        return None
    except FileNotFoundError:
        print("✗ MySQL client not found. Please install MySQL client tools.")
        print("  On Ubuntu/Debian: sudo apt-get install mysql-client")
        print("  On CentOS/RHEL: sudo yum install mysql")
        print("  On Windows: Install MySQL Shell or MySQL Workbench")
        return None

def create_import_instructions(filename):
    """Create simple import instructions"""
    instructions = f"""
Hotel Management System - Data Import Instructions
=================================================

1. Transfer this file to your new Docker deployment server

2. Copy the SQL file to the database container:
   docker cp {filename} hotel_db:/tmp/

3. Import the data into the new database:
   docker exec -i hotel_db mysql -u hotel_user -photel_password temp < /tmp/{filename}

4. Run Django migrations (if needed):
   docker exec hotel_web python manage.py migrate

5. Create a superuser (if needed):
   docker exec -it hotel_web python manage.py createsuperuser

Important Notes:
- Make sure the database container is named 'hotel_db'
- Update credentials if they differ from defaults
- Always backup your new database before importing
"""

    instructions_filename = "IMPORT_INSTRUCTIONS.txt"
    with open(instructions_filename, 'w') as f:
        f.write(instructions)
    
    print(f"✓ Import instructions created: {instructions_filename}")
    return instructions_filename

def main():
    """Main function"""
    print("Hotel Management System - Data Export")
    print("=" * 40)
    
    # Export database
    filename = export_database()
    
    if filename:
        # Create import instructions
        create_import_instructions(filename)
        
        print("\n" + "=" * 40)
        print("Export Complete!")
        print("=" * 40)
        print(f"Exported file: {filename}")
        print("Import instructions: IMPORT_INSTRUCTIONS.txt")
        print("\nNext steps:")
        print("1. Transfer these files to your new deployment")
        print("2. Follow the import instructions")
        print("3. Test the application after import")

if __name__ == "__main__":
    main()