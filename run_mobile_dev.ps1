# Mobile Development Server Script
Write-Host "Starting Django development server for mobile access..."
Write-Host "Make sure your mobile device is on the same network as your computer."
Write-Host "Access the server from your mobile device using: http://10.178.254.135:8000"
Write-Host ""

Set-Location "C:\xampp\htdocs\victoire_hotel\hotel_app"
env\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000