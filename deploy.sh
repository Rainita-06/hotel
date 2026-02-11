#!/bin/bash

# ==========================================
# Hotel Project Deployment Script (Linux)
# External DB only (Prod mode), Local DB optional
# ==========================================

set -e

GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
CYAN="\e[36m"
RESET="\e[0m"

log() {
  echo -e "$1$2${RESET}"
}

# -------------------------------
# Detect Docker Compose
# -------------------------------
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    log $RED "Docker Compose is not installed."
    exit 1
fi

log $GREEN "Using Docker Compose command: $DOCKER_COMPOSE_CMD"

# -------------------------------
# PROD MODE (External DB)
# -------------------------------
log $GREEN "Starting Hotel Project deployment (External DB)..."

if ! command -v docker &> /dev/null; then
    log $RED "Docker is not installed."
    exit 1
fi

log $GREEN "Docker detected: $(docker --version)"

if [ ! -f ".env.gcp" ]; then
    log $YELLOW "Creating .env.gcp from .env.example..."
    cp .env.example .env.gcp
    log $YELLOW "Update .env.gcp and rerun."
    exit 1
fi

log $YELLOW "Stopping existing containers..."
$DOCKER_COMPOSE_CMD -f docker-compose-gcp.yml down

log $GREEN "Building and starting containers..."
$DOCKER_COMPOSE_CMD -f docker-compose-gcp.yml --env-file .env.gcp up -d --build

log $YELLOW "Waiting for services..."
sleep 30

# -------------------------------
# DB CHECK
# -------------------------------
log $YELLOW "Checking database connectivity..."
docker exec hotel_web_gcp python manage.py shell -c \
"from django.db import connection; connection.ensure_connection(); print('Database connection successful')"

log $GREEN "Database connection verified."

# -------------------------------
# MIGRATIONS
# -------------------------------
log $YELLOW "Running migrations..."
docker exec hotel_web_gcp python manage.py migrate

log $GREEN "Migrations completed."

# -------------------------------
# INITIAL DATA
# -------------------------------
log $YELLOW "Initializing sections & permissions..."
docker exec hotel_web_gcp python manage.py init_sections

log $YELLOW "Initializing departments..."
docker exec hotel_web_gcp python manage.py init_departments

log $YELLOW "Step 3: Creating default admin user (admin:admin)..."
docker exec hotel_web_gcp python manage.py shell -c "from django.contrib.auth.models import User, Group; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); user.set_password('admin'); user.is_superuser = True; user.is_staff = True; user.save(); user.groups.clear(); admin_group = Group.objects.get(name='Admins'); user.groups.add(admin_group) if admin_group else None; print('Admin user created/updated and added to Admins group:', user.username); dept = Department.objects.first(); profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'full_name': 'Administrator', 'phone': '+1234567890', 'title': 'System Administrator', 'department': dept, 'role': 'admin'}); print('Admin profile:', profile.full_name)"
# -------------------------------
# DONE
# -------------------------------
log $GREEN "========================================"
log $GREEN "Deployment completed successfully!"
log $GREEN "========================================"
log $CYAN "Access the app at http://localhost:80"
log $YELLOW "Available Credentials:"
log $GREEN "    Superuser admin"
log $GREEN  "   Username:admin"
log $GREEN "    Password:admin"