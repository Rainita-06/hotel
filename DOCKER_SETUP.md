# Hotel Project Docker Setup Guide

This guide provides detailed instructions for setting up and running the Hotel Management System using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [Docker Compose Files](#docker-compose-files)
5. [Development Workflow](#development-workflow)
6. [Production Deployment](#production-deployment)
7. [Common Operations](#common-operations)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker Engine 20.10+
- Docker Compose 1.29+

For Windows users, Docker Desktop is recommended.

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hotel_project
   ```

2. Create environment file:
   ```bash
   cp .env.production .env
   ```

3. Edit the [.env](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/config/__init__.py) file with your configuration.

4. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. Create a superuser:
   ```bash
   docker exec -it hotel_web_dev python manage.py createsuperuser
   ```

6. Access the application at `http://localhost:8000`

## Environment Configuration

### Environment Files

The project includes several environment configuration files:

- `.env.production` - Template for production environment variables
- `.env` - Your local environment configuration (created from .env.production)

### Required Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DJANGO_SECRET_KEY` | Django secret key | django-insecure-... |
| `DJANGO_DEBUG` | Debug mode | True |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | localhost,127.0.0.1 |
| `DB_NAME` | Database name | temp |
| `DB_USER` | Database user | hotel_user |
| `DB_PASSWORD` | Database password | hotel_password |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | rootpassword |
| `TIME_ZONE` | Application timezone | Asia/Kolkata |

Note: If your secret key contains special characters like `$`, you may need to escape them with double dollar signs (`$$`) in the docker-compose files, but not in the [.env](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/config/__init__.py) file.

## Docker Compose Files

The project includes multiple Docker Compose configurations for different environments:

### docker-compose.dev.yml

Development environment with:
- Hot reloading for code changes
- Shared volumes for development
- Django development server

### docker-compose.yml

Full production-like environment with:
- Gunicorn application server
- Celery workers
- Redis
- MySQL

### docker-compose.simple.yml

Simplified environment with:
- Gunicorn application server
- MySQL only

### docker-compose.prod.yml

Production environment with:
- Nginx reverse proxy
- Gunicorn application server
- MySQL

### docker-compose.test.yml

Test environment for running unit tests with:
- MySQL test database
- Test configuration

### docker-compose.override.yml

Overrides for local development when using the default docker-compose.yml

## Development Workflow

### Starting Development Environment

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

### Code Changes

With the development environment running, code changes are automatically reflected due to volume mounting.

### Running Management Commands

```bash
# Run migrations
docker exec hotel_web_dev python manage.py migrate

# Create superuser
docker exec -it hotel_web_dev python manage.py createsuperuser

# Collect static files
docker exec hotel_web_dev python manage.py collectstatic --noinput

# Run tests
docker exec hotel_web_dev python manage.py test
```

### Running Tests in Isolated Environment

For running tests in a completely isolated environment:

```bash
# Run tests in isolated Docker environment
docker-compose -f docker-compose.test.yml up --exit-code-from web
```

This will create a separate test database and run all tests in a clean environment.

### Accessing Containers

```bash
# Access web container shell
docker exec -it hotel_web_dev bash

# Access database shell
docker exec -it hotel_db_dev mysql -u hotel_user -p
```

## Production Deployment

### Production Environment Setup

1. Copy and configure environment file:
   ```bash
   cp .env.production .env
   # Edit .env with production values
   ```

2. Start production environment:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. Create superuser:
   ```bash
   docker exec -it hotel_web python manage.py createsuperuser
   ```

### Production Considerations

1. **Security**: 
   - Use strong passwords
   - Set `DJANGO_DEBUG=False`
   - Use a strong `DJANGO_SECRET_KEY`
   - Configure `DJANGO_ALLOWED_HOSTS` appropriately

2. **SSL/HTTPS**: 
   - Configure SSL certificates with Let's Encrypt
   - Update Nginx configuration for HTTPS

3. **Backups**: 
   - Regularly backup database volumes
   - Implement backup rotation policies

4. **Monitoring**: 
   - Implement application monitoring
   - Set up log aggregation

## Common Operations

### Using Makefile (Linux/macOS)

```bash
# Start development environment
make up

# View logs
make logs

# Access shell
make shell

# Run migrations
make migrate

# Create superuser
make superuser
```

### Using PowerShell (Windows)

```powershell
# Run deployment script
.\deploy.ps1
```

### Using Shell Scripts (Linux/macOS)

```bash
# Run deployment script
./deploy.sh
```

### Database Operations

```bash
# Backup database
docker exec hotel_db_dev mysqldump -u hotel_user -p temp > backup.sql

# Restore database
docker exec -i hotel_db_dev mysql -u hotel_user -p temp < backup.sql

# Access MySQL shell
docker exec -it hotel_db_dev mysql -u hotel_user -p
```

### Scaling Services

```bash
# Scale web workers (for docker-compose.yml)
docker-compose -f docker-compose.yml up -d --scale web=3
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Solution: Change ports in docker-compose files
   - Example: Change `8000:8000` to `8001:8000`

2. **Permission Denied**
   - Solution: Ensure Docker is running with proper permissions
   - Linux: Add user to docker group

3. **Database Connection Issues**
   - Check database credentials in [.env](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/config/__init__.py) file
   - Ensure database container is running

4. **Volume Permissions**
   - Solution: Check file permissions on host system
   - Linux: Ensure proper ownership of project directory

### Checking Logs

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs

# View specific service logs
docker-compose -f docker-compose.dev.yml logs web

# View real-time logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Health Checks

All services include health checks:
- Database: MySQL ping
- Redis: Redis ping
- Web: Application readiness

Check service health:
```bash
docker-compose -f docker-compose.dev.yml ps
```

### Cleaning Up

```bash
# Remove containers and volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove all unused containers, networks, and images
docker system prune -a
```

## Advanced Configuration

### Custom Network

All Docker Compose files use custom networks for service isolation.

### Volume Management

Persistent data is stored in named volumes:
- Database data
- Static files
- Media files

### Environment-Specific Settings

Different environments use different settings:
- Development: Debug enabled, development server
- Production: Debug disabled, Gunicorn, Nginx

## Updating the Application

To update to the latest version:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Support

For issues with the Docker setup, please check:
1. This documentation
2. Docker logs
3. Environment configuration
4. System requirements