# Hotel Project - Start with Local Database
# This script ensures proper setup and starts the application

Write-Host "=== Hotel Project - Starting with Local Database ===" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "Error: .env.local file not found" -ForegroundColor Red
    Write-Host "Please run setup-local-db.ps1 first to configure your local database connection." -ForegroundColor Yellow
    exit 1
}

# Check if database credentials are properly configured
Write-Host "Checking database configuration..." -ForegroundColor Yellow
$envContent = Get-Content ".env.local"
$dbName = ($envContent | Where-Object { $_ -match "^DB_NAME=(.*)$" }) -replace "^DB_NAME=", ""
$dbUser = ($envContent | Where-Object { $_ -match "^DB_USER=(.*)$" }) -replace "^DB_USER=", ""
$dbPassword = ($envContent | Where-Object { $_ -match "^DB_PASSWORD=(.*)$" }) -replace "^DB_PASSWORD=", ""

if ($dbName -eq "your_local_database_name" -or $dbUser -eq "your_local_db_user" -or $dbPassword -eq "your_local_db_password") {
    Write-Host "Error: Database credentials not properly configured in .env.local" -ForegroundColor Red
    Write-Host "Please update the .env.local file with your actual database credentials:" -ForegroundColor Yellow
    Write-Host "1. Open .env.local in a text editor" -ForegroundColor Yellow
    Write-Host "2. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details" -ForegroundColor Yellow
    Write-Host "3. Save the file and run this script again" -ForegroundColor Yellow
    exit 1
}

Write-Host "Database configuration looks good:" -ForegroundColor Green
Write-Host "  Database Name: $dbName" -ForegroundColor Cyan
Write-Host "  Database User: $dbUser" -ForegroundColor Cyan
Write-Host ""

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local-db.yml down

# Start the application
Write-Host "Starting application with local database connection..." -ForegroundColor Yellow
docker-compose -f docker-compose.local-db.yml --env-file .env.local up -d --build

# Wait for containers to start
Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if containers are running
$containerStatus = docker-compose -f docker-compose.local-db.yml ps
Write-Host "Container status:" -ForegroundColor Yellow
Write-Host $containerStatus -ForegroundColor Cyan

Write-Host ""
Write-Host "=== Application Started Successfully ===" -ForegroundColor Green
Write-Host "Access your application at: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "To create users, run one of the following commands:" -ForegroundColor Yellow
Write-Host "  For a superuser: docker exec -it hotel_web_local python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host "  For test users:  docker exec -it hotel_web_local python manage.py create_test_users" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker-compose -f docker-compose.local-db.yml logs -f" -ForegroundColor Yellow
Write-Host "To stop: docker-compose -f docker-compose.local-db.yml down" -ForegroundColor Yellow