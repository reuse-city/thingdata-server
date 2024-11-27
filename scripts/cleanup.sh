#!/bin/bash

# Stop all containers
echo "Stopping all containers..."
docker compose down

# Remove all volumes
echo "Removing volumes..."
docker compose down -v

# Clean up old files
echo "Cleaning up old files..."
rm -rf migrations
rm -f alembic.ini
rm -rf logs/*
rm -rf app/__pycache__
rm -rf app/**/__pycache__

# Clean up docker
echo "Cleaning up Docker..."
docker system prune -f

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p app/static

echo "Cleanup complete. You can now run 'docker compose up --build' to start fresh."
