#!/bin/bash

# Hotel Project Deployment Script for Linux

set -e  # Exit on any error

echo "Starting Hotel Project deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code from repository..."
    git pull
fi

# Check if .env file exists, if not copy from .env.production
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.production template..."
    cp .env.production .env
    echo "Please update the .env file with your configuration and run this script again."
    exit 1
fi

# Build and start services
echo "Building and starting Docker containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
 sleep 15

# Show status
echo "Deployment status:"
docker-compose -f docker-compose.prod.yml ps

echo "Deployment completed successfully!"
echo "Access the application at http://localhost"
echo "To create a superuser, run: docker exec -it hotel_web python manage.py createsuperuser"
echo "To view logs, run: docker-compose -f docker-compose.prod.yml logs -f"