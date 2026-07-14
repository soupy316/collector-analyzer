#!/bin/bash

# Move automatically to the directory where this script is saved on the Mac
cd "$(dirname "$0")"

echo "--------------------------------------------------"
echo "⚡ Starting collector_analyzer Suite... "
echo "--------------------------------------------------"

# 1. Activate your local virtual environment isolated shell space
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run setup first."
    exit 1
fi

# 2. Kill any old hung processes sitting on our ports so it runs clean
kill -9 $(lsof -t -i:5001) 2>/dev/null
kill -9 $(lsof -t -i:3000) 2>/dev/null

# 3. Fire up the Python backend server in the background
python backend/app.py &
BACKEND_PID=$!

# 4. Wait a brief second for the API loop to stabilize
sleep 2

# 5. Spin up the frontend web interface web tier loop
python3 -m http.server 3000 --directory frontend &
FRONTEND_PID=$!

# 6. Smoothly force-open your default Mac web browser straight to the page
open "http://localhost:3000"

# Keep the terminal window open and gracefully handle shutdowns
echo "🚀 Application is Live at http://localhost:3000"
echo "Press [Ctrl + C] inside this window to shut down both server tiers."
echo "--------------------------------------------------"

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait