"""
MenuNavigator integrates the menu system with LCD display and rotary encoder input.
"""

from gpiozero import Button, RotaryEncoder
from typing import Optional
import time
import threading

# Use try/except to support both relative and absolute imports
try:
    from .LCD import LCD
    from .menu import Menu, SubMenu, MenuItem
    from .threaded_lcd_manager import ThreadedLCDManager, get_lcd_manager
except ImportError:
    from LCD import LCD
    from menu import Menu, SubMenu, MenuItem
    from threaded_lcd_manager import ThreadedLCDManager, get_lcd_manager


class MenuNavigator:
    """
    Handles navigation through menu system using rotary encoder and displays on LCD.
    """
    
    def __init__(self, root_menu: SubMenu, lcd: Optional[LCD] = None, 
                 encoder_a: int = 6, encoder_b: int = 27, switch_pin: int = 26,
                 update_delay: float = 0.2, use_threaded_lcd: bool = True):
        """
        Initialize the menu navigator.
        
        Args:
            root_menu: Root SubMenu to start navigation from
            lcd: LCD instance (creates new one if None)
            encoder_a: GPIO pin for rotary encoder A
            encoder_b: GPIO pin for rotary encoder B
            switch_pin: GPIO pin for rotary encoder switch
            update_delay: Minimum delay between display updates (seconds)
            use_threaded_lcd: Whether to use the threaded LCD manager
        """
        self.root_menu = root_menu
        self.current_menu = root_menu
        
        # Initialize LCD - use threaded manager if requested
        self.use_threaded_lcd = use_threaded_lcd
        if use_threaded_lcd:
            self.lcd_manager = get_lcd_manager()
            self.lcd = None  # We'll use the threaded manager
        else:
            self.lcd = lcd if lcd else LCD()
            self.lcd_manager = None
        
        # Initialize rotary encoder and switch
        self.encoder = RotaryEncoder(a=encoder_a, b=encoder_b, max_steps=0)
        self.switch = Button(switch_pin, pull_up=True)
        self.switch_pin = switch_pin
        
        # Track encoder position
        self.last_encoder_steps = 0
        
        # Thread safety and rate limiting
        self.display_lock = threading.Lock()
        self.last_update = 0
        self.update_delay = update_delay  # Minimum time between updates
        
        # Button press detection thread
        self._button_thread = None
        self._button_stop_event = threading.Event()
        self.long_press_time = 1.0  # 1 second for long press
        
        # Setup callbacks
        self.encoder.when_rotated = self._on_rotate
        # Note: We'll handle button presses in a dedicated thread instead of callbacks
        
        # Flag to control running state
        self.running = False
        
        # Display initial menu
        self._safe_update_display()

        self.state_lock = threading.Lock()
    
    def _on_rotate(self):
        """Handle rotary encoder rotation with rate limiting."""
        if not self.running:
            return
        
        with self.state_lock:
            current_time = time.time()
            
            if current_time - self.last_update < self.update_delay:
                return
         
            current_steps = self.encoder.steps
            
            if current_steps > self.last_encoder_steps:
                # Rotated clockwise - next item
                if isinstance(self.current_menu, SubMenu):
                    self.current_menu.next()
                    self._safe_update_display()
            elif current_steps < self.last_encoder_steps:
                # Rotated counter-clockwise - previous item
                if isinstance(self.current_menu, SubMenu):
                    self.current_menu.previous()
                    self._safe_update_display()
            
            self.last_encoder_steps = current_steps
            self.last_update = current_time
    
    def _button_monitor_loop(self):
        """Monitor button state in dedicated thread for reliable press detection."""
        print(f"Button monitor thread started on GPIO {self.switch_pin}")
        
        while not self._button_stop_event.is_set():
            try:
                # Wait for button press using gpiozero's Button.is_pressed
                while not self._button_stop_event.is_set():
                    if self.switch.is_pressed:  # Button pressed
                        break
                    time.sleep(0.01)  # 10ms polling
                
                if self._button_stop_event.is_set():
                    break
                
                # Button was pressed - measure hold duration
                press_start = time.time()
                time.sleep(0.05)  # Debounce delay
                
                # Wait for release or long press timeout
                is_long_press = False
                while not self._button_stop_event.is_set():
                    hold_duration = time.time() - press_start
                    
                    if not self.switch.is_pressed:  # Button released
                        break
                    
                    if hold_duration >= self.long_press_time:
                        is_long_press = True
                        break
                    
                    time.sleep(0.05)  # Check every 50ms
                
                if self._button_stop_event.is_set():
                    break
                
                # Handle press based on duration and game mode
                if is_long_press:
                    self._handle_long_press()
                    # Wait for button release
                    while self.switch.is_pressed and not self._button_stop_event.is_set():
                        time.sleep(0.05)
                else:
                    self._handle_short_press()
                
                # Additional debounce after release
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in button monitor: {e}")
                time.sleep(0.1)
        
        print("Button monitor thread stopped")
    
    def _handle_short_press(self):
        """Handle short button press."""
        if not self.running:
            return
        
        # In game mode, ignore short presses
        if self.use_threaded_lcd and self.lcd_manager:
            if self.lcd_manager.is_in_game_mode():
                return
        
        # Short press in menu mode - execute current selection
        with self.state_lock:
            if isinstance(self.current_menu, SubMenu):
                # Execute the current selection
                next_menu = self.current_menu.execute()
                
                if next_menu is not None:
                    # Navigate to the returned menu
                    self.current_menu = next_menu
                    self._safe_update_display()
                elif next_menu is None and self.current_menu.get_parent() is None:
                    # If we're at root and execute returns None, stay at root
                    self._safe_update_display()
    
    def _handle_long_press(self):
        """Handle long button press (1 second hold)."""
        if not self.running:
            return
        
        print("Long button press detected!")  # Debug message
        
        # Check if in game mode - if so, request game interrupt
        if self.use_threaded_lcd and self.lcd_manager:
            if self.lcd_manager.is_in_game_mode():
                # Long press confirmed - request interrupt
                print("Requesting game interrupt...")
                self.lcd_manager.request_game_interrupt()
                self.lcd_manager.show_message("Ending game...", "Returning to menu", 2.0)
                return
    
    def _safe_update_display(self):
        """Thread-safe display update with error handling."""
        with self.display_lock:
            try:
                self.update_display()
            except Exception as e:
                print(f"Display update error: {e}")
                # Graceful degradation - don't crash
    
    def update_display(self):
        """Update the LCD display with current menu state."""
        if self.use_threaded_lcd and self.lcd_manager:
            # Use threaded LCD manager
            self.lcd_manager.set_menu_mode(self.current_menu)
        else:
            # Use direct LCD access
            if isinstance(self.current_menu, SubMenu):
                # Line 1: Current menu title
                line1 = self.current_menu.get_display_text()
                
                # Line 2: Current selection with navigation info
                current_child_text = self.current_menu.get_current_display_text()
                nav_info = self.current_menu.get_navigation_info()
                
                # Format: "> Item Name 1/5"
                # Calculate available space: 16 chars - "> " - " X/Y"
                nav_info_len = len(nav_info) + 1  # +1 for space before nav_info
                available_space = 16 - 2 - nav_info_len
                
                if len(current_child_text) > available_space:
                    current_child_text = current_child_text[:available_space]
                
                line2 = f"> {current_child_text}"
                # Pad to push nav_info to the right
                line2 = line2.ljust(16 - len(nav_info)) + nav_info
                
                self.lcd.clear()
                self.lcd.message(line1, line=1)
                self.lcd.message(line2, line=2)
    
    def start(self):
        """Start the menu navigator (enables input handling)."""
        self.running = True
        
        # Start button monitor thread
        self._button_stop_event.clear()
        self._button_thread = threading.Thread(target=self._button_monitor_loop, daemon=True)
        self._button_thread.start()
        
        self._safe_update_display()
        print("Menu navigator started. Press Ctrl+C to exit.")
        print("Hold button for 1 second during game to interrupt and return to menu.")
    
    def stop(self):
        """Stop the menu navigator (disables input handling)."""
        self.running = False
        
        # Stop button monitor thread
        self._button_stop_event.set()
        if self._button_thread and self._button_thread.is_alive():
            self._button_thread.join(timeout=2.0)
        
        if self.use_threaded_lcd and self.lcd_manager:
            # Don't clear LCD here - let the threaded manager handle it
            pass
        else:
            self.lcd.clear()
        print("Menu navigator stopped.")
    
    def navigate_to_root(self):
        """Navigate back to the root menu."""
        self.current_menu = self.root_menu
        self.current_menu.reset_index()
        self._safe_update_display()
    
    def get_current_menu(self) -> Menu:
        """Get the current menu being displayed."""
        return self.current_menu
    
    def get_lcd_manager(self) -> Optional[ThreadedLCDManager]:
        """Get the LCD manager instance (if using threaded LCD)."""
        return self.lcd_manager if self.use_threaded_lcd else None
