#!/bin/bash

echo "=========================================="
echo "   MARUTHI REPOSITORY SETUP (MAC/LINUX)"
echo "=========================================="
echo ""

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "[1/5] Setting up environment variables..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "  Created backend/.env"
else
    echo "  backend/.env already exists."
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "  Created frontend/.env"
else
    echo "  frontend/.env already exists."
fi

echo ""
echo "[2/5] Setting up Python backend environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Created virtual environment."
fi
source venv/bin/activate
echo "  Installing backend dependencies (this may take a minute)..."
pip install -r ../requirements.txt > /dev/null
cd ..

echo ""
echo "[3/5] Setting up Node frontend environment..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  Installing frontend dependencies (this may take a minute)..."
    npm install > /dev/null
else
    echo "  node_modules already exists."
fi
cd ..

echo ""
echo "[4/5] Initializing Database and injecting Dummy Data..."
cd backend
python -c "from app.db.database import init_sqlite_db_and_seed; init_sqlite_db_and_seed()"
cd ..

echo ""
echo "[5/5] Running Backend Tests..."
source backend/venv/bin/activate
pytest

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "You can now run the app by executing ./START-MARUTHI.bat (Windows) or running the servers manually."
echo "=========================================="
