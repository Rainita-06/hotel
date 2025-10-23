# Troubleshooting Guide

This guide helps you resolve common issues with the Hotel Project setup.

## CSRF Verification Failed (403 Error)

### Problem
When trying to log in, you receive a "CSRF verification failed. Request aborted." error.

### Solutions

1. **Ensure proper database connection**
   - Check that your database credentials in `.env.local` are correct
   - Verify that your local MySQL is configured to accept external connections
   - Make sure the database user has proper permissions

2. **Check Django migrations**
   - Run migrations to ensure the database schema is up to date:
     ```bash
     docker exec -it hotel_web_local python manage.py migrate
     ```

3. **Clear browser cache and cookies**
   - Clear your browser's cache and cookies for localhost
   - Try accessing the application in an incognito/private browsing window

4. **Verify CSRF middleware is enabled**
   - Check that `django.middleware.csrf.CsrfViewMiddleware` is in your MIDDLEWARE settings

## Database Connection Issues

### Problem
Django cannot connect to your local database.

### Solutions

1. **Check database credentials**
   - Verify that DB_NAME, DB_USER, and DB_PASSWORD in `.env.local` are correct
   - Ensure the database exists and the user has access to it

2. **Configure MySQL for external connections**
   - Edit your MySQL configuration file (`my.ini` or `my.cnf`)
   - Add or modify: `bind-address = 0.0.0.0`
   - Restart MySQL service

3. **Create proper database user**
   ```sql
   CREATE USER 'hotel_user'@'%' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON your_database.* TO 'hotel_user'@'%';
   FLUSH PRIVILEGES;
   ```

4. **Test connection manually**
   ```bash
   mysql -h 127.0.0.1 -u hotel_user -p your_database_name
   ```

## Docker Container Issues

### Problem
Containers fail to start or keep restarting.

### Solutions

1. **Check Docker logs**
   ```bash
   docker-compose -f docker-compose.local-db.yml logs
   ```

2. **Ensure sufficient resources**
   - Make sure Docker has enough memory and CPU allocated
   - Check Docker Desktop settings

3. **Rebuild containers**
   ```bash
   docker-compose -f docker-compose.local-db.yml down
   docker-compose -f docker-compose.local-db.yml up -d --build
   ```

## Login Issues

### Problem
Unable to log in after creating users.

### Solutions

1. **Create a superuser**
   ```bash
   docker exec -it hotel_web_local python manage.py createsuperuser
   ```

2. **Create test users**
   ```bash
   docker exec -it hotel_web_local python manage.py create_test_users
   ```

3. **Check user permissions**
   - Log in as admin and check user roles in the admin panel
   - Ensure users are assigned to appropriate groups

## Port Conflicts

### Problem
Application fails to start due to port conflicts.

### Solutions

1. **Change the port in docker-compose.local-db.yml**
   ```yaml
   ports:
     - "8001:8000"  # Change 8001 to an available port
   ```

2. **Check for processes using the port**
   ```bash
   netstat -ano | findstr :8000
   ```

## Static Files Not Loading

### Problem
CSS and other static files are not loading.

### Solutions

1. **Collect static files**
   ```bash
   docker exec -it hotel_web_local python manage.py collectstatic --noinput
   ```

2. **Check static file configuration**
   - Ensure STATIC_URL and STATIC_ROOT are properly configured in settings.py

## General Debugging Steps

1. **Check all container logs**
   ```bash
   docker-compose -f docker-compose.local-db.yml logs -f
   ```

2. **Verify environment variables**
   ```bash
   docker exec -it hotel_web_local env
   ```

3. **Access container shell for debugging**
   ```bash
   docker exec -it hotel_web_local bash
   ```

4. **Check Django settings**
   ```bash
   docker exec -it hotel_web_local python manage.py diffsettings
   ```