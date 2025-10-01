# Quick Start Guide

## Running the Chess Game with Menu System

### 1. Start the Game
```bash
cd /Users/vinaypanicker/Documents/MAGIC---FYP/src/chess_sim
python main.py
```

### 2. Navigate the Menu

**Hardware Controls:**
- **Rotate encoder clockwise**: Move to next menu item
- **Rotate encoder counter-clockwise**: Move to previous menu item  
- **Press encoder button**: Select current item / Enter submenu

### 3. Menu Structure

```
Main Menu
├── Player vs Robot          ← Choose this for human vs computer
│   ├── Player Colour        ← Select White or Black
│   ├── Robot Level          ← Choose difficulty (1-20)
│   ├── Start Game           ← Begin the game
│   └── Back                 ← Return to main menu
│
└── Robot vs Robot           ← Choose this for computer vs computer
    ├── Robot 1 Level        ← Set first robot difficulty
    ├── Robot 2 Level        ← Set second robot difficulty
    ├── Start Game           ← Begin the game
    └── Back                 ← Return to main menu
```

### 4. Example: Setting up Player vs Robot Game

1. **Main Menu** displays on LCD
2. Rotate to highlight `Player vs Robot`
3. Press to enter submenu
4. Rotate to `Player Colour`, press to enter
5. Rotate to select `White` or `Black`, press to confirm
6. You're back at Player vs Robot menu
7. Rotate to `Robot Level`, press to enter
8. Rotate to desired level (e.g., `Level 5`), press to confirm
9. Back at Player vs Robot menu
10. Rotate to `Start Game`, press to begin!

## Testing Without Hardware

### Test Menu Structure (No LCD/Encoder needed)
```bash
cd /Users/vinaypanicker/Documents/MAGIC---FYP/src/display_and_input
python menu_example.py --no-hardware
```

This will print the menu structure and test navigation programmatically.

### Test with Hardware
```bash
cd /Users/vinaypanicker/Documents/MAGIC---FYP/src/display_and_input
python menu_example.py
```

This runs a simple test menu with the actual LCD and rotary encoder.

## Troubleshooting

### LCD Not Displaying
- Check I2C connection: `i2cdetect -y 1`
- Verify I2C address (default: 0x27)
- Check backlight setting in LCD initialization

### Rotary Encoder Not Responding
- Verify GPIO pin connections:
  - Encoder A: GPIO 27
  - Encoder B: GPIO 22
  - Switch: GPIO 17
- Check pull-up resistors
- Test with `rotary_encoder_switch.py`

### Import Errors
```bash
# Make sure you're in the project root
cd /Users/vinaypanicker/Documents/MAGIC---FYP

# Run from correct directory
python -m src.chess_sim.main
```

## Customization

### Change GPIO Pins
Edit `menu_navigator.py` or pass custom pins:

```python
navigator = MenuNavigator(
    root_menu,
    encoder_a=27,    # Change these
    encoder_b=22,    # to your
    switch_pin=17    # GPIO pins
)
```

### Adjust Scrolling Behavior
Control when and how text scrolls:

```python
navigator = MenuNavigator(
    root_menu,
    scroll_threshold=10,  # Scroll text longer than 10 chars (default)
    scroll_speed=0.3      # Scroll speed in seconds (default: 0.3)
)
```

**Note:** Text longer than `scroll_threshold` characters will automatically scroll across the display. For example, "Player vs Robot" (16 chars) will scroll since it's > 10 characters.

### Change LCD I2C Address
Edit `LCD.py` or pass custom address:

```python
lcd = LCD(i2c_addr=0x27)  # Change to your address
```

### Modify Menu Options
Edit `chess_menu.py`:

```python
# Change robot level range
for level in range(1, 11):  # Now 1-10 instead of 1-20
    level_menu.add(MenuItem(f"Level {level}", ...))
```

### Add Custom Menu Items
```python
from display_and_input import MenuItem

def my_action():
    print("Custom action!")

custom_item = MenuItem("My Option", my_action)
submenu.add(custom_item)
```

## Code Examples

### Creating a Simple Menu
```python
from display_and_input import SubMenu, MenuItem, BackMenuItem

# Create root
root = SubMenu("Settings")

# Add items
root.add(MenuItem("Option 1", lambda: print("Option 1")))
root.add(MenuItem("Option 2", lambda: print("Option 2")))

# Add submenu
sub = SubMenu("Advanced")
sub.add(MenuItem("Advanced 1", lambda: print("Adv 1")))
sub.add(BackMenuItem())

root.add(sub)
```

### Using with Navigator
```python
from display_and_input import MenuNavigator
from signal import pause

navigator = MenuNavigator(root)
navigator.start()
pause()  # Keep running
```

### Building Chess Menu
```python
from display_and_input import ChessMenuBuilder

def start_game(config):
    print(f"Game mode: {config['game_mode']}")
    print(f"Config: {config}")

builder = ChessMenuBuilder()
builder.set_start_game_callback(start_game)
menu = builder.build()
```

## Display Format

The LCD shows:
```
┌────────────────┐
│ Player vs Robot│  ← Current menu/submenu
│ > Start Game 3/4│ ← Selected item + position
└────────────────┘
```

- **Line 1**: Where you are (menu title)
- **Line 2**: What you're selecting (item + position)
- **`>`**: Indicates current selection
- **`X/Y`**: Position (item X of Y total items)

## Next Steps

1. **Test the menu system**: Run `menu_example.py`
2. **Configure your game**: Use the menu to set options
3. **Start playing**: Select "Start Game"
4. **Modify as needed**: Edit `chess_menu.py` for custom options

## Support

- **Architecture details**: See `ARCHITECTURE.md`
- **Full documentation**: See `README.md`
- **Code reference**: See inline comments in source files
