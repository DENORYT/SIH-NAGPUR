#!/bin/bash

echo "========================================================"
echo "  SHADOWLINK ENTERPRISE - UNIFIED LAUNCHER"
echo "========================================================"
echo ""
echo "Starting the FastAPI server (Backend + Frontend)..."

cd backend

# Start the uvicorn server in the background
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

echo "Waiting for the server to initialize..."
sleep 3

echo "Opening the dashboard in your default web browser..."
if which xdg-open > /dev/null
then
  xdg-open http://127.0.0.1:8000/
elif which open > /dev/null
then
  open http://127.0.0.1:8000/
fi

echo ""
echo "========================================================"
echo "System is running!"
echo "Press [CTRL+C] to stop the server and exit."
echo "========================================================"

# Keep script running to hold the background process, kill it on exit
trap "kill $SERVER_PID" EXIT
wait
