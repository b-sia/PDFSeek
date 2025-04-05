#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt --no-cache-dir

# Create necessary directories
mkdir -p logs
mkdir -p sessions
mkdir -p models
mkdir -p vector_store

# Copy environment variables template if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template. Please update the values."
fi

# Set up pre-commit hooks
pip install pre-commit
pre-commit install

echo "Backend setup complete. Please update the .env file with your configuration." 