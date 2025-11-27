#!/bin/bash

# Voice Chat Agent - Production Start Script
set -e

echo "Starting Voice Chat Agent API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using system environment variables."
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run database migrations if any (placeholder for future use)
# echo "Running migrations..."
# python -m app.migrations

# Start the server
echo "Starting Uvicorn server on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --access-log \
    --log-level info