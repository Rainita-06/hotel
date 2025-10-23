# Hotel Project - Docker Deployment Guide

This guide explains how to containerize and deploy the Hotel Project using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed:
- Docker Engine 20.10+
- Docker Compose 1.29+

## Project Structure

The project includes the following Docker-related files:
- `Dockerfile`: Defines the application container
- `docker-compose.yml`: Full deployment with MySQL, Redis, Celery workers
- `docker-compose.simple.yml`: Simplified deployment with just MySQL
- `docker-compose.prod.yml`: Production deployment with Nginx reverse proxy
- `.dockerignore`: Specifies files to exclude from Docker builds
- `.env`: Environment variables for local development
- `.env.production`: Environment variables template for production

## Environment Configuration

### Local Development

Create a `.env` file in the project root with your configuration:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DB_NAME=temp
DB_USER=hotel_user
DB_PASSWORD=hotel_password
MYSQL_ROOT_PASSWORD=rootpassword

# Timezone
TIME_ZONE=Asia/Kolkata
```

### Production Deployment

For production, use the `.env.production` file as a template and update it with secure values:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-very-long-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DB_NAME=hotel_db
DB_USER=hotel_user
DB_PASSWORD=your-secure-db-password
MYSQL_ROOT_PASSWORD=your-secure-root-password

# Timezone
TIME_ZONE=Asia/Kolkata
```

## Dockerizing the Application

### 1. Building the Docker Image

To build the Docker image locally:

```bash
docker build -t hotel-app .
```

### 2. Running with Docker Compose (Recommended)

#### Full Deployment (with Celery and Redis)

```bash
docker-compose up -d
```

This will start:
- MySQL database
- Redis server
- Web application
- Celery worker
- Celery beat scheduler

#### Simple Deployment (Web + MySQL only)

```bash
docker-compose -f docker-compose.simple.yml up -d
```

#### Production Deployment (with Nginx)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This will start:
- MySQL database
- Web application
- Nginx reverse proxy

#### Local Database Deployment (Django only, connects to local database)

```bash
docker-compose -f docker-compose.local-db.yml --env-file .env.local up -d
```

This will start:
- Web application (connected to your local database)

See [LOCAL_DB_SETUP.md](LOCAL_DB_SETUP.md) for detailed instructions on configuring this setup.

### 3. Initial Setup

After starting the containers, you need to create a superuser:

```bash
# Create superuser
docker exec -it hotel_web python manage.py createsuperuser

# Load initial data (optional)
docker exec -it hotel_web python manage.py loaddata initial_data.json
```

Note: Migrations and static file collection are automatically handled during container startup.

## Deploying to Linux Server

### 1. Install Docker on Ubuntu/Debian

```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose -y

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Deploy the Application

```bash
# Clone or copy your project to the server
git clone <your-repo-url>
cd hotel_project

# Create .env file with production settings
cp .env.production .env
# Edit .env with your production values

# Start the application with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Production Considerations

1. **Environment Variables**: Always use a `.env` file with secure passwords.
   
   Note: If your secret key contains special characters like `$`, you may need to escape them with double dollar signs (`$$`) in the docker-compose files, but not in the [.env](file:///c%3A/Users/varun/Desktop/Victoireus%20internship/hotel_project/config/__init__.py) file.
2. **HTTPS**: For production, configure SSL certificates with Let's Encrypt.
3. **Backup**: Regularly backup your database volume:
   ```bash
   docker run --rm -v hotel_project_db_data:/data -v $(pwd):/backup ubuntu tar czf /backup/db_backup.tar.gz -C /data .
   ```
4. **Monitoring**: Implement monitoring for your containers and application.

## Useful Docker Commands

### Managing Containers

```bash
# View running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f web

# Stop containers
docker-compose down

# Restart specific service
docker-compose restart web

# Execute commands in container
docker exec -it hotel_web bash
```

### Database Management

```bash
# Access MySQL shell
docker exec -it hotel_db mysql -u hotel_user -p

# Backup database
docker exec hotel_db mysqldump -u hotel_user -p temp > backup.sql

# Restore database
docker exec -i hotel_db mysql -u hotel_user -p temp < backup.sql
```

### Scaling the Application

To scale the web application:

```bash
# Scale web workers (for docker-compose.yml only)
docker-compose up -d --scale web=3
```

## Troubleshooting

### Common Issues

1. **Permission denied errors**: Ensure Docker is running and your user has permissions.
2. **Port conflicts**: Change exposed ports in docker-compose.yml if needed.
3. **Database connection errors**: Check DB credentials and ensure the database container is running.
4. **Health check failures**: Check logs for specific service errors.

### Checking Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db

# View real-time logs
docker-compose logs -f
```

## Updating the Application

To deploy updates:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart with production configuration
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Health Checks

All services now include health checks to ensure proper operation:
- Database: MySQL ping
- Redis: Redis ping
- Web: Will be healthy when the application starts serving requests

Health checks improve reliability by ensuring services are ready before dependent services start.