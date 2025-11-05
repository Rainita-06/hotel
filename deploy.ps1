# Hotel Project Deployment Script for Windows

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
        Write-Host "1. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details" -ForegroundColor Yellow
        Write-Host "2. Set DB_HOST=host.docker.internal to connect to your local database" -ForegroundColor Yellow
        exit 1
    }
    
    # Display current database configuration
    Write-Host "Current database configuration in .env.local:" -ForegroundColor Yellow
    $envContent = Get-Content ".env.local"
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
    docker-compose -f docker-compose.local-db.yml --env-file .env.local up -d --build
    
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
    
    # Build and start services
    Write-Host "Building and starting Docker containers..." -ForegroundColor Green
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Show status
    Write-Host "Deployment status:" -ForegroundColor Green
    docker-compose -f docker-compose.prod.yml ps
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Access the application at http://localhost" -ForegroundColor Cyan
    Write-Host "To create a superuser, run: docker exec -it hotel_web python manage.py createsuperuser" -ForegroundColor Cyan
    Write-Host "To view logs, run: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan
}