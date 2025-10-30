#!/usr/bin/env python3
"""
Simple Data Export Script for Hotel Management System

This script exports your current database to SQL files that can be imported
into your new Docker deployment.

Usage:
1. Make sure you have MySQL client installed
2. Set your database environment variables in .env.local
3. Ensure your database is accessible
4. Run: python export_data.py
5. The script will create SQL dump files in the current directory
"""

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env.local file
load_dotenv('.env.local')

def get_db_config():
    """Get database configuration - loads from environment variables"""
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
    
    # Print database configuration for debugging (mask password)
    masked_password = '*' * len(db_config['password']) if db_config['password'] else '(not set)'
    print(f"Database Configuration:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Name: {db_config['name']}")
    print(f"  User: {db_config['user']}")
    print(f"  Password: {masked_password}")
    print()
    
    # Validate that we have a database name
    if not db_config['name']:
        print("✗ Error: Database name is not set. Please check your .env.local file.")
        return None
    
    # Check if database exists by trying to connect
    print("Checking database connection...")
    try:
        # Test connection with a simple query
        test_cmd = [
            'mysql',
            f'--host={db_config["host"]}',
            f'--port={db_config["port"]}',
            f'--user={db_config["user"]}',
            '--execute=SELECT 1;',
            '--skip-column-names'
        ]
        
        # Add password if provided
        if db_config["password"]:
            test_cmd.insert(4, f'--password={db_config["password"]}')
        
        subprocess.run(test_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✓ Database connection successful")
        print()
    except subprocess.CalledProcessError:
        print("✗ Failed to connect to database")
        print("Please check:")
        print("1. Database server is running")
        print("2. Database credentials are correct")
        print("3. Network connectivity to database server")
        print("4. Database user has proper permissions")
        print()
        return None
    except FileNotFoundError:
        print("✗ MySQL client not found")
        print("Please install MySQL client tools:")
        print("  On Ubuntu/Debian: sudo apt-get install mysql-client")
        print("  On CentOS/RHEL: sudo yum install mysql")
        print("  On Windows: Install MySQL Shell or MySQL Workbench")
        print()
        return None
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export complete database
    complete_filename = f"hotel_db_export_{timestamp}.sql"
    
    # Build mysqldump command
    cmd = [
        'mysqldump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--user={db_config["user"]}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--complete-insert',
        db_config['name']
    ]
    
    # Add password if provided
    if db_config["password"]:
        cmd.insert(4, f'--password={db_config["password"]}')
    
    print(f"Running mysqldump command...")
    print(f"Command: {' '.join(cmd[:4] + ['--password=***'] + cmd[5:]) if db_config['password'] else ' '.join(cmd)}")
    
    try:
        with open(complete_filename, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
        print(f"✓ Database exported successfully to: {complete_filename}")
        # Check if file is empty
        if os.path.getsize(complete_filename) == 0:
            print("⚠ Warning: Export file is empty. This might indicate no data in the database.")
        return complete_filename
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export database: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr.strip()}")
        print("Make sure:")
        print("1. MySQL client is installed and in PATH")
        print("2. Database credentials are correct")
        print("3. You can connect to the database")
        print("4. The database exists and contains data")
        return None
    except FileNotFoundError:
        print("✗ MySQL client not found. Please install MySQL client tools.")
        print("  On Ubuntu/Debian: sudo apt-get install mysql-client")
        print("  On CentOS/RHEL: sudo yum install mysql")
        print("  On Windows: Install MySQL Shell or MySQL Workbench")
        return None
    except Exception as e:
        print(f"✗ Unexpected error occurred: {e}")
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
    print()
    
    # Check if .env.local exists
    if not os.path.exists('.env.local'):
        print("⚠ Warning: .env.local file not found.")
        print("Please create a .env.local file with your database configuration.")
        print("You can copy .env.local.example to .env.local and update it with your settings.")
        print()
    else:
        print("✓ Found .env.local file")
        print()
    
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
    else:
        print("\n" + "=" * 40)
        print("Export Failed!")
        print("=" * 40)
        print("Please check the error messages above and try again.")
        print()
        print("Troubleshooting tips:")
        print("1. Ensure your .env.local file has correct database credentials")
        print("2. Make sure your database server is running")
        print("3. Verify MySQL client tools are installed")
        print("4. Check that the database exists and contains data")
        print("5. Ensure the database user has proper permissions")

if __name__ == "__main__":
    main()