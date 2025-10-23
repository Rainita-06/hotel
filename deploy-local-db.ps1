# Hotel Project Deployment Script for Windows - Local Database Version

param(
    [Parameter(Mandatory=$false)]
    [string]$EnvFile = ".env.local"
)

Write-Host "=== Hotel Project Deployment - Local Database Version ===" -ForegroundColor Green
Write-Host ""

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

# Check if docker-compose.local-db.yml exists
if (-Not (Test-Path "docker-compose.local-db.yml")) {
    Write-Host "docker-compose.local-db.yml not found. Please ensure you're in the correct directory." -ForegroundColor Red
    exit 1
}

# Check if .env.local file exists, if not copy from .env.production
if (-Not (Test-Path $EnvFile)) {
    Write-Host "Creating $EnvFile file from .env.production template..." -ForegroundColor Yellow
    Copy-Item ".env.production" $EnvFile
    Write-Host "Please update the $EnvFile file with your local database configuration and run this script again." -ForegroundColor Yellow
    Write-Host "Required updates:" -ForegroundColor Yellow
    Write-Host "1. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details" -ForegroundColor Yellow
    Write-Host "2. Set DB_HOST=host.docker.internal to connect to your local database" -ForegroundColor Yellow
    exit 1
}

# Display current database configuration
Write-Host "Current database configuration in $EnvFile:" -ForegroundColor Yellow
$envContent = Get-Content $EnvFile
$dbName = ($envContent | Where-Object { $_ -match "^DB_NAME=(.*)$" }) -replace "^DB_NAME=", ""
$dbUser = ($envContent | Where-Object { $_ -match "^DB_USER=(.*)$" }) -replace "^DB_USER=", ""
$dbHost = ($envContent | Where-Object { $_ -match "^DB_HOST=(.*)$" }) -replace "^DB_HOST=", ""

Write-Host "  Database Name: $dbName" -ForegroundColor Cyan
Write-Host "  Database User: $dbUser" -ForegroundColor Cyan
Write-Host "  Database Host: $dbHost" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
Write-Host "Ready to deploy Django container connected to your local database." -ForegroundColor Yellow
Write-Host "Make sure your local database is running and accessible." -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Do you want to continue? (y/N)"

if ($confirmation -ne "y" -and $confirmation -ne "Y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local-db.yml down

# Build and start services
Write-Host "Building and starting Docker containers with local database connection..." -ForegroundColor Green
docker-compose -f docker-compose.local-db.yml --env-file $EnvFile up -d --build

# Wait for services to be healthy
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Show status
Write-Host "Deployment status:" -ForegroundColor Green
docker-compose -f docker-compose.local-db.yml ps

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Access the application at http://localhost:8000" -ForegroundColor Cyan
Write-Host "To create a superuser, run: docker exec -it hotel_web_local python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host "To view logs, run: docker-compose -f docker-compose.local-db.yml logs -f" -ForegroundColor Cyan