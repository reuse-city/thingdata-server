#!/bin/bash

# Stop all containers
echo "Stopping containers..."
docker compose down

# Remove all __pycache__ directories
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Clean up Docker resources
echo "Cleaning Docker resources..."
docker compose down -v --remove-orphans
docker system prune -f

# Remove temp files and logs
echo "Cleaning temporary files..."
rm -rf logs/*
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov

echo "Cleanup completed!"