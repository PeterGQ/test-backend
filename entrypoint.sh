#!/bin/sh

# This line ensures that the script will exit immediately if a command fails.
set -e

# Apply database migrations using the flask command directly
echo "Applying database migrations..."
flask db upgrade

# Start the Flask application using gunicorn
echo "Starting the application..."
gunicorn --bind 0.0.0.0:5000 --timeout 240 run:app

