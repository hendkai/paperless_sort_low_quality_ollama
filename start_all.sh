#!/bin/bash
cd "$(dirname "$0")"

echo "Starting services..." > service_status.log

# Start Backend
echo "Launching Backend..." >> service_status.log
./start_backend.sh >> backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID" >> service_status.log

# Wait for backend to be potentially ready
sleep 2

# Start Frontend
echo "Launching Frontend..." >> service_status.log
cd gui
npx vite --host >> frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID" >> service_status.log

# Trap cleanup
cleanup() {
    echo "Stopping services..." >> service_status.log
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT SIGTERM

# Keep alive
echo "Services running. Waiting..." >> service_status.log
wait
