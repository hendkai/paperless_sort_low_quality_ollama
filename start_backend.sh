#!/bin/bash
cd "$(dirname "$0")"

# Use the python binary inside venv directly to ensure correct env
PYTHON_BIN="./venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Python venv not found at $PYTHON_BIN"
    # Fallback to system python but print warning
    PYTHON_BIN="python3"
    echo "Falling back to system python3..."
fi

echo "Starting backend with $PYTHON_BIN..."
exec $PYTHON_BIN backend/server.py
