# Hotel Project - Local Database Setup Script

Write-Host "=== Hotel Project - Local Database Setup ===" -ForegroundColor Green
Write-Host ""

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local file from example..." -ForegroundColor Yellow
    if (Test-Path ".env.local.example") {
        Copy-Item ".env.local.example" ".env.local"
        Write-Host ".env.local created from .env.local.example template" -ForegroundColor Green
    } else {
        Copy-Item ".env.production" ".env.local"
        Write-Host ".env.local created from .env.production template" -ForegroundColor Green
    }
}

Write-Host "Please update the .env.local file with your local database credentials:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Open .env.local in a text editor" -ForegroundColor Yellow
Write-Host "2. Update the following values:" -ForegroundColor Yellow
Write-Host "   - DB_NAME: Your local database name" -ForegroundColor Yellow
Write-Host "   - DB_USER: Your local database username" -ForegroundColor Yellow
Write-Host "   - DB_PASSWORD: Your local database password" -ForegroundColor Yellow
Write-Host ""
Write-Host "Example:" -ForegroundColor Yellow
Write-Host "DB_NAME=hotel_management" -ForegroundColor Cyan
Write-Host "DB_USER=hotel_user" -ForegroundColor Cyan
Write-Host "DB_PASSWORD=secure_password123" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Save the file" -ForegroundColor Yellow
Write-Host "4. Run '.\start-local-db.ps1' to start the application" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== Database Configuration Instructions ===" -ForegroundColor Green
Write-Host "Make sure your local MySQL database is configured to accept external connections:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Edit your MySQL configuration file (my.ini or my.cnf)" -ForegroundColor Yellow
Write-Host "2. Add or modify the following line:" -ForegroundColor Yellow
Write-Host "   bind-address = 0.0.0.0" -ForegroundColor Cyan
Write-Host "3. Restart your MySQL service" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Create a database user for Docker connections:" -ForegroundColor Yellow
Write-Host "   CREATE USER 'hotel_user'@'%' IDENTIFIED BY 'secure_password123';" -ForegroundColor Cyan
Write-Host "   GRANT ALL PRIVILEGES ON hotel_management.* TO 'hotel_user'@'%';" -ForegroundColor Cyan
Write-Host "   FLUSH PRIVILEGES;" -ForegroundColor Cyan
Write-Host ""

Write-Host "After completing these steps, run '.\start-local-db.ps1' to start your application." -ForegroundColor Green