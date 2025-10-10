#!/bin/bash
# Installation script for MAGIC Chess Board service

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}MAGIC Chess Board Service Installer${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./install_chess_service.sh"
    exit 1
fi

# Get the actual user who invoked sudo
ACTUAL_USER="${SUDO_USER:-$USER}"
echo -e "${YELLOW}Installing service for user: $ACTUAL_USER${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}Project directory: $SCRIPT_DIR${NC}"

# Update the service file with the actual paths
SERVICE_FILE="$SCRIPT_DIR/chess-game.service"
TEMP_SERVICE_FILE="/tmp/chess-game.service.tmp"

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}Error: chess-game.service not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Replace placeholder paths with actual paths
sed "s|/home/magicpi/MAGIC---FYP|$SCRIPT_DIR|g" "$SERVICE_FILE" > "$TEMP_SERVICE_FILE"
sed -i "s|User=magicpi|User=$ACTUAL_USER|g" "$TEMP_SERVICE_FILE"
sed -i "s|Group=magicpi|Group=$ACTUAL_USER|g" "$TEMP_SERVICE_FILE"

echo ""
echo -e "${YELLOW}Step 1: Copying service file to systemd directory...${NC}"
cp "$TEMP_SERVICE_FILE" /etc/systemd/system/chess-game.service
rm "$TEMP_SERVICE_FILE"
echo -e "${GREEN}✓ Service file copied${NC}"

echo ""
echo -e "${YELLOW}Step 2: Setting correct permissions...${NC}"
chmod 644 /etc/systemd/system/chess-game.service
echo -e "${GREEN}✓ Permissions set${NC}"

echo ""
echo -e "${YELLOW}Step 3: Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Daemon reloaded${NC}"

echo ""
echo -e "${YELLOW}Step 4: Enabling service to start on boot...${NC}"
systemctl enable chess-game.service
echo -e "${GREEN}✓ Service enabled${NC}"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Service commands:"
echo -e "  ${YELLOW}Start service:${NC}   sudo systemctl start chess-game"
echo -e "  ${YELLOW}Stop service:${NC}    sudo systemctl stop chess-game"
echo -e "  ${YELLOW}Restart service:${NC} sudo systemctl restart chess-game"
echo -e "  ${YELLOW}View status:${NC}     sudo systemctl status chess-game"
echo -e "  ${YELLOW}View logs:${NC}       sudo journalctl -u chess-game -f"
echo -e "  ${YELLOW}Disable service:${NC} sudo systemctl disable chess-game"
echo ""
echo -e "${YELLOW}Do you want to start the service now? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo -e "${YELLOW}Starting chess-game service...${NC}"
    systemctl start chess-game.service
    echo -e "${GREEN}✓ Service started${NC}"
    echo ""
    echo "Checking service status..."
    sleep 2
    systemctl status chess-game.service --no-pager
else
    echo ""
    echo -e "${YELLOW}Service not started. Use 'sudo systemctl start chess-game' when ready.${NC}"
fi

echo ""
echo -e "${GREEN}The chess game will now automatically start on boot!${NC}"
