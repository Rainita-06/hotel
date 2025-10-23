# Local Database Setup for Hotel Project

This guide explains how to set up and run the Hotel Project with a local database connection.

## Overview

This setup allows you to:
- Run Django in a Docker container
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

Edit the `.env.local` file with your database details:

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
# Run the setup script (optional, for first-time setup)
.\setup-local-db.ps1

# Run the application
.\run-local-db.ps1
```

### Manual Execution

```bash
# Using the environment file
docker-compose -f docker-compose.local-db.yml --env-file .env.local up --build
```

## Creating Users

After the application is running, you'll need to create users to log in:

### Option 1: Create a Superuser

```bash
docker exec -it hotel_web_local python manage.py createsuperuser
```

### Option 2: Create Test Users

```bash
docker exec -it hotel_web_local python manage.py create_test_users
```

This creates three test users:
- Admin: test_admin / testpassword123
- Staff: test_staff / testpassword123
- User: test_user / testpassword123

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
docker exec -it hotel_web_local python manage.py migrate
docker exec -it hotel_web_local python manage.py createsuperuser
```