#!/bin/bash

# Production startup script
# Backend: port 8080, Frontend: static files served by nginx or similar

echo "Starting Kiro Honcho in production mode..."

# Start backend
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!
cd ..

echo ""
echo "🚀 Backend server running!"
echo "   API:     http://localhost:8080"
echo "   Docs:    http://localhost:8080/docs"
echo ""
echo "Frontend static files are in: frontend/dist/"
echo "Serve them with nginx or any static file server."

trap "kill $BACKEND_PID 2>/dev/null" EXIT

wait
