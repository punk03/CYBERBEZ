#!/bin/bash

# Script to run the application

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Start Docker Compose services
echo "Starting Docker Compose services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "Checking services status..."
docker-compose ps

# Run the application
echo "Starting FastAPI application..."
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
