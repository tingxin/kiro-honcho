#!/bin/bash

# Start both backend and frontend in development mode
# Backend: port 8080, Frontend: port 5020

# Start backend
echo "Starting backend on port 8080..."
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
echo "Starting frontend on port 5020..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🚀 Development servers running!"
echo "   Backend:  http://localhost:8080"
echo "   API Docs: http://localhost:8080/docs"
echo "   Frontend: http://localhost:5020"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Trap to kill both processes on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
