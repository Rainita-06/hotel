#!/usr/bin/env python3
"""
Data Import Script for New Docker Deployment

This script helps import your exported data into the new Docker environment.
It should be run in the new Docker environment after deployment.

Usage:
1. Copy your exported SQL file to the new server
2. Place this script in the project root directory
3. Run: python import_data.py <exported_sql_file>
"""

import os
import sys
import subprocess
from pathlib import Path

def check_docker_containers():
    """Check if required Docker containers are running"""
    try:
        # Check if hotel_db container is running
        result = subprocess.run(['docker', 'ps', '--filter', 'name=hotel_db', '--format', '{{.Names}}'], 
                              capture_output=True, text=True, check=True)
        if 'hotel_db' not in result.stdout:
            print("✗ Database container (hotel_db) is not running")
            return False
            
        # Check if hotel_web container is running
        result = subprocess.run(['docker', 'ps', '--filter', 'name=hotel_web', '--format', '{{.Names}}'], 
                              capture_output=True, text=True, check=True)
        if 'hotel_web' not in result.stdout:
            print("✗ Web container (hotel_web) is not running")
            return False
            
        print("✓ Required Docker containers are running")
        return True
    except subprocess.CalledProcessError:
        print("✗ Docker is not available or not running")
        return False

def import_database_data(sql_file):
    """Import database data from SQL file"""
    try:
        # Copy SQL file to database container
        print(f"Copying {sql_file} to database container...")
        subprocess.run(['docker', 'cp', str(sql_file), 'hotel_db:/tmp/'], check=True)
        
        # Get filename only
        filename = Path(sql_file).name
        
        # Import data into database
        print("Importing data into database...")
        cmd = [
            'docker', 'exec', '-i', 'hotel_db', 
            'mysql', '-u', 'hotel_user', '-photel_password', 'temp'
        ]
        
        with open(sql_file, 'r') as f:
            subprocess.run(cmd, stdin=f, check=True)
            
        print("✓ Database import completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to import database: {e}")
        return False

def run_django_migrations():
    """Run Django migrations"""
    try:
        print("Running Django migrations...")
        subprocess.run(['docker', 'exec', 'hotel_web', 'python', 'manage.py', 'migrate'], check=True)
        print("✓ Django migrations completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to run migrations: {e}")
        return False

def collect_static_files():
    """Collect static files"""
    try:
        print("Collecting static files...")
        subprocess.run(['docker', 'exec', 'hotel_web', 'python', 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("✓ Static files collected")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to collect static files: {e}")
        return False

def main():
    """Main function"""
    print("Hotel Management System - Data Import")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python import_data.py <exported_sql_file>")
        print("Example: python import_data.py hotel_db_export_20251020_153000.sql")
        sys.exit(1)
    
    sql_file = Path(sys.argv[1])
    
    # Check if SQL file exists
    if not sql_file.exists():
        print(f"✗ SQL file not found: {sql_file}")
        sys.exit(1)
    
    print(f"Importing data from: {sql_file}")
    
    # Check Docker containers
    if not check_docker_containers():
        print("Please make sure Docker is running and containers are started")
        print("Start containers with: docker-compose -f docker-compose.prod.yml up -d")
        sys.exit(1)
    
    # Import database
    if not import_database_data(sql_file):
        sys.exit(1)
    
    # Run migrations
    if not run_django_migrations():
        sys.exit(1)
    
    # Collect static files
    if not collect_static_files():
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("Import Complete!")
    print("=" * 40)
    print("Your data has been successfully imported.")
    print("\nNext steps:")
    print("1. Test the application by accessing it in your browser")
    print("2. Create a superuser if needed:")
    print("   docker exec -it hotel_web python manage.py createsuperuser")
    print("3. Verify all data is present and correct")

if __name__ == "__main__":
    main()