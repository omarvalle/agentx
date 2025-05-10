#!/bin/bash

# Define path to the app directory
APP_DIR="./app_project_1746588204_web"
cd "$APP_DIR"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "[INFO] Creating .env file from .env.example"
    cp .env.example .env
fi

# Install dependencies if node_modules doesn't exist or package.json was modified
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-json-check" ]; then
    echo "[INFO] Installing dependencies..."
    npm install
    touch node_modules/.package-json-check
fi

# Ensure the app binds to 0.0.0.0 to allow connections from Windows host
echo "[INFO] Starting Todo app on 0.0.0.0:3000..."

# Export HOST and PORT variables to ensure external visibility
export HOST=0.0.0.0
export PORT=3000

# Start the app
node server.js

echo "[INFO] App stopped." 