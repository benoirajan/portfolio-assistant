#!/usr/bin/env bash

# ==============================================================================
# Portfolio Assistant - Development Startup Script
# Automatically executes unit tests and database migrations before boot.
# ==============================================================================

set -e

# Change to the directory of this script (backend/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN} 🚀 Portfolio Assistant Backend Startup Pipeline${NC}"
echo -e "${CYAN}======================================================${NC}"

# Detect Python interpreter
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    ALEMBIC=".venv/bin/alembic"
    UVICORN=".venv/bin/uvicorn"
else
    PYTHON="python3"
    ALEMBIC="alembic"
    UVICORN="uvicorn"
fi

# Step 1: Run Unit Tests
echo -e "\n${YELLOW}[Step 1/3] 🧪 Running Backend Unit Tests...${NC}"
export PYTHONPATH=.
if $PYTHON -m unittest discover -s tests -p "test_*.py"; then
    echo -e "${GREEN}✓ All unit tests passed successfully!${NC}"
else
    echo -e "${RED}✗ Unit tests failed! Aborting server boot.${NC}"
    exit 1
fi

# Step 2: Run Alembic Database Migrations
echo -e "\n${YELLOW}[Step 2/3] 🗄️ Checking & Applying Database Migrations...${NC}"
if $ALEMBIC upgrade head; then
    echo -e "${GREEN}✓ Database schema is up to date!${NC}"
else
    echo -e "${YELLOW}⚠ Alembic migration warning (offline/fallback mode active)${NC}"
fi

# Step 3: Start FastAPI Application Server
echo -e "\n${YELLOW}[Step 3/3] 🌐 Launching FastAPI Server with Hot Reload...${NC}"
echo -e "${GREEN}API Docs available at: http://127.0.0.1:8000/docs${NC}"
echo -e "${GREEN}Health probe at:      http://127.0.0.1:8000/health${NC}"
echo -e "${CYAN}------------------------------------------------------${NC}\n"

exec $UVICORN src.main:app --host 127.0.0.1 --port 8000 --reload
