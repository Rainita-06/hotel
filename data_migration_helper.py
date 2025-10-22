#!/usr/bin/env python3
"""
Data Migration Helper Script for Hotel Management System

This script helps migrate data from an existing database to a new Docker deployment.
It generates SQL dump files and provides instructions for importing data.

Usage:
1. Run this script on your current system to export data
2. Transfer the generated files to your new deployment
3. Follow the instructions to import data into the new Docker environment
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def check_mysql_client():
    """Check if MySQL client is available"""
    try:
        subprocess.run(['mysql', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_db_config():
    """Get database configuration from environment or use defaults"""
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '3306'),
        'name': os.environ.get('DB_NAME', 'temp'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
    }

def export_database_schema(db_config, output_dir):
    """Export database schema without data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    schema_file = output_dir / f"hotel_db_schema_{timestamp}.sql"
    
    cmd = [
        'mysqldump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--user={db_config["user"]}',
        f'--password={db_config["password"]}',
        '--no-data',
        '--single-transaction',
        '--routines',
        '--triggers',
        db_config['name']
    ]
    
    try:
        with open(schema_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
        print(f"✓ Database schema exported to: {schema_file}")
        return schema_file
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export database schema: {e}")
        return None

def export_database_data(db_config, output_dir):
    """Export database data without schema"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_file = output_dir / f"hotel_db_data_{timestamp}.sql"
    
    cmd = [
        'mysqldump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--user={db_config["user"]}',
        f'--password={db_config["password"]}',
        '--no-create-info',
        '--single-transaction',
        '--skip-triggers',
        '--complete-insert',
        db_config['name']
    ]
    
    try:
        with open(data_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
        print(f"✓ Database data exported to: {data_file}")
        return data_file
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export database data: {e}")
        return None

def export_database_complete(db_config, output_dir):
    """Export complete database (schema + data)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    complete_file = output_dir / f"hotel_db_complete_{timestamp}.sql"
    
    cmd = [
        'mysqldump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--user={db_config["user"]}',
        f'--password={db_config["password"]}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--complete-insert',
        db_config['name']
    ]
    
    try:
        with open(complete_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
        print(f"✓ Complete database exported to: {complete_file}")
        return complete_file
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export complete database: {e}")
        return None

def create_import_instructions(output_dir, db_config):
    """Create instructions for importing data into Docker environment"""
    instructions = f"""
Hotel Management System - Data Migration Instructions
=====================================================

This document provides instructions for importing your data into the new Docker deployment.

1. Exported Files:
   - Schema only: [SCHEMA_FILE]
   - Data only: [DATA_FILE]
   - Complete database: [COMPLETE_FILE]

2. Transfer Files:
   Copy the exported SQL files to your new deployment server.

3. Import into Docker Environment:

   Option A: Import complete database
   ----------------------------------
   # Copy the complete database file to the database container
   docker cp [COMPLETE_FILE] hotel_db:/tmp/
   
   # Import the data
   docker exec -i hotel_db mysql -u {db_config['user']} -p{db_config['password']} {db_config['name']} < [COMPLETE_FILE]

   Option B: Import schema and data separately
   ------------------------------------------
   # Copy files to the database container
   docker cp [SCHEMA_FILE] hotel_db:/tmp/
   docker cp [DATA_FILE] hotel_db:/tmp/
   
   # Import schema first
   docker exec -i hotel_db mysql -u {db_config['user']} -p{db_config['password']} {db_config['name']} < [SCHEMA_FILE]
   
   # Import data
   docker exec -i hotel_db mysql -u {db_config['user']} -p{db_config['password']} {db_config['name']} < [DATA_FILE]

4. Run Django Migrations:
   After importing the data, run any new migrations that may have been added:
   
   docker exec hotel_web python manage.py migrate

5. Create Superuser (if needed):
   docker exec -it hotel_web python manage.py createsuperuser

6. Collect Static Files:
   docker exec hotel_web python manage.py collectstatic --noinput

Important Notes:
- Replace [SCHEMA_FILE], [DATA_FILE], and [COMPLETE_FILE] with actual filenames
- Make sure to use the correct container names (hotel_db, hotel_web)
- Update database credentials if they differ from the exported ones
- Always backup your new database before importing data
"""

    instructions_file = output_dir / "DATA_MIGRATION_INSTRUCTIONS.md"
    with open(instructions_file, 'w') as f:
        f.write(instructions)
    
    print(f"✓ Import instructions created: {instructions_file}")
    return instructions_file

def create_migration_config(output_dir, db_config):
    """Create a configuration file with migration settings"""
    config = {
        'export_timestamp': datetime.now().isoformat(),
        'database': db_config,
        'exported_files': {},
        'migration_instructions': 'DATA_MIGRATION_INSTRUCTIONS.md'
    }
    
    config_file = output_dir / "migration_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Migration configuration saved: {config_file}")
    return config_file

def main():
    """Main function"""
    print("Hotel Management System - Data Migration Helper")
    print("=" * 50)
    
    # Check if MySQL client is available
    if not check_mysql_client():
        print("✗ MySQL client not found. Please install MySQL client tools.")
        print("  On Ubuntu/Debian: sudo apt-get install mysql-client")
        print("  On CentOS/RHEL: sudo yum install mysql")
        print("  On Windows: Install MySQL Shell or MySQL Workbench")
        sys.exit(1)
    
    # Get database configuration
    db_config = get_db_config()
    
    # Create output directory
    output_dir = Path("data_migration_exports")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Exporting data to: {output_dir.absolute()}")
    print(f"Database: {db_config['name']}@{db_config['host']}:{db_config['port']}")
    
    # Export data
    print("\nExporting database...")
    schema_file = export_database_schema(db_config, output_dir)
    data_file = export_database_data(db_config, output_dir)
    complete_file = export_database_complete(db_config, output_dir)
    
    # Create instructions
    print("\nCreating import instructions...")
    instructions_file = create_import_instructions(output_dir, db_config)
    
    # Create configuration
    print("\nCreating migration configuration...")
    config_file = create_migration_config(output_dir, db_config)
    
    # Update instructions with actual filenames
    if all([schema_file, data_file, complete_file, instructions_file]):
        with open(instructions_file, 'r') as f:
            content = f.read()
        
        content = content.replace('[SCHEMA_FILE]', schema_file.name)
        content = content.replace('[DATA_FILE]', data_file.name)
        content = content.replace('[COMPLETE_FILE]', complete_file.name)
        
        with open(instructions_file, 'w') as f:
            f.write(content)
    
    print("\n" + "=" * 50)
    print("Migration Export Complete!")
    print("=" * 50)
    print(f"Exported files are in: {output_dir}")
    print(f"Follow the instructions in: {instructions_file}")
    print("\nNext steps:")
    print("1. Transfer the exported files to your new deployment")
    print("2. Follow the instructions in the migration guide")
    print("3. Test the application after import")

if __name__ == "__main__":
    main()