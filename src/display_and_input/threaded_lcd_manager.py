"""
Threaded LCD Display Manager for Chess Game

This module provides a threaded LCD display manager that can run concurrently
with the chess game, displaying game status, menu navigation, and other
information without blocking the main game loop.
"""

import threading
import time
import queue
from typing import Optional, Dict, Any
from enum import Enum
import chess

# Use try/except to support both relative and absolute imports
try:
    from .LCD import LCD
    from .menu import Menu
except ImportError:
    from LCD import LCD
    from menu import Menu


class DisplayMode(Enum):
    """Enumeration of different display modes."""
    MENU = "menu"
    GAME_STATUS = "game_status"
    MESSAGE = "message"
    IDLE = "idle"


class LCDMessage:
    """Message class for LCD display queue."""
    
    def __init__(self, mode: DisplayMode, data: Dict[str, Any], duration: float = 0.0):
        """
        Initialize LCD message.
        
        Args:
            mode: Display mode for this message
            data: Data to display (varies by mode)
            duration: How long to display this message (0 = until next message)
        """
        self.mode = mode
        self.data = data
        self.duration = duration
        self.timestamp = time.time()


class ThreadedLCDManager:
    """
    Threaded LCD display manager that runs concurrently with the chess game.
    
    This class manages LCD display updates in a separate thread, allowing
    the main game loop to continue running without blocking on LCD operations.
    """
    
    def __init__(self, lcd: Optional[LCD] = None, update_interval: float = 0.3):
        """
        Initialize the threaded LCD manager.
        
        Args:
            lcd: LCD instance (creates new one if None)
            update_interval: Minimum time between display updates (seconds)
        """
        self.lcd = lcd if lcd else LCD()
        self.update_interval = update_interval
        
        # Thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Message queue for thread-safe communication
        self._message_queue = queue.Queue()
        
        # Current display state
        self._current_mode = DisplayMode.IDLE
        self._current_data: Dict[str, Any] = {}
        self._last_update = 0
        self._last_actual_update = 0  # Track when display was actually updated
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Menu reference for menu mode
        self._current_menu: Optional[Menu] = None
        
        # Game state for game status mode
        self._game_state: Dict[str, Any] = {
            'current_player': None,
            'move_count': 0,
            'game_status': 'waiting',
            'last_move': None,
            'board_fen': None,
            'thinking_time': 0,
            'opponent_name': None
        }
        
        # Cache for display content to prevent unnecessary updates
        self._display_cache = {'line1': '', 'line2': ''}
        self._previous_mode = None
        
        # Game interrupt control with handshake
        self._game_interrupt_requested = False
        self._game_interrupt_acknowledged = False
        self._in_game_mode = False
        self._interrupt_request_count = 0  # Track how many times interrupt was requested
    
    def start(self):
        """Start the LCD display thread."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the LCD display thread."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        # Clear the display
        try:
            self.lcd.clear()
        except:
            pass
    
    def set_menu_mode(self, menu: Menu):
        """
        Switch to menu display mode.
        
        Args:
            menu: Menu object to display
        """
        with self._lock:
            self._current_menu = menu
        
        message = LCDMessage(DisplayMode.MENU, {'menu': menu})
        self._message_queue.put(message)
    
    def set_game_status_mode(self, game_state: Dict[str, Any]):
        """
        Switch to game status display mode.
        
        Args:
            game_state: Dictionary containing current game state
        """
        with self._lock:
            self._game_state.update(game_state)
        
        message = LCDMessage(DisplayMode.GAME_STATUS, {'game_state': self._game_state.copy()})
        self._message_queue.put(message)
    
    def show_message(self, line1: str, line2: str = "", duration: float = 3.0):
        """
        Display a temporary message on the LCD.
        
        Args:
            line1: First line of the message
            line2: Second line of the message
            duration: How long to display the message (seconds)
        """
        self.lcd.clear()
        message = LCDMessage(
            DisplayMode.MESSAGE,
            {'line1': line1, 'line2': line2},
            duration
        )
        self._message_queue.put(message)
    
    def show_idle(self):
        """Switch to idle display mode."""
        message = LCDMessage(DisplayMode.IDLE, {})
        self._message_queue.put(message)
    
    def _display_loop(self):
        """Main display loop running in separate thread."""
        while self._running and not self._stop_event.is_set():
            try:
                # Process messages from queue
                self._process_message_queue()
                
                # Update display based on current mode
                self._update_display()
                
                # Sleep to prevent excessive CPU usage
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in LCD display loop: {e}")
                time.sleep(1.0)  # Wait longer on error
    
    def _process_message_queue(self):
        """Process all pending messages in the queue."""
        while not self._message_queue.empty():
            try:
                message = self._message_queue.get_nowait()
                self._handle_message(message)
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error processing LCD message: {e}")
    
    def _handle_message(self, message: LCDMessage):
        """
        Handle a single LCD message.
        
        Args:
            message: LCDMessage to process
        """
        with self._lock:
            self._current_mode = message.mode
            self._current_data = message.data.copy()
            self._last_update = time.time()
    
    def _update_display(self):
        """Update the LCD display based on current mode."""
        current_time = time.time()
        
        # Rate limiting - use actual update time, not message receipt time
        if current_time - self._last_actual_update < self.update_interval:
            return
        
        try:
            with self._lock:
                mode = self._current_mode
                data = self._current_data.copy()
            
            if mode == DisplayMode.MENU:
                self._display_menu(data)
            elif mode == DisplayMode.GAME_STATUS:
                self._display_game_status(data)
            elif mode == DisplayMode.MESSAGE:
                self._display_message(data)
            elif mode == DisplayMode.IDLE:
                self._display_idle()
            
            # Update the actual update timestamp
            self._last_actual_update = current_time
                
        except Exception as e:
            print(f"Error updating LCD display: {e}")
    
    def _display_menu(self, data: Dict[str, Any]):
        """Display menu navigation."""
        menu = data.get('menu')
        if not menu:
            return
        
        try:
            # Line 1: Current menu title
            line1 = menu.get_display_text()
            
            # Line 2: Current selection with navigation info
            if hasattr(menu, 'get_current_display_text') and hasattr(menu, 'get_navigation_info'):
                current_child_text = menu.get_current_display_text()
                nav_info = menu.get_navigation_info()
                
                # Format: "> Item Name 1/5"
                nav_info_len = len(nav_info) + 1
                available_space = 16 - 2 - nav_info_len
                
                if len(current_child_text) > available_space:
                    current_child_text = current_child_text[:available_space]
                
                line2 = f"> {current_child_text}"
                line2 = line2.ljust(16 - len(nav_info)) + nav_info
            else:
                line2 = "Navigate with encoder"
            
            # Only update if content has changed or mode switched
            self._smart_display_update(line1, line2)
            
        except Exception as e:
            print(f"Error displaying menu: {e}")
    
    def _display_game_status(self, data: Dict[str, Any]):
        """Display current game status."""
        game_state = data.get('game_state', {})
        
        try:
            current_player = game_state.get('current_player')
            game_status = game_state.get('game_status', 'waiting')
            move_count = game_state.get('move_count', 0)
            last_move = game_state.get('last_move')
            thinking_time = game_state.get('thinking_time', 0)
            opponent_name = game_state.get('opponent_name')
            
            # Line 1: Current player and move count
            if current_player:
                player_name = "White" if current_player.colour == chess.WHITE else "Black"
                if isinstance(current_player, str):  # For online games
                    player_name = current_player
                line1 = f"{player_name} to move"
            else:
                line1 = f"Move {move_count}"
            
            # Line 2: Game status or last move
            if game_status == 'thinking':
                line2 = f"Thinking... {thinking_time:.1f}s"
            elif last_move:
                line2 = f"Last: {last_move}"
            elif opponent_name:
                line2 = f"vs {opponent_name[:12]}"
            else:
                line2 = game_status.title()
            
            # Only update if content has changed or mode switched
            self._smart_display_update(line1, line2)
            
        except Exception as e:
            print(f"Error displaying game status: {e}")
    
    def _display_message(self, data: Dict[str, Any]):
        """Display a temporary message."""
        line1 = data.get('line1', '')
        line2 = data.get('line2', '')
        
        try:
            # Messages always update (they're typically one-off notifications)
            self._smart_display_update(line1, line2, force=True)
        except Exception as e:
            print(f"Error displaying message: {e}")
    
    def _display_idle(self):
        """Display idle screen."""
        try:
            self._smart_display_update("Chess Robot", "Ready to play")
        except Exception as e:
            print(f"Error displaying idle: {e}")
    
    def _smart_display_update(self, line1: str, line2: str, force: bool = False):
        """
        Smart display update that only clears and writes when content actually changes.
        
        Args:
            line1: First line content
            line2: Second line content  
            force: Force update even if content hasn't changed
        """
        # Pad lines to LCD width for accurate comparison
        line1_padded = line1[:16].ljust(16)
        line2_padded = line2[:16].ljust(16)
        
        # Check if content has changed or mode switched
        mode_changed = self._previous_mode != self._current_mode
        content_changed = (self._display_cache['line1'] != line1_padded or 
                          self._display_cache['line2'] != line2_padded)
        
        if force or mode_changed or content_changed:
            # Only clear if mode changed (prevents flicker on content updates)
            if mode_changed:
                self.lcd.clear()
            
            # Update only changed lines
            if force or mode_changed or self._display_cache['line1'] != line1_padded:
                self.lcd.message(line1_padded, line=1)
                self._display_cache['line1'] = line1_padded
            
            if force or mode_changed or self._display_cache['line2'] != line2_padded:
                self.lcd.message(line2_padded, line=2)
                self._display_cache['line2'] = line2_padded
            
            # Update mode tracking
            self._previous_mode = self._current_mode
    
    def update_game_state(self, **kwargs):
        """
        Update specific game state values.
        
        Args:
            **kwargs: Game state values to update
        """
        with self._lock:
            self._game_state.update(kwargs)
        
        # Send update message if in game status mode
        if self._current_mode == DisplayMode.GAME_STATUS:
            message = LCDMessage(DisplayMode.GAME_STATUS, {'game_state': self._game_state.copy()})
            self._message_queue.put(message)
    
    def is_running(self) -> bool:
        """Check if the LCD manager is running."""
        return self._running
    
    def get_current_mode(self) -> DisplayMode:
        """Get the current display mode."""
        with self._lock:
            return self._current_mode
    
    def request_game_interrupt(self):
        """Request interruption of current game with persistent flag."""
        with self._lock:
            print(f"DEBUG: Interrupt requested. In game mode: {self._in_game_mode}, Already requested: {self._game_interrupt_requested}")
            if self._in_game_mode:
                if not self._game_interrupt_requested:
                    self._game_interrupt_requested = True
                    self._game_interrupt_acknowledged = False
                    self._interrupt_request_count = 1
                    print("Game interrupt requested")
                else:
                    self._interrupt_request_count += 1
            else:
                print("DEBUG: Interrupt ignored - not in game mode")
    
    def is_game_interrupt_requested(self) -> bool:
        """Check if game interruption has been requested (non-destructive check)."""
        with self._lock:
            if self._game_interrupt_requested and not self._game_interrupt_acknowledged:
                return True
            return False
    
    def acknowledge_interrupt(self):
        """Acknowledge that the interrupt was received and processed."""
        with self._lock:
            if self._game_interrupt_requested:
                self._game_interrupt_acknowledged = True
                return True
            return False
    
    def set_game_mode(self, active: bool):
        """Set whether currently in game mode."""
        with self._lock:
            self._in_game_mode = active
            if active:
                # Reset interrupt state when entering game mode
                self._game_interrupt_requested = False
                self._game_interrupt_acknowledged = False
                self._interrupt_request_count = 0
    
    def is_in_game_mode(self) -> bool:
        """Check if currently in game mode."""
        with self._lock:
            return self._in_game_mode
    
    def clear_game_interrupt(self):
        """Clear the game interrupt flag after it's been handled."""
        with self._lock:
            self._game_interrupt_requested = False
            self._game_interrupt_acknowledged = False
            self._interrupt_request_count = 0
    
    def get_promotion_choice(self) -> str:
        """
        Display a menu for selecting a promotion piece and wait for user selection.
        
        Returns:
            Single character representing the piece: 'q', 'r', 'b', or 'n'
        """
        try:
            from .menu import SubMenu, MenuItem
            from .menu_navigator import MenuNavigator
        except ImportError:
            from menu import SubMenu, MenuItem
            from menu_navigator import MenuNavigator
        
        # Create promotion menu
        promotion_menu = SubMenu("Promote Pawn")
        
        # Store selection
        selection = {'piece': None}
        
        def select_piece(piece_symbol):
            selection['piece'] = piece_symbol
        
        promotion_menu.add(MenuItem("Queen", lambda: select_piece('q'), auto_back=True))
        promotion_menu.add(MenuItem("Rook", lambda: select_piece('r'), auto_back=True))
        promotion_menu.add(MenuItem("Bishop", lambda: select_piece('b'), auto_back=True))
        promotion_menu.add(MenuItem("Knight", lambda: select_piece('n'), auto_back=True))
        
        # Get the navigator instance and temporarily switch to promotion menu
        navigator = MenuNavigator.get_instance()
        if not navigator:
            # Fallback to queen if no navigator available
            print("Warning: No MenuNavigator found, defaulting to Queen promotion")
            return 'q'
        
        # Save current state
        original_menu = navigator.current_menu
        original_index = original_menu.current_index if hasattr(original_menu, 'current_index') else 0
        was_in_game_mode = self.is_in_game_mode()
        
        # Temporarily disable game mode so button works for menu selection
        if was_in_game_mode:
            self.set_game_mode(False)
        
        # Navigate to promotion menu
        navigator.current_menu = promotion_menu
        promotion_menu.current_index = 0
        
        # Update display with promotion menu
        self.set_menu_mode(promotion_menu)
        
        print("Promotion menu displayed. Use encoder to select piece and press button to confirm.")
        
        # Wait for selection (blocking)
        import time
        timeout = 30  # 30 second timeout
        start_time = time.time()
        
        while selection['piece'] is None:
            time.sleep(0.05)  # Check more frequently
            if time.time() - start_time > timeout:
                # Timeout - default to queen
                print("Promotion selection timed out, defaulting to Queen")
                selection['piece'] = 'q'
                break
        
        print(f"Promotion piece selected: {selection['piece']}")
        
        # Restore original state
        navigator.current_menu = original_menu
        if hasattr(original_menu, 'current_index'):
            original_menu.current_index = original_index
        
        # Restore game mode if it was active
        if was_in_game_mode:
            self.set_game_mode(True)
            # Don't show menu, let game continue
        elif original_menu:
            self.set_menu_mode(original_menu)
        
        return selection['piece']


# Global instance for easy access
_lcd_manager: Optional[ThreadedLCDManager] = None
_lcd_manager_lock = threading.Lock()

def get_lcd_manager() -> ThreadedLCDManager:
    global _lcd_manager
    if _lcd_manager is None:
        with _lcd_manager_lock:
            # Double-checked locking pattern
            if _lcd_manager is None:
                _lcd_manager = ThreadedLCDManager()
    return _lcd_manager


def start_lcd_manager():
    """Start the global LCD manager."""
    manager = get_lcd_manager()
    manager.start()


def stop_lcd_manager():
    """Stop the global LCD manager."""
    global _lcd_manager
    if _lcd_manager:
        _lcd_manager.stop()
        _lcd_manager = None


if __name__ == "__main__":
    # Test the threaded LCD manager
    manager = ThreadedLCDManager()
    manager.start()
    
    try:
        # Test different display modes
        manager.show_message("Testing LCD", "Thread Manager", 2.0)
        time.sleep(3)
        
        manager.show_idle()
        time.sleep(2)
        
        manager.update_game_state(
            current_player="White",
            move_count=5,
            game_status="thinking",
            thinking_time=2.5
        )
        time.sleep(3)
        
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
