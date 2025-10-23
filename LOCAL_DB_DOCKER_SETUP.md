# Local Database Docker Setup

This guide explains how to run Django in a Docker container while connecting to your local database.

## Overview

This setup allows you to:
- Containerize only the Django application
- Connect to your local MySQL database
- Maintain your existing database setup

## Prerequisites

1. Docker Desktop installed and running
2. MySQL database running locally
3. PowerShell (for Windows) or terminal (for other systems)

## Database Configuration

### 1. Configure MySQL to Accept External Connections

Edit your MySQL configuration file (`my.ini` on Windows or `my.cnf` on Linux/Mac) and add or modify:

```ini
[mysqld]
bind-address = 0.0.0.0
```

### 2. Create Database User for Docker Connection

Connect to your MySQL database and run:

```sql
-- Create a user that can connect from Docker containers
CREATE USER 'docker_user'@'%' IDENTIFIED BY 'your_secure_password';

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON your_database.* TO 'docker_user'@'%';

-- Apply changes
FLUSH PRIVILEGES;
```

### 3. Restart MySQL Service

After making these changes, restart your MySQL service.

## Configuration

### 1. Update Environment Variables

Edit the [.env.local](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/.env.local) file with your database details:

```env
# Database Configuration
DB_NAME=your_actual_database_name
DB_USER=docker_user
DB_PASSWORD=your_secure_password
DB_HOST=host.docker.internal
DB_PORT=3306
```

### 2. Test Database Connection

Before running the container, test that you can connect to your database from the command line:

```bash
mysql -h 127.0.0.1 -u docker_user -p your_database_name
```

## Running the Application

### Using PowerShell Script (Windows)

```powershell
# Run the PowerShell script
.\run-local-db.ps1
```

The script will:
1. Check if Docker is installed and running
2. Verify configuration files
3. Display current database settings
4. Start the Django container

### Manual Execution

```bash
# Using the environment file
docker-compose -f docker-compose.local-db.yml --env-file .env.local up --build
```

## Accessing the Application

Once running, access your application at:
- http://localhost:8000

## Stopping the Application

To stop the containers:

```bash
# If using the PowerShell script, press Ctrl+C in the terminal

# Or stop manually
docker-compose -f docker-compose.local-db.yml down
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure MySQL is configured to accept external connections
2. **Access denied**: Verify database user credentials and privileges
3. **Docker not found**: Ensure Docker Desktop is installed and running
4. **Port conflicts**: Change the port in docker-compose.local-db.yml if 8000 is in use

### Checking Logs

To view container logs:

```bash
docker-compose -f docker-compose.local-db.yml logs -f
```

### Running Management Commands

To run Django management commands:

```bash
docker exec -it hotel_web python manage.py migrate
docker exec -it hotel_web python manage.py createsuperuser
```