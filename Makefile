# Makefile for Hotel Project Docker Operations

# Default environment
ENV ?= dev

# Docker Compose files
DEV_COMPOSE := docker-compose.dev.yml
PROD_COMPOSE := docker-compose.prod.yml
SIMPLE_COMPOSE := docker-compose.simple.yml

# Help target
help:
	@echo "Hotel Project Docker Commands"
	@echo "============================="
	@echo "make build              - Build Docker images"
	@echo "make up                 - Start development environment"
	@echo "make down               - Stop and remove containers"
	@echo "make logs               - View container logs"
	@echo "make shell              - Access web container shell"
	@echo "make migrate            - Run database migrations"
	@echo "make superuser          - Create superuser"
	@echo "make collectstatic      - Collect static files"
	@echo "make test               - Run tests in container"
	@echo "make prod-up            - Start production environment"
	@echo "make simple-up          - Start simple environment"
	@echo "make clean              - Remove containers and volumes"
	@echo ""
	@echo "Environment variables:"
	@echo "ENV=dev|prod|simple     - Set environment (default: dev)"

# Build images
build:
	docker-compose -f $(DEV_COMPOSE) build

# Start development environment
up:
	docker-compose -f $(DEV_COMPOSE) up -d

# Start production environment
prod-up:
	docker-compose -f $(PROD_COMPOSE) up -d

# Start simple environment
simple-up:
	docker-compose -f $(SIMPLE_COMPOSE) up -d

# Stop containers
down:
	docker-compose -f $(DEV_COMPOSE) down

# View logs
logs:
	docker-compose -f $(DEV_COMPOSE) logs -f

# Access web container shell
shell:
	docker exec -it hotel_web_dev bash

# Run migrations
migrate:
	docker exec hotel_web_dev python manage.py migrate

# Create superuser
superuser:
	docker exec -it hotel_web_dev python manage.py createsuperuser

# Collect static files
collectstatic:
	docker exec hotel_web_dev python manage.py collectstatic --noinput

# Run tests
test:
	docker exec hotel_web_dev python manage.py test

# Clean up (remove containers and volumes)
clean:
	docker-compose -f $(DEV_COMPOSE) down -v

# Production clean
prod-clean:
	docker-compose -f $(PROD_COMPOSE) down -v

# Simple clean
simple-clean:
	docker-compose -f $(SIMPLE_COMPOSE) down -v

.PHONY: help build up prod-up simple-up down logs shell migrate superuser collectstatic test clean prod-clean simple-clean