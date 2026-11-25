#!/bin/bash
# DigitalMaker AI - Startup Script

cd "$(dirname "$0")"
echo "=========================================================="
echo "⚡ Starting DigitalMaker AI (Google Flow + ChatGPT Edition)"
echo "=========================================================="
echo "Server URL: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo "----------------------------------------------------------"

python3 backend/app.py
