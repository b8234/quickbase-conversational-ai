#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Quickbase Conversational AI...${NC}"

# Navigate to frontend directory
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${BLUE}Creating .env from example.env...${NC}"
    if [ -f ../example.env ]; then
        cp ../example.env .env
        echo -e "${GREEN}✅ .env created. Please configure it before running.${NC}"
        exit 1
    else
        echo -e "${RED}❌ example.env not found!${NC}"
        exit 1
    fi
fi

# Install dependencies if needed
if ! python -m streamlit --version &> /dev/null; then
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    pip install -q streamlit audio-recorder-streamlit python-dotenv requests
fi

# Stop any existing streamlit processes
pkill -f streamlit 2>/dev/null && echo -e "${BLUE}🛑 Stopped existing Streamlit process${NC}"

# Check if demo mode
DEMO_MODE=$(grep DEMO_MODE .env | cut -d '=' -f2 | tr -d ' ')
if [ "$DEMO_MODE" = "true" ]; then
    echo -e "${GREEN}🧪 Running in DEMO MODE${NC}"
else
    echo -e "${GREEN}🔴 Running in LIVE MODE${NC}"
fi

# Start Streamlit
echo -e "${BLUE}🌐 Starting Streamlit on http://0.0.0.0:8501${NC}"
echo ""
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
