#!/bin/bash
cd "$(dirname "$0")/gui"
# Run only Vite web server (no Electron)
npx vite --host
