#!/bin/bash
# Setup script for the WiFi Credentials Sender app

# Text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== WiFi Credentials Sender Setup =====${NC}"
echo "This script will set up all dependencies for the application."

# Check if Node.js is installed
echo -e "\n${BLUE}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed.${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}Node.js is installed (${NODE_VERSION})${NC}"
fi

# Check if npm is installed
echo -e "\n${BLUE}Checking npm installation...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is not installed.${NC}"
    echo "Please install npm (it usually comes with Node.js)"
    exit 1
else
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}npm is installed (${NPM_VERSION})${NC}"
fi

# Check if Python is installed
echo -e "\n${BLUE}Checking Python installation...${NC}"
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}${PYTHON_VERSION} is installed${NC}"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        PYTHON_CMD="python"
        echo -e "${GREEN}${PYTHON_VERSION} is installed${NC}"
    else
        echo -e "${RED}Python 3 is required, but found: ${PYTHON_VERSION}${NC}"
        echo "Please install Python 3"
        exit 1
    fi
else
    echo -e "${RED}Python is not installed.${NC}"
    echo "Please install Python 3"
    exit 1
fi

# Check Python Bluetooth support
echo -e "\n${BLUE}Checking Python Bluetooth support...${NC}"
BLUETOOTH_SUPPORT=$($PYTHON_CMD -c "
import socket
try:
    socket.AF_BLUETOOTH
    print('Available')
except AttributeError:
    print('Not available')
" 2>/dev/null)

if [ "$BLUETOOTH_SUPPORT" = "Available" ]; then
    echo -e "${GREEN}Python Bluetooth support is available${NC}"
else
    echo -e "${RED}Python Bluetooth support is not available${NC}"
    
    # Detect OS and provide instructions
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "On Linux, install the required packages with:"
        echo "  sudo apt-get install bluetooth bluez libbluetooth-dev"
        echo "  sudo setcap 'cap_net_raw,cap_net_admin+eip' \$(which $PYTHON_CMD)"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "On macOS, install the PyBluez package with:"
        echo "  pip install pybluez"
        echo "You may need to install Xcode Command Line Tools:"
        echo "  xcode-select --install"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "On Windows, install the PyBluez package with:"
        echo "  pip install pybluez"
        echo "You may need to install additional drivers for your Bluetooth adapter"
    fi
    
    echo -e "\nContinuing setup, but Bluetooth functionality may not work."
fi

# Install Python dependencies
echo -e "\n${BLUE}Installing Python dependencies...${NC}"
$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Python dependencies installed successfully${NC}"
else
    echo -e "${RED}Failed to install Python dependencies${NC}"
    exit 1
fi

# Install Node.js dependencies
echo -e "\n${BLUE}Installing Node.js dependencies...${NC}"
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Node.js dependencies installed successfully${NC}"
else
    echo -e "${RED}Failed to install Node.js dependencies${NC}"
    exit 1
fi

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo "You can now run the application with: npm start"