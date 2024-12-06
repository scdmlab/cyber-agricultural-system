#!/bin/bash

echo "Building frontend..."
npm run build

echo "Starting production server..."
cd backend
# Add error handling and environment check
if [ -f "gunicorn_config.py" ]; then
    gunicorn main:app -c gunicorn_config.py
else
    echo "Error: gunicorn_config.py not found"
    exit 1
fi 