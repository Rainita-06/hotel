# Simple Hotel Project Deployment Script for Windows
# This script bypasses PowerShell profile issues and focuses on core deployment functionality

param(
    [Parameter(Mandatory=$false)]
    [switch]$LocalDB
)

if ($LocalDB) {
    Write-Host "Starting Hotel Project deployment with Local Database..." -ForegroundColor Green
    
    # Check if docker-compose.local-db.yml exists
    if (-Not (Test-Path "docker-compose.local-db.yml")) {
        Write-Host "docker-compose.local-db.yml not found. Please ensure you're in the correct directory." -ForegroundColor Red
        exit 1
    }       
    
    # Check if .env.local file exists, if not copy from .env.production
    if (-Not (Test-Path ".env.local")) {
        Write-Host "Creating .env.local file from .env.production template..." -ForegroundColor Yellow
        Copy-Item ".env.production" ".env.local"
        Write-Host "Please update the .env.local file with your local database configuration and run this script again with -LocalDB flag." -ForegroundColor Yellow
        Write-Host "Required updates:" -ForegroundColor Yellow
        Write-Host "1. Update DB_NAME, DB_USER,Human and DB_PASSWORD with your local database details" -ForegroundColor Yellow
        Write-Host "2. Set DB_HOST=host.docker.internal to connect to your local database" -ForegroundColor Yellow
        exit 1
    }
    
    # Stop any existing containers
    Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.local-db.yml down
    
    # Build and start services
    Write-Host "Building and starting Docker containers with local database connection..." -ForegroundColor Green
    docker-compose -f docker-compose.local-db.yml --env-file .env.local up -d --build
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Access the application at http://localhost:8000" -ForegroundColor Cyan
}
else {
    Write-Host "Starting Hotel Project deployment..." -ForegroundColor Green
    
    # Check if Docker is installed
    try {
        $dockerVersion = docker --version
        Write-Host "Docker is installed: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if Docker Compose is installed
    try {
        $composeVersion = docker-compose --version
        Write-Host "Docker Compose is installed: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "Docker Compose is not installed. Please install Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if .env file exists, if not copy from .env.production
    if (-Not (Test-Path ".env")) {
        Write-Host "Creating .env file from .env.production template..." -ForegroundColor Yellow
        Copy-Item ".env.production" ".env"
        Write-Host "Please update the .env file with your configuration and run this script again." -ForegroundColor Yellow
        exit 1
    }
    
    # Stop any existing containers
    Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml down
    
    # Build and start services
    Write-Host "Building and starting Docker containers..." -ForegroundColor Green
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Initialize data
    Write-Host "Initializing data..." -ForegroundColor Yellow
    
    # Wait a bit more for containers to be fully ready
    Start-Sleep -Seconds 15
    
    # Create default admin user
    Write-Host "Creating default admin user (admin:admin)..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py shell -c 'from django.contrib.auth.models import User; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"}); user.set_password("admin"); user.is_superuser = True; user.is_staff = True; user.save(); print("Admin user created/updated:", user.username); dept = Department.objects.first(); profile, profile_created = UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "department": dept, "role": "admin"}) if dept else UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "role": "admin"}); print("Admin profile created/updated:", profile.full_name)'
    
    # Initialize sections and permissions (Admins, Staff, Users groups)
    Write-Host "Initializing sections and permissions..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py init_sections
    
    # Create test users
    Write-Host "Creating test users..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py create_test_users
    
    # Initialize departments and user groups
    Write-Host "Initializing departments and user groups..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py init_departments
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Access the application at http://localhost:8080" -ForegroundColor Cyan
    Write-Host "Default admin credentials: admin / admin" -ForegroundColor Cyan
    Write-Host "Test users created: test_admin, test_staff, test_user (all with password: testpassword123)" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
    Write-Host "Permissions configured:" -ForegroundColor Yellow
    Write-Host "  - Admins: Full access to all sections" -ForegroundColor Green
    Write-Host "  - Staff: View access to all sections except Users" -ForegroundColor Green
    Write-Host "  - Users: Access only to My Tickets section" -ForegroundColor Green
}