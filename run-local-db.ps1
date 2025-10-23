# Hotel Project - Run Django with Local Database
# This script runs Django in Docker connected to your local database

param(
    [Parameter(Mandatory=$false)]
    [string]$EnvFile = ".env.local"
)

Write-Host "=== Hotel Project - Django with Local Database ===" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is running
Write-Host "Checking Docker daemon..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info
    Write-Host "Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose.local-db.yml exists
if (-not (Test-Path "docker-compose.local-db.yml")) {
    Write-Host "Error: docker-compose.local-db.yml not found" -ForegroundColor Red
    Write-Host "Please ensure you're running this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

# Check if environment file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "Environment file not found: $EnvFile" -ForegroundColor Yellow
    Write-Host "Creating a template file..." -ForegroundColor Yellow
    
    # Create a template if it doesn't exist
    Copy-Item ".env.production" ".env.local" -ErrorAction SilentlyContinue
    Write-Host "Created .env.local from .env.production template" -ForegroundColor Green
    Write-Host "Please update .env.local with your local database credentials:" -ForegroundColor Yellow
    Write-Host "1. Open .env.local in a text editor" -ForegroundColor Yellow
    Write-Host "2. Update DB_NAME, DB_USER, and DB_PASSWORD with your local database details" -ForegroundColor Yellow
    Write-Host "3. Save the file and run this script again" -ForegroundColor Yellow
    exit 1
}

# Display current database configuration
Write-Host "Current database configuration:" -ForegroundColor Yellow
$envContent = Get-Content $EnvFile
$dbName = ($envContent | Where-Object { $_ -match "^DB_NAME=(.*)$" }) -replace "^DB_NAME=", ""
$dbUser = ($envContent | Where-Object { $_ -match "^DB_USER=(.*)$" }) -replace "^DB_USER=", ""
$dbHost = ($envContent | Where-Object { $_ -match "^DB_HOST=(.*)$" }) -replace "^DB_HOST=", ""

Write-Host "  Database Name: $dbName" -ForegroundColor Cyan
Write-Host "  Database User: $dbUser" -ForegroundColor Cyan
Write-Host "  Database Host: $dbHost" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
Write-Host "Ready to start Django container connected to your local database." -ForegroundColor Yellow
Write-Host "Make sure your local database is running and accessible." -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Do you want to continue? (y/N)"

if ($confirmation -ne "y" -and $confirmation -ne "Y") {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local-db.yml down

# Start the containers
Write-Host "Starting Django container..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run to build the container." -ForegroundColor Yellow
Write-Host ""

try {
    # Run docker-compose with the local database configuration
    docker-compose -f docker-compose.local-db.yml --env-file $EnvFile up --build
    
    Write-Host ""
    Write-Host "Django container has been stopped." -ForegroundColor Green
    Write-Host "To restart, simply run this script again." -ForegroundColor Yellow
} catch {
    Write-Host "Error occurred while starting containers:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Script completed ===" -ForegroundColor Green