"""
Example/test file demonstrating the menu system with LCD and rotary encoder.

This file shows how to use the Composite Pattern menu system and can be run
independently to test the menu navigation without starting a full chess game.
"""

import sys
import os
from signal import pause

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import with absolute imports
from menu import SubMenu, MenuItem, BackMenuItem
from menu_navigator import MenuNavigator
from LCD import LCD


def example_action(name):
    """Example action callback for menu items."""
    def action():
        print(f"\n>>> Action executed: {name}")
    return action


def build_simple_test_menu():
    """
    Build a simple test menu to demonstrate the menu system.
    
    Returns:
        Root SubMenu for testing
    """
    # Create root menu
    root = SubMenu("Test Menu")
    
    # Add some simple menu items
    root.add(MenuItem("Option 1", example_action("Option 1")))
    root.add(MenuItem("Option 2", example_action("Option 2")))
    
    # Add a submenu with auto_back items (like color selection)
    submenu1 = SubMenu("Select Color")
    submenu1.add(MenuItem("Red", example_action("Red selected"), auto_back=True))
    submenu1.add(MenuItem("Blue", example_action("Blue selected"), auto_back=True))
    submenu1.add(MenuItem("Green", example_action("Green selected"), auto_back=True))
    submenu1.add(BackMenuItem())
    root.add(submenu1)
    
    # Add another submenu with nested submenus
    submenu2 = SubMenu("Settings")
    
    nested_submenu = SubMenu("Difficulty")
    nested_submenu.add(MenuItem("Easy", example_action("Easy mode"), auto_back=True))
    nested_submenu.add(MenuItem("Medium", example_action("Medium mode"), auto_back=True))
    nested_submenu.add(MenuItem("Hard", example_action("Hard mode"), auto_back=True))
    nested_submenu.add(BackMenuItem())
    
    submenu2.add(nested_submenu)
    submenu2.add(MenuItem("Save Settings", example_action("Settings saved")))
    submenu2.add(BackMenuItem())
    root.add(submenu2)
    
    return root


def test_menu_structure():
    """Test the menu structure without hardware (no LCD/encoder)."""
    print("Testing Menu Structure (No Hardware)")
    print("=" * 50)
    
    root = build_simple_test_menu()
    
    # Test navigation
    print(f"\nRoot menu: {root.get_display_text()}")
    print(f"Children count: {root.get_child_count()}")
    
    # Navigate through children
    for i in range(root.get_child_count()):
        child = root.get_child(i)
        print(f"  [{i}] {child.get_display_text()}")
    
    # Test next/previous
    print(f"\nCurrent selection: {root.get_current_display_text()}")
    root.next()
    print(f"After next(): {root.get_current_display_text()}")
    root.next()
    print(f"After next(): {root.get_current_display_text()}")
    root.previous()
    print(f"After previous(): {root.get_current_display_text()}")
    
    # Test execute (navigate into submenu)
    root.current_index = 2  # Select "Submenu 1"
    print(f"\nExecuting: {root.get_current_display_text()}")
    next_menu = root.execute()
    if next_menu:
        print(f"Navigated to: {next_menu.get_display_text()}")
        print(f"Children count: {next_menu.get_child_count()}")
        for i in range(next_menu.get_child_count()):
            child = next_menu.get_child(i)
            print(f"  [{i}] {child.get_display_text()}")
    
    print("\n" + "=" * 50)


def test_with_hardware():
    """Test the menu system with actual LCD and rotary encoder hardware."""
    print("Testing Menu System with Hardware")
    print("=" * 50)
    print("Instructions:")
    print("  - Rotate encoder to navigate menu items")
    print("  - Press encoder button to select/enter")
    print("  - Select 'Back' to go to previous menu")
    print("  - Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        # Build test menu
        root = build_simple_test_menu()
        
        # Create navigator
        navigator = MenuNavigator(root)
        navigator.start()
        
        # Keep running
        pause()
        
    except KeyboardInterrupt:
        print("\n\nExiting test...")
        if 'navigator' in locals():
            navigator.stop()
    except Exception as e:
        print(f"\nError: {e}")
        if 'navigator' in locals():
            navigator.stop()


def main():
    """Main entry point for the example."""
    if len(sys.argv) > 1 and sys.argv[1] == "--no-hardware":
        # Test without hardware
        test_menu_structure()
    else:
        # Test with hardware
        test_with_hardware()


if __name__ == "__main__":
    main()
