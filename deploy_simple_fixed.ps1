# Simple Hotel Project Deployment Script for Windows
# This script bypasses PowerShell profile issues and focuses on core deployment functionality

param(
    [Parameter(Mandatory = $false)]
    [switch]$LocalDB
)

if ($LocalDB) {
    Write-Host "Starting Hotel Project deployment with Local Database..." -ForegroundColor Green
    
    # Check if docker-compose.local-db.yml exists
    if (-Not (Test-Path "docker-compose.local-db.yml")) {
        Write-Host "docker-compose.local-db.yml not found. Please ensure you're in the correct directory." -ForegroundColor Red
        exit 1
    }       
    
    # Check if .env.local file exists, if not copy from .env.example
    if (-Not (Test-Path ".env.local")) {
        Write-Host "Creating .env.local file from .env.example template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env.local"
        Write-Host "Please update the .env.local file with your local database configuration and run this script again with -LocalDB flag." -ForegroundColor Yellow
        Write-Host "Required updates:" -ForegroundColor Yellow
        Write-Host "1. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details" -ForegroundColor Yellow
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
    }
    catch {
        Write-Host "Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if Docker Compose is installed
    try {
        $composeVersion = docker-compose --version
        Write-Host "Docker Compose is installed: $composeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Docker Compose is not installed. Please install Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if .env file exists, if not copy from .env.example
    if (-Not (Test-Path ".env")) {
        Write-Host "Creating .env file from .env.example template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
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
    
    # Additional wait to ensure database is fully initialized
    Write-Host "Ensuring database is fully initialized..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Check if database is accessible
    Write-Host "Checking database connectivity..." -ForegroundColor Yellow
    $dbCheck = docker exec hotel_web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Database connection failed. Retrying after additional wait..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        $dbCheck = docker exec hotel_web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Database connection still failing. Please check the logs." -ForegroundColor Red
            docker logs hotel_db
            exit 1
        }
    }
    
    Write-Host "Database connection verified successfully." -ForegroundColor Green
    
    # Initialize data
    Write-Host "Initializing data..." -ForegroundColor Yellow
    
    # Wait a bit more for containers to be fully ready
    Start-Sleep -Seconds 15
    
    # CRITICAL: Run database migrations FIRST
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py migrate
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration failed. Please check the logs." -ForegroundColor Red
        docker logs hotel_web
        exit 1
    }
    
    Write-Host "Migrations completed successfully." -ForegroundColor Green
    
    # STEP 1: Initialize sections and permissions FIRST (creates groups)
    Write-Host "Step 1: Initializing sections and permissions..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py init_sections
    
    # STEP 2: Initialize departments
    Write-Host "Step 2: Initializing departments..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py init_departments
    
    # STEP 3: Create admin user and add to Admins group
    Write-Host "Step 3: Creating default admin user (admin:admin)..." -ForegroundColor Yellow
    docker exec hotel_web python manage.py shell -c "from django.contrib.auth.models import User, Group; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); user.set_password('admin'); user.is_superuser = True; user.is_staff = True; user.save(); user.groups.clear(); admin_group = Group.objects.get(name='Admins'); user.groups.add(admin_group); print('Admin user created/updated and added to Admins group:', user.username); dept = Department.objects.first(); profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'full_name': 'Administrator', 'phone': '+1234567890', 'title': 'System Administrator', 'department': dept, 'role': 'admin'}); print('Admin profile:', profile.full_name)"
    
    # STEP 4: Create test users
    Write-Host "Step 4: Creating test users..." -ForegroundColor Yellow
    # docker exec hotel_web python manage.py sample_tickets
    docker exec hotel_web python manage.py sample_gym,feed
    docker exec hotel_web python manage.py create_test_users
    
    Write-Host "" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "" -ForegroundColor Cyan
    Write-Host "Access the application at http://localhost:8080" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Available Credentials:" -ForegroundColor Yellow
    Write-Host "  Superuser Admin:" -ForegroundColor White
    Write-Host "    Username: admin" -ForegroundColor Green
    Write-Host "    Password: admin" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
    Write-Host "  Test Users:" -ForegroundColor White
    Write-Host "    Admin:  test_admin  / testpassword123" -ForegroundColor Green
    Write-Host "    Staff:  test_staff  / testpassword123" -ForegroundColor Green
    Write-Host "    User:   test_user   / testpassword123" -ForegroundColor Green
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Permissions configured:" -ForegroundColor Yellow
    Write-Host "  - Admins: Full access to all sections" -ForegroundColor Green
    Write-Host "  - Users: Access to all sections except Users" -ForegroundColor Green
    Write-Host "  - Staff: Access only to My Tickets section" -ForegroundColor Green
    Write-Host "" -ForegroundColor Cyan
}