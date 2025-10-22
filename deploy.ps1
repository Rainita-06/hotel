# Hotel Project Deployment Script for Windows

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