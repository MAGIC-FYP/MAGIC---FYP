"""
Menu system using Composite Pattern for LCD display with rotary encoder navigation.

This module implements a hierarchical menu system where:
- Menu: Base class (Component)
- MenuItem: Leaf node representing an executable action
- SubMenu: Composite node containing other Menu objects
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, List


class Menu(ABC):
    """
    Base class for all menu components (Component in Composite Pattern).
    """
    
    def __init__(self, name: str):
        """
        Initialize a menu component.
        
        Args:
            name: Display name for this menu component
        """
        self.name = name
        self.parent: Optional['SubMenu'] = None
    
    @abstractmethod
    def execute(self) -> Optional['Menu']:
        """
        Execute the menu component's action.
        
        Returns:
            The next menu to navigate to, or None to stay on current menu
        """
        pass
    
    @abstractmethod
    def get_display_text(self) -> str:
        """
        Get the text to display for this menu component.
        
        Returns:
            String to display on LCD
        """
        pass
    
    def get_parent(self) -> Optional['SubMenu']:
        """Get the parent menu."""
        return self.parent
    
    def set_parent(self, parent: 'SubMenu'):
        """Set the parent menu."""
        self.parent = parent


class MenuItem(Menu):
    """
    Leaf node in the menu tree representing an executable action (Leaf in Composite Pattern).
    """
    
    def __init__(self, name: str, action: Optional[Callable] = None, auto_back: bool = False):
        """
        Initialize a menu item.
        
        Args:
            name: Display name for this menu item
            action: Optional callback function to execute when selected
            auto_back: If True, automatically navigate back to parent menu after execution
        """
        super().__init__(name)
        self.action = action
        self.auto_back = auto_back
    
    def execute(self) -> Optional['Menu']:
        """
        Execute the menu item's action.
        
        Returns:
            Parent menu if auto_back is True, or the result from action if it returns a Menu,
            otherwise None (stays on current menu)
        """
        if self.action:
            result = self.action()
            # If action returns a menu, navigate to it
            if isinstance(result, Menu):
                return result
        
        # If auto_back is enabled, navigate to parent's parent (grandparent)
        # because parent is the submenu we're currently in
        if self.auto_back and self.parent:
            return self.parent.get_parent()
        
        return None
    
    def get_display_text(self) -> str:
        """Get the display text for this menu item."""
        return self.name


class SubMenu(Menu):
    """
    Composite node in the menu tree that can contain other Menu objects (Composite in Composite Pattern).
    """
    
    def __init__(self, name: str):
        """
        Initialize a submenu.
        
        Args:
            name: Display name for this submenu
        """
        super().__init__(name)
        self.children: List[Menu] = []
        self.current_index = 0
    
    def add(self, menu: Menu) -> 'SubMenu':
        """
        Add a child menu component to this submenu.
        
        Args:
            menu: Menu component to add (can be MenuItem or SubMenu)
            
        Returns:
            Self for method chaining
        """
        menu.set_parent(self)
        self.children.append(menu)
        return self
    
    def remove(self, menu: Menu) -> 'SubMenu':
        """
        Remove a child menu component from this submenu.
        
        Args:
            menu: Menu component to remove
            
        Returns:
            Self for method chaining
        """
        if menu in self.children:
            menu.set_parent(None)
            self.children.remove(menu)
            # Adjust current index if needed
            if self.current_index >= len(self.children) and self.current_index > 0:
                self.current_index = len(self.children) - 1
        return self
    
    def get_child(self, index: int) -> Optional[Menu]:
        """
        Get child at specified index.
        
        Args:
            index: Index of child to retrieve
            
        Returns:
            Menu component at index, or None if index out of bounds
        """
        if 0 <= index < len(self.children):
            return self.children[index]
        return None
    
    def get_current_child(self) -> Optional[Menu]:
        """
        Get the currently selected child.
        
        Returns:
            Currently selected Menu component, or None if no children
        """
        return self.get_child(self.current_index)
    
    def get_child_count(self) -> int:
        """Get the number of children in this submenu."""
        return len(self.children)
    
    def next(self):
        """Move selection to next child (wraps around)."""
        if self.children:
            self.current_index = (self.current_index + 1) % len(self.children)
    
    def previous(self):
        """Move selection to previous child (wraps around)."""
        if self.children:
            self.current_index = (self.current_index - 1) % len(self.children)
    
    def reset_index(self):
        """Reset the current index to 0."""
        self.current_index = 0
    
    def execute(self) -> Optional['Menu']:
        """
        Execute the currently selected child.
        
        Returns:
            The menu to navigate to (could be a child submenu or result from action)
        """
        current_child = self.get_current_child()
        if current_child:
            if isinstance(current_child, SubMenu):
                # Navigate into the submenu
                current_child.reset_index()
                return current_child
            else:
                # Execute the menu item
                return current_child.execute()
        return None
    
    def get_display_text(self) -> str:
        """Get the display text for this submenu."""
        return self.name
    
    def get_current_display_text(self) -> str:
        """
        Get the display text for the currently selected child.
        
        Returns:
            Display text of current child, or empty string if no children
        """
        current_child = self.get_current_child()
        if current_child:
            return current_child.get_display_text()
        return ""
    
    def get_navigation_info(self) -> str:
        """
        Get navigation information (e.g., "1/5" for first of 5 items).
        
        Returns:
            String showing current position and total items
        """
        if self.children:
            return f"{self.current_index + 1}/{len(self.children)}"
        return "0/0"


class BackMenuItem(MenuItem):
    """
    Special menu item that navigates back to parent menu.
    """
    
    def __init__(self, name: str = "Back"):
        """
        Initialize a back menu item.
        
        Args:
            name: Display name (defaults to "Back")
        """
        super().__init__(name)
    
    def execute(self) -> Optional['Menu']:
        """
        Navigate back to parent menu.
        
        Returns:
            Parent menu, or None if no parent
        """
        return self.parent.get_parent() if self.parent else None
