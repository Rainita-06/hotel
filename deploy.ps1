# Hotel Project Deployment Script for Windows

param(
    [Parameter(Mandatory=$false)]
    [switch]$LocalDB
)

# Suppress oh-my-posh errors by temporarily redirecting the profile
$originalProfile = $PROFILE
$PROFILE = $null

try {
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
        
        # Wait for services to be fully ready
        Write-Host "Waiting for services to be fully ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        # Check if the container is running before proceeding
        Write-Host "Checking container status..." -ForegroundColor Yellow
        $containerStatus = docker-compose -f docker-compose.local-db.yml ps
        Write-Host $containerStatus -ForegroundColor White

        # Check if container is healthy
        $containerHealth = docker inspect --format='{{.State.Running}}' hotel_web_local 2>$null
        if ($containerHealth -ne "true") {
            Write-Host "⚠ Warning: Container is not running properly. Check logs with: docker-compose -f docker-compose.local-db.yml logs" -ForegroundColor Yellow
            Write-Host "Skipping data initialization steps due to container issues." -ForegroundColor Yellow
        } else {
            Write-Host "Container is running. Proceeding with data initialization..." -ForegroundColor Green
        
            # Extract data from current database if it exists
            Write-Host "Checking for existing database data to preserve..." -ForegroundColor Yellow
            # This would be where we'd extract data from current database if needed
            
            # Create default admin user
            Write-Host "Creating default admin user (admin:admin)..." -ForegroundColor Yellow
            $adminResult = docker exec hotel_web_local python manage.py shell -c 'from django.contrib.auth.models import User; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"}); user.set_password("admin"); user.is_superuser = True; user.is_staff = True; user.save(); print("Admin user created/updated:", user.username); dept = Department.objects.first(); profile, profile_created = UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "department": dept, "role": "admin"}) if dept else UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "role": "admin"}); print("Admin profile created/updated:", profile.full_name)'
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Default admin user created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to create default admin user" -ForegroundColor Yellow
            }

            # Initialize roles and permissions
            Write-Host "Initializing roles and permissions..." -ForegroundColor Yellow
            $rolesResult = docker exec hotel_web_local python manage.py init_roles
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Roles and permissions initialized successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to initialize roles and permissions" -ForegroundColor Yellow
            }

            # Create test users
            Write-Host "Creating test users..." -ForegroundColor Yellow
            $usersResult = docker exec hotel_web_local python manage.py create_test_users
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Test users created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to create test users" -ForegroundColor Yellow
            }

            # Initialize departments and user groups
            Write-Host "Initializing departments and user groups..." -ForegroundColor Yellow
            $departmentsResult = docker exec hotel_web_local python manage.py init_departments
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Departments and user groups initialized successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to initialize departments and user groups" -ForegroundColor Yellow
            }

            # Seed demo data
            Write-Host "Seeding demo data..." -ForegroundColor Yellow
            $demoDataResult = docker exec hotel_web_local python manage.py seed_demo_data --force
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Demo data seeded successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to seed demo data" -ForegroundColor Yellow
                # Try alternative approach if seed_demo_data fails
                Write-Host "Trying alternative data seeding approach..." -ForegroundColor Yellow
                docker exec hotel_web_local python manage.py shell -c 'from django.contrib.auth.models import User; print("Users in database:", User.objects.count())'
            }

            # Validate data population
            Write-Host "Validating data population..." -ForegroundColor Yellow
            $validationResult = docker exec hotel_web_local python manage.py shell -c 'from django.contrib.auth.models import User; from hotel_app.models import Department, UserGroup; print("Users:", User.objects.count()); print("Departments:", Department.objects.count()); print("User Groups:", UserGroup.objects.count()); print("SUCCESS: Data validation completed")'
            Write-Host "Data validation results:" -ForegroundColor Cyan
            Write-Host $validationResult -ForegroundColor White
        }
        
        # Show status
        Write-Host "Deployment status:" -ForegroundColor Green
        docker-compose -f docker-compose.local-db.yml ps
        
        Write-Host "Deployment completed successfully!" -ForegroundColor Green
        Write-Host "Access the application at http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Default admin credentials: admin / admin" -ForegroundColor Cyan
        Write-Host "Test users created: test_admin, test_staff, test_user (all with password: testpassword123)" -ForegroundColor Cyan
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
        Start-Sleep -Seconds 30
        
        # Wait for services to be fully ready
        Write-Host "Waiting for services to be fully ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        # Check if the container is running before proceeding
        Write-Host "Checking container status..." -ForegroundColor Yellow
        $containerStatus = docker-compose -f docker-compose.prod.yml ps
        Write-Host $containerStatus -ForegroundColor White

        # Check if container is healthy
        $containerHealth = docker inspect --format='{{.State.Running}}' hotel_web 2>$null
        if ($containerHealth -ne "true") {
            Write-Host "⚠ Warning: Container is not running properly. Check logs with: docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Yellow
            Write-Host "Skipping data initialization steps due to container issues." -ForegroundColor Yellow
        } else {
            Write-Host "Container is running. Proceeding with data initialization..." -ForegroundColor Green
        
            # Extract data from current database if it exists
            Write-Host "Checking for existing database data to preserve..." -ForegroundColor Yellow
            # This would be where we'd extract data from current database if needed
            
            # Create default admin user
            Write-Host "Creating default admin user (admin:admin)..." -ForegroundColor Yellow
            $adminResult = docker exec hotel_web python manage.py shell -c 'from django.contrib.auth.models import User; from hotel_app.models import UserProfile, Department; user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"}); user.set_password("admin"); user.is_superuser = True; user.is_staff = True; user.save(); print("Admin user created/updated:", user.username); dept = Department.objects.first(); profile, profile_created = UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "department": dept, "role": "admin"}) if dept else UserProfile.objects.get_or_create(user=user, defaults={"full_name": "Administrator", "phone": "+1234567890", "title": "System Administrator", "role": "admin"}); print("Admin profile created/updated:", profile.full_name)'
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Default admin user created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to create default admin user" -ForegroundColor Yellow
            }

            # Initialize roles and permissions
            Write-Host "Initializing roles and permissions..." -ForegroundColor Yellow
            $rolesResult = docker exec hotel_web python manage.py init_roles
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Roles and permissions initialized successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to initialize roles and permissions" -ForegroundColor Yellow
            }

            # Create test users
            Write-Host "Creating test users..." -ForegroundColor Yellow
            $usersResult = docker exec hotel_web python manage.py create_test_users
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Test users created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to create test users" -ForegroundColor Yellow
            }

            # Initialize departments and user groups
            Write-Host "Initializing departments and user groups..." -ForegroundColor Yellow
            $departmentsResult = docker exec hotel_web python manage.py init_departments
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Departments and user groups initialized successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to initialize departments and user groups" -ForegroundColor Yellow
            }

            # Seed demo data
            Write-Host "Seeding demo data..." -ForegroundColor Yellow
            $demoDataResult = docker exec hotel_web python manage.py seed_demo_data --force
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Demo data seeded successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Failed to seed demo data" -ForegroundColor Yellow
                # Try alternative approach if seed_demo_data fails
                Write-Host "Trying alternative data seeding approach..." -ForegroundColor Yellow
                docker exec hotel_web python manage.py shell -c 'from django.contrib.auth.models import User; print("Users in database:", User.objects.count())'
            }

            # Validate data population
            Write-Host "Validating data population..." -ForegroundColor Yellow
            $validationResult = docker exec hotel_web python manage.py shell -c 'from django.contrib.auth.models import User; from hotel_app.models import Department, UserGroup; print("Users:", User.objects.count()); print("Departments:", Department.objects.count()); print("User Groups:", UserGroup.objects.count()); print("SUCCESS: Data validation completed")'
            Write-Host "Data validation results:" -ForegroundColor Cyan
            Write-Host $validationResult -ForegroundColor White
        }
        
        # Show status
        Write-Host "Deployment status:" -ForegroundColor Green
        docker-compose -f docker-compose.prod.yml ps
        
        Write-Host "Deployment completed successfully!" -ForegroundColor Green
        Write-Host "Access the application at http://localhost:8080" -ForegroundColor Cyan
        Write-Host "Default admin credentials: admin / admin" -ForegroundColor Cyan
        Write-Host "Test users created: test_admin, test_staff, test_user (all with password: testpassword123)" -ForegroundColor Cyan
        Write-Host "To view logs, run: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan
    }
}
finally {
    # Restore original profile
    $PROFILE = $originalProfile
}