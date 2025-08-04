.PHONY: up down build migrate migrate-up migrate-down seed clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make build           - Build all services"
	@echo "  make migrate         - Run database migrations"
	@echo "  make migrate-up      - Run migrations up"
	@echo "  make migrate-down    - Roll back migrations"
	@echo "  make seed            - Seed the database with sample data"
	@echo "  make clean           - Remove all containers and volumes"

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Build all services
build:
	docker-compose build

# Run database migrations
migrate: migrate-up

# Run migrations up
migrate-up:
	docker-compose run --rm backend alembic upgrade head

# Roll back migrations
migrate-down:
	docker-compose run --rm backend alembic downgrade -1

# Seed the database with sample data
seed:
	docker-compose run --rm backend python -m scripts.seed_db

# Remove all containers and volumes
clean:
	docker-compose down -v
