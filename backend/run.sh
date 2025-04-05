#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 