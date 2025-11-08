#!/bin/bash

# Truth Quest - Quick Start Script

echo "🚀 Truth Quest Setup"
echo "===================="
echo ""

# Check if Firebase credentials exist
if [ ! -f "backend/serviceAccountKey.json" ]; then
    echo "❌ Firebase service account key not found!"
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://console.firebase.google.com/"
    echo "2. Select 'truth-quest' project"
    echo "3. Go to Project Settings → Service Accounts"
    echo "4. Click 'Generate new private key'"
    echo "5. Save as backend/serviceAccountKey.json"
    echo ""
    echo "See FIREBASE_SETUP.md for detailed instructions"
    exit 1
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found!"
    echo ""
    echo "Please create backend/.env with:"
    echo "OPENAI_API_KEY=your_key"
    echo "BRAVE_API_KEY=your_key"
    echo "YOUTUBE_API_KEY=your_key"
    echo "GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json"
    exit 1
fi

echo "✅ Credentials found!"
echo ""

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "✅ Backend ready!"
echo ""

# Setup frontend
cd ../frontend
echo "📦 Setting up frontend..."

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install > /dev/null 2>&1
fi

echo "✅ Frontend ready!"
echo ""

# Start servers
echo "🎬 Starting servers..."
echo ""
echo "Backend: http://localhost:3001"
echo "Frontend: http://localhost:5173"
echo ""

# Start backend in background
cd ../backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!

# Start frontend in foreground
cd ../frontend
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
