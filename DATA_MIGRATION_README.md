# Hotel Management System - Data Migration Guide

This guide explains how to migrate your existing data to the new Docker deployment.

## Overview

The migration process involves:
1. Exporting data from your current system
2. Setting up the new Docker environment
3. Importing data into the new environment

## Files Provided

1. **[export_data.py](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/export_data.py)** - Export data from your current system
2. **[import_data.py](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/import_data.py)** - Import data into the new Docker environment
3. **[data_migration_helper.py](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/data_migration_helper.py)** - Advanced migration helper (optional)

## Step 1: Export Data from Current System

### Prerequisites
- MySQL client tools installed
- Access to your current database

### Process
1. Copy [export_data.py](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/export_data.py) to your current system
2. Set database environment variables (or edit the script):
   ```bash
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_NAME=temp
   export DB_USER=your_username
   export DB_PASSWORD=your_password
   ```
3. Run the export script:
   ```bash
   python export_data.py
   ```
4. This will create:
   - A SQL dump file (e.g., `hotel_db_export_20251020_153000.sql`)
   - Import instructions (`IMPORT_INSTRUCTIONS.txt`)

## Step 2: Set Up New Docker Environment

1. Transfer all project files to your new server
2. Create environment file:
   ```bash
   cp .env.production .env
   # Edit .env with your configuration
   ```
3. Start the Docker environment:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Step 3: Import Data into New Environment

1. Copy the SQL dump file to your new server
2. Copy [import_data.py](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/import_data.py) to your project root
3. Run the import script:
   ```bash
   python import_data.py hotel_db_export_20251020_153000.sql
   ```
4. The script will:
   - Copy the SQL file to the database container
   - Import the data
   - Run Django migrations
   - Collect static files

## Step 4: Finalize Setup

1. Create a superuser (if needed):
   ```bash
   docker exec -it hotel_web python manage.py createsuperuser
   ```
2. Test the application in your browser
3. Verify all data is present and correct

## Troubleshooting

### Common Issues

1. **MySQL client not found**
   - Install MySQL client tools:
     - Ubuntu/Debian: `sudo apt-get install mysql-client`
     - CentOS/RHEL: `sudo yum install mysql`

2. **Connection refused**
   - Ensure database credentials are correct
   - Check that the database is running

3. **Permission denied**
   - Ensure Docker is running with proper permissions
   - Check file permissions on SQL dump file

4. **Import fails**
   - Check the SQL file for errors
   - Ensure the database schema matches

### Manual Import

If the script doesn't work, you can manually import the data:

1. Copy SQL file to container:
   ```bash
   docker cp hotel_db_export_20251020_153000.sql hotel_db:/tmp/
   ```

2. Import data:
   ```bash
   docker exec -i hotel_db mysql -u hotel_user -photel_password temp < hotel_db_export_20251020_153000.sql
   ```

3. Run migrations:
   ```bash
   docker exec hotel_web python manage.py migrate
   ```

4. Collect static files:
   ```bash
   docker exec hotel_web python manage.py collectstatic --noinput
   ```

## Important Notes

- Always backup your new database before importing data
- The import process will overwrite existing data in the new database
- Test the application thoroughly after migration
- Keep the SQL dump file as a backup until you're confident in the migration