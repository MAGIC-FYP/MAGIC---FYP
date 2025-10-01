# Display and Input Module

This module provides a hierarchical menu system for the chess game using the **Composite Pattern**, integrated with LCD display and rotary encoder input.

## Architecture

The menu system follows the **Composite Pattern** design:

```
Menu (Component - Abstract Base Class)
├── MenuItem (Leaf - Executable actions)
├── SubMenu (Composite - Contains other Menu objects)
└── BackMenuItem (Special Leaf - Navigates to parent)
```

### Class Hierarchy

#### `Menu` (Component)
- Abstract base class for all menu components
- Defines interface: `execute()`, `get_display_text()`, `get_parent()`, `set_parent()`

#### `MenuItem` (Leaf)
- Represents an executable action
- Takes an optional callback function
- Returns result of action when executed

#### `SubMenu` (Composite)
- Contains other `Menu` objects (can be `MenuItem` or `SubMenu`)
- Maintains insertion order using a list
- Provides navigation methods: `next()`, `previous()`, `execute()`
- Tracks current selection with `current_index`

#### `BackMenuItem` (Special Leaf)
- Navigates back to parent menu when executed
- Automatically added to submenus for easy navigation

## Components

### 1. `menu.py`
Core menu classes implementing the Composite Pattern.

**Classes:**
- `Menu`: Abstract base class
- `MenuItem`: Leaf node for actions
- `SubMenu`: Composite node for menu hierarchy
- `BackMenuItem`: Special item for navigation

### 2. `menu_navigator.py`
Integrates menu system with hardware (LCD + rotary encoder).

**Features:**
- Rotary encoder rotation → Navigate menu items
- Rotary encoder press → Select/execute current item
- Automatic LCD display updates
- Two-line display format:
  - Line 1: Current menu title
  - Line 2: `> Current Item X/Y` (with navigation info)

### 3. `chess_menu.py`
Chess-specific menu builder.

**Menu Structure:**
```
Main Menu
├── Player vs Robot
│   ├── Player Colour
│   │   ├── White
│   │   ├── Black
│   │   └── Back
│   ├── Robot Level
│   │   ├── Level 1
│   │   ├── Level 2
│   │   ├── ...
│   │   ├── Level 20
│   │   └── Back
│   ├── Start Game
│   └── Back
└── Robot vs Robot
    ├── Robot 1 Level
    │   ├── Level 1
    │   ├── ...
    │   ├── Level 20
    │   └── Back
    ├── Robot 2 Level
    │   ├── Level 1
    │   ├── ...
    │   ├── Level 20
    │   └── Back
    ├── Start Game
    └── Back
```

### 4. `LCD.py`
LCD display driver for 16x2 I2C LCD.

**Features:**
- Display text on 2 lines
- Scrolling support
- Clear display
- Backlight control

### 5. `menu_example.py`
Test/example file demonstrating menu system usage.

## Usage

### Basic Menu Creation

```python
from display_and_input import SubMenu, MenuItem, BackMenuItem

# Create root menu
root = SubMenu("Main Menu")

# Add simple items
root.add(MenuItem("Option 1", lambda: print("Option 1 selected")))
root.add(MenuItem("Option 2", lambda: print("Option 2 selected")))

# Add submenu
submenu = SubMenu("Settings")
submenu.add(MenuItem("Setting 1", lambda: print("Setting 1")))
submenu.add(MenuItem("Setting 2", lambda: print("Setting 2")))
submenu.add(BackMenuItem())

root.add(submenu)
```

### Using with Hardware

```python
from display_and_input import MenuNavigator
from signal import pause

# Create menu structure
root = build_menu()

# Create navigator with LCD and rotary encoder
navigator = MenuNavigator(root)
navigator.start()

# Keep running
pause()
```

### Chess Game Integration

```python
from display_and_input import ChessMenuBuilder, MenuNavigator

def start_game(config):
    # Your game start logic
    print(f"Starting game with config: {config}")

# Build chess menu
builder = ChessMenuBuilder()
builder.set_start_game_callback(start_game)
root_menu = builder.build()

# Start navigation
navigator = MenuNavigator(root_menu)
navigator.start()
```

## Hardware Configuration

### Default GPIO Pins
- **Rotary Encoder A**: GPIO 27
- **Rotary Encoder B**: GPIO 22
- **Rotary Encoder Switch**: GPIO 17
- **LCD I2C Address**: 0x27

### Custom Configuration

```python
navigator = MenuNavigator(
    root_menu,
    encoder_a=27,
    encoder_b=22,
    switch_pin=17
)
```

## Testing

### Test without hardware:
```bash
python menu_example.py --no-hardware
```

### Test with hardware:
```bash
python menu_example.py
```

### Test chess menu:
```bash
cd src/chess_sim
python main.py
```

## Design Pattern Benefits

### Composite Pattern Advantages:
1. **Uniform Treatment**: Both `MenuItem` and `SubMenu` implement the same `Menu` interface
2. **Hierarchical Structure**: Natural tree structure for nested menus
3. **Easy Extension**: Add new menu types by extending `Menu` class
4. **Flexible Composition**: Build complex menu structures by composing simple components
5. **Ordered Children**: Insertion order preserved using list

### Example of Extensibility:

```python
class ToggleMenuItem(MenuItem):
    """Menu item that toggles between two states."""
    
    def __init__(self, name, on_action, off_action):
        super().__init__(name)
        self.state = False
        self.on_action = on_action
        self.off_action = off_action
    
    def execute(self):
        if self.state:
            self.off_action()
        else:
            self.on_action()
        self.state = not self.state
        return None
    
    def get_display_text(self):
        state_text = "ON" if self.state else "OFF"
        return f"{self.name} [{state_text}]"
```

## File Structure

```
display_and_input/
├── __init__.py              # Package initialization
├── LCD.py                   # LCD display driver
├── rotary_encoder_switch.py # Original rotary encoder test
├── menu.py                  # Composite Pattern menu classes
├── menu_navigator.py        # LCD + encoder integration
├── chess_menu.py            # Chess-specific menu builder
├── menu_example.py          # Test/example file
└── README.md                # This file
```

## Dependencies

- `smbus`: I2C communication for LCD
- `gpiozero`: GPIO control for rotary encoder
- `chess`: Chess library (for chess menu)

## Future Enhancements

1. **Scrolling long menu items**: For items longer than 16 characters
2. **Icons/symbols**: Custom LCD characters for better UI
3. **Menu item validation**: Disable items based on conditions
4. **Menu history**: Navigate back through history, not just parent
5. **Confirmation dialogs**: For destructive actions
6. **Input fields**: For numeric/text input using rotary encoder
