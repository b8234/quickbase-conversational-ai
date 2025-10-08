#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🛑 Stopping Streamlit..."
pkill -f streamlit

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Streamlit stopped successfully${NC}"
else
    echo -e "${RED}ℹ️  No Streamlit process found${NC}"
fi
