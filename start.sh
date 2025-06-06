#!/bin/bash

# Start script for the application
echo "🏦 Starting Automated Bank Check Processing System..."

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Streamlit app
echo "🚀 Launching Streamlit application..."
streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true
