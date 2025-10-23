#!/bin/bash
# Script to run Django in Docker connected to local database

echo "Starting Django container connected to local database..."

# Use the new docker-compose file
docker-compose -f docker-compose.local-db.yml up --build

echo "Django container is running and connected to your local database."
echo "Access your application at http://localhost:8000"