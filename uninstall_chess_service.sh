#!/bin/bash
# Uninstallation script for MAGIC Chess Board service

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}MAGIC Chess Board Service Uninstaller${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./uninstall_chess_service.sh"
    exit 1
fi

# Check if service exists
if [ ! -f /etc/systemd/system/chess-game.service ]; then
    echo -e "${YELLOW}Service is not installed.${NC}"
    exit 0
fi

echo -e "${YELLOW}Step 1: Stopping chess-game service...${NC}"
systemctl stop chess-game.service 2>/dev/null || true
echo -e "${GREEN}✓ Service stopped${NC}"

echo ""
echo -e "${YELLOW}Step 2: Disabling service from boot...${NC}"
systemctl disable chess-game.service 2>/dev/null || true
echo -e "${GREEN}✓ Service disabled${NC}"

echo ""
echo -e "${YELLOW}Step 3: Removing service file...${NC}"
rm -f /etc/systemd/system/chess-game.service
echo -e "${GREEN}✓ Service file removed${NC}"

echo ""
echo -e "${YELLOW}Step 4: Reloading systemd daemon...${NC}"
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true
echo -e "${GREEN}✓ Daemon reloaded${NC}"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${GREEN}The chess game service has been removed and will not start on boot.${NC}"
