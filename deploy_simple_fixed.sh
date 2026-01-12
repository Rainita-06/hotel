#!/bin/bash

# Simple Hotel Project Deployment Script for Linux
# This script replicates the logic of deploy_simple_fixed.ps1 for Linux environments (Ubuntu/Debian, etc.)

LOCAL_DB=false

# Usage information
usage() {
    echo "Usage: $0 [--local-db]"
    echo "  --local-db : Use local database configuration (requires docker-compose.local-db.yml)"
    exit 1
}

# Parse arguments
for arg in "$@"
do
    case $arg in
        --local-db|-LocalDB)
        LOCAL_DB=true
        shift
        ;;
        -h|--help)
        usage
        ;;
    esac
done

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine Docker Compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}Docker Compose is not installed (neither 'docker-compose' nor 'docker compose' found). Please install Docker Desktop or Docker Compose plugin.${NC}"
    exit 1
fi

echo -e "${GREEN}Using Docker Compose command: $DOCKER_COMPOSE_CMD${NC}"

if [ "$LOCAL_DB" = true ]; then
    echo -e "${GREEN}Starting Hotel Project deployment with Local Database...${NC}"
    
    # Check if docker-compose.local-db.yml exists
    if [ ! -f "docker-compose.local-db.yml" ]; then
        echo -e "${RED}docker-compose.local-db.yml not found. Please ensure you're in the correct directory.${NC}"
        exit 1
    fi
    
    # Check if .env.local file exists, if not copy from .env.example
    if [ ! -f ".env.local" ]; then
        echo -e "${YELLOW}Creating .env.local file from .env.example template...${NC}"
        cp ".env.example" ".env.local"
        echo -e "${YELLOW}Please update the .env.local file with your local database configuration and run this script again with --local-db flag.${NC}"
        echo -e "${YELLOW}Required updates:${NC}"
        echo -e "${YELLOW}1. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details${NC}"
        echo -e "${YELLOW}2. Set DB_HOST=host.docker.internal to connect to your local database${NC}"
        exit 1
    fi
    
    # Stop any existing containers
    echo -e "${YELLOW}Stopping any existing containers...${NC}"
    $DOCKER_COMPOSE_CMD -f docker-compose.local-db.yml down
    
    # Build and start services
    echo -e "${GREEN}Building and starting Docker containers with local database connection...${NC}"
    $DOCKER_COMPOSE_CMD -f docker-compose.local-db.yml --env-file .env.local up -d --build
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 15
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${CYAN}Access the application at http://localhost:8000${NC}"

else
    echo -e "${GREEN}Starting Hotel Project deployment...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    docker_version=$(docker --version)
    echo -e "${GREEN}Docker is installed: $docker_version${NC}"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example template...${NC}"
        # Make sure .env.example exists before copying
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            echo -e "${YELLOW}Please update the .env file with your configuration and run this script again.${NC}"
        else
             echo -e "${RED}.env.example not found. Cannot create .env.${NC}"
        fi
        exit 1
    fi
    
    # Stop any existing containers
    echo -e "${YELLOW}Stopping any existing containers...${NC}"
    $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml down
    
    # Build and start services
    echo -e "${GREEN}Building and starting Docker containers...${NC}"
    $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --build
    
    # Wait for services
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 30
    
    echo -e "${YELLOW}Ensuring database is fully initialized...${NC}"
    sleep 15
    
    # Check if database is accessible
    echo -e "${YELLOW}Checking database connectivity...${NC}"
    docker exec hotel_web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Database connection failed. Retrying after additional wait...${NC}"
        sleep 30
        docker exec hotel_web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Database connection still failing. Please check the logs.${NC}"
            docker logs hotel_db
            exit 1
        fi
    fi
    
    echo -e "${GREEN}Database connection verified successfully.${NC}"
    
    # Initialize data
    echo -e "${YELLOW}Initializing data...${NC}"
    sleep 15
    
    # CRITICAL: Run database migrations FIRST
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker exec hotel_web python manage.py migrate
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Migration failed. Please check the logs.${NC}"
        docker logs hotel_web
        exit 1
    fi
    
    echo -e "${GREEN}Migrations completed successfully.${NC}"
    
    # STEP 1: Initialize sections and permissions FIRST (creates groups)
    echo -e "${YELLOW}Step 1: Initializing sections and permissions...${NC}"
    docker exec hotel_web python manage.py init_sections
    
    # STEP 2: Initialize departments
    echo -e "${YELLOW}Step 2: Initializing departments...${NC}"
    docker exec hotel_web python manage.py init_departments
    
    # STEP 3: Create admin user
    echo -e "${YELLOW}Step 3: Creating default admin user (admin:admin)...${NC}"
    # Note: Using printf to avoid issues with quoting in bash within shell -c
    # But for simplicity, we keep the Python one-liner carefully quoted.
    docker exec hotel_web python manage.py shell -c "from django.contrib.auth.models import User, Group; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); user.set_password('admin'); user.is_superuser = True; user.is_staff = True; user.save(); user.groups.clear(); admin_group = Group.objects.get(name='Admins'); user.groups.add(admin_group) if admin_group else None; print('Admin user created/updated and added to Admins group:', user.username); dept = Department.objects.first(); profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'full_name': 'Administrator', 'phone': '+1234567890', 'title': 'System Administrator', 'department': dept, 'role': 'admin'}); print('Admin profile:', profile.full_name)"
    
    # STEP 4: Create test users
    echo -e "${YELLOW}Step 4: Creating test users...${NC}"
    docker exec hotel_web python manage.py sample_tickets
    docker exec hotel_web python manage.py sample_gym,feed
    docker exec hotel_web python manage.py create_test_users
    
    echo -e ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${CYAN}Access the application at http://localhost:8080${NC}"
    echo -e "${YELLOW}"
    echo -e "Available Credentials:"
    echo -e "  Superuser Admin:"
    echo -e "    Username: admin"
    echo -e "    Password: admin"
    echo -e ""
    echo -e "  Test Users:"
    echo -e "    Admin:  test_admin  / testpassword123"
    echo -e "    Staff:  test_staff  / testpassword123"
    echo -e "    User:   test_user   / testpassword123"
    echo -e "${GREEN}"
    echo -e "Permissions configured:"
    echo -e "  - Admins: Full access to all sections"
    echo -e "  - Users: Access to all sections except Users"
    echo -e "  - Staff: Access only to My Tickets section"
    echo -e "${NC}"
fi
