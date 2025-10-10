# MAGIC Chess Board - Auto-Start Service

This directory contains scripts to automatically run the chess game on boot using systemd.

## Files

- **chess-game.service**: Systemd service configuration file
- **install_chess_service.sh**: Installation script to enable auto-start on boot
- **uninstall_chess_service.sh**: Uninstallation script to remove the service

## Installation

1. Make the installation script executable and run it:

```bash
chmod +x install_chess_service.sh
sudo ./install_chess_service.sh
```

2. The script will:
   - Copy the service file to `/etc/systemd/system/`
   - Update paths to match your installation directory
   - Enable the service to start on boot
   - Optionally start the service immediately

## Service Management

Once installed, you can manage the service using these commands:

### Start the service
```bash
sudo systemctl start chess-game
```

### Stop the service
```bash
sudo systemctl stop chess-game
```

### Restart the service
```bash
sudo systemctl restart chess-game
```

### Check service status
```bash
sudo systemctl status chess-game
```

### View service logs
```bash
# View live logs
sudo journalctl -u chess-game -f

# View last 50 lines
sudo journalctl -u chess-game -n 50

# View logs from today
sudo journalctl -u chess-game --since today
```

### Disable auto-start on boot
```bash
sudo systemctl disable chess-game
```

### Re-enable auto-start on boot
```bash
sudo systemctl enable chess-game
```

## Uninstallation

To completely remove the service:

```bash
chmod +x uninstall_chess_service.sh
sudo ./uninstall_chess_service.sh
```

## Service Configuration

The service is configured with:

- **Working Directory**: `src/chess_sim/` in your project directory
- **Executable**: `main.py`
- **User**: The user who ran the installation script
- **Auto-restart**: Service will automatically restart if it crashes
- **Restart Delay**: 10 seconds between restart attempts
- **Network Dependency**: Waits for network to be available (required for Lichess online games)
- **Logging**: All output is logged to the system journal (accessible via `journalctl`)

## Requirements

- Systemd (pre-installed on Raspberry Pi OS and most modern Linux distributions)
- Root/sudo access for installation
- Python 3 and all chess game dependencies installed

## Troubleshooting

### Service fails to start

1. Check the service status:
   ```bash
   sudo systemctl status chess-game
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u chess-game -n 100
   ```

3. Common issues:
   - Missing Python dependencies (check logs)
   - Incorrect file paths (verify paths in `/etc/systemd/system/chess-game.service`)
   - Permission issues (ensure user has access to GPIO, I2C, etc.)
   - Missing `.env` file for Lichess API token

### Service starts but crashes immediately

Check logs for Python errors:
```bash
sudo journalctl -u chess-game -f
```

### Need to edit service configuration

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/chess-game.service
   ```

2. Reload systemd and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart chess-game
   ```

## Notes

- The service runs with `PYTHONUNBUFFERED=1` to ensure real-time log output
- All stdout and stderr are logged to the systemd journal
- The service automatically restarts on failure with a 10-second delay
- The service starts after the network is available
