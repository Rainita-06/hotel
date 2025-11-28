# Quick Fix Script for User Authentication Issues in Docker
# Run this if you're having login problems after deployment

Write-Host "Fixing user authentication issues..." -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if hotel_web container exists
$containerExists = docker ps -a --filter "name=hotel_web" --format "{{.Names}}"
if (-not $containerExists) {
    Write-Host "❌ hotel_web container not found. Please run deploy_simple.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Running user fix command..." -ForegroundColor Yellow
docker exec hotel_web python manage.py fix_users

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "User fix completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now login with these credentials:" -ForegroundColor Cyan
Write-Host "  admin       / admin           (Superuser)" -ForegroundColor Green
Write-Host "  test_admin  / testpassword123 (Admin)" -ForegroundColor Green
Write-Host "  test_staff  / testpassword123 (Staff)" -ForegroundColor Green
Write-Host "  test_user   / testpassword123 (User)" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application at: http://localhost:8080" -ForegroundColor Cyan
