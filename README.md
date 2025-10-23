# Hotel Management System

A comprehensive hotel management system with user role-based access control, voucher management, guest registration, and QR code functionality.

## Features

### User Role-Based Access Control

The system implements a robust permission system with three main user groups:

1. **Admins**: Full access to all features including user management, department management, and system configuration
2. **Staff**: Access to guest management, voucher operations, and operational features
3. **Users**: Limited access (currently not used in the UI)

#### Implementation Details

- Custom decorators for view-level permission checking
- Template tags for UI-level permission checking
- Context processors for global permission variables
- Navigation menu that dynamically shows/hides items based on user permissions
- **API-level permissions** with custom permission classes for fine-grained control

#### API Permission Structure

The API implements a comprehensive permission system with the following rules:

- **Admin Users**: Full access to all API endpoints including create, read, update, and delete operations
- **Staff Users**: Read and create access to operational endpoints (guests, vouchers, dashboard), but cannot delete or modify system configuration
- **Regular Users**: Limited or no access to most API endpoints

Specific API permissions include:
- **User Management**: Only admins can list, create, update, or delete users
- **Guest Management**: Staff and admins can view and create guests; only admins can modify existing guests
- **Voucher Management**: Staff and admins can view and create vouchers; only admins can modify or delete vouchers
- **Voucher Validation**: Only staff and admins can validate vouchers
- **Dashboard Access**: Only staff and admins can access dashboard analytics
- **System Configuration**: Only admins can manage departments, locations, user groups, etc.

### Voucher Management

- Multi-day voucher validation system
- QR code generation and storage as base64 strings in the database
- Voucher scanning with detailed audit logging
- Analytics dashboard for voucher usage tracking

### Guest Management

- Guest registration with automatic QR code generation
- Guest details management
- Check-in/check-out date tracking
- Breakfast inclusion tracking

### QR Code System

- Base64-encoded QR codes stored in database TextField fields
- QR codes generated on-demand with configurable sizes
- QR code regeneration functionality
- WhatsApp sharing integration

## Frontend Styling with Tailwind CSS

This project uses Tailwind CSS for styling the dashboard interface. For more information on how to set up and use Tailwind CSS, see [TAILWIND_SETUP.md](TAILWIND_SETUP.md).

Key features:
- Custom color palette matching the project's design system
- Pre-built components for buttons, cards, navigation, and more
- Responsive design utilities
- Custom component classes for consistent UI elements

You can initialize Tailwind CSS by running:
```bash
python init_tailwind.py
```

## Production-Ready Features

### Security

- Environment-based configuration
- Secure secret key management
- HTTPS enforcement in production
- Security headers (XSS protection, content type sniffing protection)
- HTTP Strict Transport Security (HSTS)
- **API-level authentication and authorization**

### Performance

- Static file serving with WhiteNoise
- Database connection pooling
- Caching strategies
- Optimized database queries

### Deployment

- Gunicorn application server support
- Docker-ready configuration
- Environment variable configuration
- Comprehensive deployment guide

## Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Initialize groups: `python manage.py init_groups`
8. Set up Tailwind CSS: 
   - Run the initialization script: `python init_tailwind.py`
   - Follow the instructions to install Node.js dependencies and build CSS
9. Run the server: `python manage.py runserver`

## User Groups Setup

To initialize the default user groups, run:
```bash
python manage.py init_groups
```

This creates the following groups:
- Admins
- Staff
- Users

## Docker Deployment

This project includes comprehensive Docker configuration for development and production environments.

### Quick Start with Docker

1. Install Docker and Docker Compose
2. Copy `.env.production` to `.env` and update values:
   ```bash
   cp .env.production .env
   # Edit .env file with your settings
   ```
3. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```
   Or start the production environment:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
4. Create a superuser:
   ```bash
   docker exec -it hotel_web_dev python manage.py createsuperuser
   ```

### Docker Environments

- **Development**: `docker-compose.dev.yml` - Includes hot reloading and development server
- **Production**: `docker-compose.prod.yml` - Includes Nginx reverse proxy and Gunicorn
- **Simple**: `docker-compose.simple.yml` - Basic setup with MySQL and Gunicorn
- **Full**: `docker-compose.yml` - Complete setup with Celery workers and Redis
- **Local Database**: `docker-compose.local-db.yml` - Django container only, connects to your local database (see [LOCAL_DB_SETUP.md](LOCAL_DB_SETUP.md))

### Data Migration

If you're migrating from an existing installation, see [DATA_MIGRATION_README.md](DATA_MIGRATION_README.md) for instructions on how to export your data and import it into the new Docker environment.

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed instructions on all deployment options.

## Testing

Run the test suite:
```bash
python manage.py test
```

## API Endpoints

The system provides a REST API for integration with external systems. See the API documentation for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is proprietary and confidential. All rights reserved.