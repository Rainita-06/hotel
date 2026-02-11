<#
Hotel Project Deployment Script for Windows (PowerShell)
External DB only (Prod mode), Local DB optional
#>

param(
    [switch]$LocalDB
)

# -------------------------------
# Colors
# -------------------------------
$GREEN  = "Green"
$YELLOW = "Yellow"
$RED    = "Red"
$CYAN   = "Cyan"

function Write-Color {
    param ($Message, $Color)
    Write-Host $Message -ForegroundColor $Color
}

# -------------------------------
# Detect Docker Compose
# -------------------------------
$DOCKER_COMPOSE_CMD = $null

if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $DOCKER_COMPOSE_CMD = "docker-compose"
}
elseif (docker compose version 2>$null) {
    $DOCKER_COMPOSE_CMD = "docker compose"
}
else {
    Write-Color "Docker Compose is not installed. Install Docker Desktop first." $RED
    exit 1
}

Write-Color "Using Docker Compose command: $DOCKER_COMPOSE_CMD" $GREEN

# -------------------------------
# LOCAL DB MODE
# -------------------------------
if ($LocalDB) {
    Write-Color "Starting Hotel Project deployment with Local Database..." $GREEN

    if (-not (Test-Path "docker-compose.local-db.yml")) {
        Write-Color "docker-compose.local-db.yml not found." $RED
        exit 1
    }

    if (-not (Test-Path ".env.local")) {
        Write-Color "Creating .env.local from .env.example..." $YELLOW
        Copy-Item ".env.example" ".env.local"
        Write-Color "Update .env.local and rerun with -LocalDB" $YELLOW
        exit 1
    }

    Write-Color "Stopping existing containers..." $YELLOW
    & $DOCKER_COMPOSE_CMD -f docker-compose.local-db.yml down

    Write-Color "Building and starting containers (Local DB)..." $GREEN
    & $DOCKER_COMPOSE_CMD -f docker-compose.local-db.yml --env-file .env.local up -d --build

    Write-Color "Waiting for services to start..." $YELLOW
    Start-Sleep -Seconds 15

    Write-Color "Deployment completed successfully!" $GREEN
    Write-Color "Access the app at http://localhost:8000" $CYAN
    exit 0
}

# -------------------------------
# PROD MODE (External DB)
# -------------------------------
Write-Color "Starting Hotel Project deployment (External DB)..." $GREEN

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Color "Docker is not installed." $RED
    exit 1
}

Write-Color "Docker detected: $(docker --version)" $GREEN

if (-not (Test-Path ".env.gcp")) {
    Write-Color "Creating .env.gcp from .env.example..." $YELLOW
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.gcp"
        Write-Color "Update .env.gcp with external DB credentials and rerun." $YELLOW
    }
    else {
        Write-Color ".env.example not found." $RED
    }
    exit 1
}

Write-Color "Stopping existing containers..." $YELLOW
& $DOCKER_COMPOSE_CMD -f docker-compose-gcp.yml down

Write-Color "Building and starting containers..." $GREEN
& $DOCKER_COMPOSE_CMD -f docker-compose-gcp.yml --env-file .env.gcp up -d --build

Write-Color "Waiting for services..." $YELLOW
Start-Sleep -Seconds 30

# -------------------------------
# DB CHECK (External DB)
# -------------------------------
Write-Color "Checking database connectivity..." $YELLOW
docker exec hotel_web_gcp python manage.py shell -c `
"from django.db import connection; connection.ensure_connection(); print('Database connection successful')"

if ($LASTEXITCODE -ne 0) {
    Write-Color "Database connection failed. Check external DB host/credentials/firewall." $RED
    exit 1
}

Write-Color "Database connection verified." $GREEN

# -------------------------------
# MIGRATIONS
# -------------------------------
Write-Color "Running migrations..." $YELLOW
docker exec hotel_web_gcp python manage.py migrate

if ($LASTEXITCODE -ne 0) {
    Write-Color "Migration failed." $RED
    docker logs hotel_web_gcp
    exit 1
}

Write-Color "Migrations completed." $GREEN

# -------------------------------
# INITIAL DATA
# -------------------------------
Write-Color "Initializing sections & permissions..." $YELLOW
docker exec hotel_web_gcp python manage.py init_sections

Write-Color "Initializing departments..." $YELLOW
docker exec hotel_web_gcp python manage.py init_departments

# STEP 3: Create admin user and add to Admins group
    Write-Host "Step 3: Creating default admin user (admin:admin)..." -ForegroundColor Yellow
    docker exec hotel_web_gcp python manage.py shell -c "from django.contrib.auth.models import User, Group; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); user.set_password('admin'); user.is_superuser = True; user.is_staff = True; user.save(); user.groups.clear(); admin_group = Group.objects.get(name='Admins'); user.groups.add(admin_group); print('Admin user created/updated and added to Admins group:', user.username); dept = Department.objects.first(); profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'full_name': 'Administrator', 'phone': '+1234567890', 'title': 'System Administrator', 'department': dept, 'role': 'admin'}); print('Admin profile:', profile.full_name)"
    
# -------------------------------
# DONE
# -------------------------------
Write-Color "========================================" $GREEN
Write-Color "Deployment completed successfully!" $GREEN
Write-Color "========================================" $GREEN
Write-Color "Access the app at http://localhost:80" $CYAN
Write-Host "" -ForegroundColor Yellow
    Write-Host "Available Credentials:" -ForegroundColor Yellow
    Write-Host "  Superuser Admin:" -ForegroundColor White
    Write-Host "    Username: admin" -ForegroundColor Green
    Write-Host "    Password: admin" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
