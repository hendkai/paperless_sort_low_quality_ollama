#!/bin/bash
cd "$(dirname "$0")/gui"

# Build once (skip if already built)
if [ ! -d "dist" ]; then
    echo "Building production bundle..."
    npm run build --only-web 2>/dev/null || npx vite build
fi

# Serve the production build (no HMR, no auto-refresh)
echo "Starting production server on port 5173..."
npx vite preview --host --port 5173
