# Game Interrupt Feature

## Overview
The chess robot now supports interrupting an active game and returning to the main menu using the rotary encoder button.

## How to Use

### During a Game
1. **Press and hold** the rotary encoder button for **1 second**
2. The LCD will display: "Ending game..." / "Returning to menu"
3. The game will cleanly exit and return you to the main menu
4. You can then start a new game or change settings

### Visual Feedback
- Short press (<1 second): No effect during game
- Long press (≥1 second): Game interrupt triggered
- LCD shows confirmation message
- Menu is restored automatically

## Technical Details

### Components Modified

#### 1. ThreadedLCDManager (`threaded_lcd_manager.py`)
- Added `_game_interrupt_requested` flag
- Added `_in_game_mode` state tracking
- New methods:
  - `request_game_interrupt()`: Request game interruption
  - `is_game_interrupt_requested()`: Check interrupt status
  - `set_game_mode(active)`: Enable/disable game mode
  - `clear_game_interrupt()`: Reset interrupt flag

#### 2. MenuNavigator (`menu_navigator.py`)
- Enhanced `_on_press()` method to detect long press during game mode
- Requires 1-second hold to prevent accidental interrupts
- Sends interrupt request to LCD manager

#### 3. Board (`models/board.py`)
- Modified `__init__` to accept `lcd_manager` parameter
- Updated `play_game()` to check for interrupt in game loop
- Updated `play_game_gui()` to check for interrupt in game loop
- Both methods now return `bool` (True if completed, False if interrupted)

#### 4. Main (`main.py`)
- Pass LCD manager to Board constructor
- Set game mode active before starting game
- Set game mode inactive after game ends
- Handle interrupted games gracefully
- Return to menu on interrupt

### Game Loop Integration

The interrupt check happens at the start of each game turn:
```python
while not self.is_game_over():
    # Check for game interrupt
    if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
        print("\nGame interrupted by user")
        return False
    # ... rest of game logic
```

### Safety Features

1. **Long Press Requirement**: Prevents accidental interrupts (1-second hold required)
2. **Game Mode State**: Button only triggers interrupt when actually in a game
3. **Clean Cleanup**: Game resources are properly cleaned up on interrupt
4. **User Confirmation**: Visual feedback via LCD display
5. **Thread-Safe**: All state changes use proper locking

## Supported Game Modes

The interrupt feature works with:
- ✅ Player vs Robot
- ✅ Robot vs Robot  
- ✅ Online Lichess games
- ✅ Archived game replay

## Examples

### Scenario 1: Exit During Player Turn
1. Game is waiting for human move
2. User holds encoder button for 1+ second
3. Game exits immediately
4. Returns to main menu

### Scenario 2: Exit During Robot Turn
1. Robot is calculating move
2. User holds encoder button for 1+ second
3. Current move calculation completes or is aborted
4. Game exits cleanly
5. Returns to main menu

### Scenario 3: Exit During Online Game
1. Playing against Lichess opponent
2. User holds encoder button for 1+ second
3. Local game exits (Lichess game continues on server)
4. Returns to main menu

## Configuration

### Adjust Long Press Duration
Edit `menu_navigator.py`, line 112:
```python
while self.switch.is_pressed and (time.time() - start_time) < 1.0:
```
Change `1.0` to desired seconds (e.g., `0.5` for half second, `2.0` for 2 seconds)

### Disable Feature
To disable game interrupt, comment out the interrupt check in `board.py`:
```python
# if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
#     print("\nGame interrupted by user")
#     return False
```

## Troubleshooting

### Button Not Responding
- Ensure rotary encoder is properly connected to GPIO 26
- Check that `menu_navigator.running` is True
- Verify LCD manager is in game mode

### Accidental Interrupts
- Increase long press duration (see Configuration above)
- Check for hardware issues with encoder button

### Game Not Exiting
- Verify LCD manager reference is passed to Board
- Check console for "Game interrupted by user" message
- Ensure game loop is checking interrupt flag

## Future Enhancements

Potential improvements:
- Visual progress bar during long press
- Pause/resume instead of exit
- Save game state on interrupt
- Confirmation dialog before exit
