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
except ImportError:
    from LCD import LCD
    from menu import Menu, SubMenu, MenuItem


class MenuNavigator:
    """
    Handles navigation through menu system using rotary encoder and displays on LCD.
    """
    
    def __init__(self, root_menu: SubMenu, lcd: Optional[LCD] = None, 
                 encoder_a: int = 27, encoder_b: int = 22, switch_pin: int = 17,
                 update_delay: float = 0.1):
        """
        Initialize the menu navigator.
        
        Args:
            root_menu: Root SubMenu to start navigation from
            lcd: LCD instance (creates new one if None)
            encoder_a: GPIO pin for rotary encoder A
            encoder_b: GPIO pin for rotary encoder B
            switch_pin: GPIO pin for rotary encoder switch
            update_delay: Minimum delay between display updates (seconds)
        """
        self.root_menu = root_menu
        self.current_menu = root_menu
        
        # Initialize LCD
        self.lcd = lcd if lcd else LCD()
        
        # Initialize rotary encoder and switch
        self.encoder = RotaryEncoder(a=encoder_a, b=encoder_b, max_steps=0)
        self.switch = Button(switch_pin, pull_up=True)
        
        # Track encoder position
        self.last_encoder_steps = 0
        
        # Thread safety and rate limiting
        self.display_lock = threading.Lock()
        self.last_update = 0
        self.update_delay = update_delay  # Minimum time between updates
        
        # Setup callbacks
        self.encoder.when_rotated = self._on_rotate
        self.switch.when_pressed = self._on_press
        
        # Flag to control running state
        self.running = False
        
        # Display initial menu
        self._safe_update_display()
    
    def _on_rotate(self):
        """Handle rotary encoder rotation with rate limiting."""
        if not self.running:
            return
        
        current_time = time.time()
        if current_time - self.last_update < self.update_delay:
            return  # Rate limit - debounce rapid rotations
            
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
    
    def _on_press(self):
        """Handle rotary encoder switch press with debouncing."""
        if not self.running:
            return
        
        time.sleep(0.05)  # Debounce button press
            
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
        self._safe_update_display()
        print("Menu navigator started. Press Ctrl+C to exit.")
    
    def stop(self):
        """Stop the menu navigator (disables input handling)."""
        self.running = False
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
