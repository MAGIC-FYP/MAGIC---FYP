#!/usr/bin/env python3
"""
Example script demonstrating the threaded LCD manager integration.

This script shows how to use the threaded LCD manager to display
game status while running other operations concurrently.
"""

import time
import threading
from src.display_and_input.threaded_lcd_manager import get_lcd_manager, start_lcd_manager, stop_lcd_manager
import chess

def simulate_chess_game():
    """Simulate a chess game with LCD status updates."""
    lcd_manager = get_lcd_manager()
    
    # Create a mock chess board
    board = chess.Board()
    
    print("Starting simulated chess game...")
    
    # Switch to game status mode
    lcd_manager.set_game_status_mode({
        'game_status': 'simulation',
        'current_player': 'White',
        'move_count': 0,
        'opponent_name': 'Computer'
    })
    
    # Simulate game moves
    moves = [
        ('e2e4', 'White plays e4'),
        ('e7e5', 'Black plays e5'),
        ('g1f3', 'White plays Nf3'),
        ('b8c6', 'Black plays Nc6'),
        ('f1b5', 'White plays Bb5'),
        ('a7a6', 'Black plays a6'),
        ('b5a4', 'White plays Ba4'),
        ('d7d6', 'Black plays d6'),
    ]
    
    for i, (move_uci, description) in enumerate(moves):
        # Update LCD with current state
        lcd_manager.update_game_state(
            current_player='White' if i % 2 == 0 else 'Black',
            move_count=i + 1,
            last_move=move_uci,
            game_status='thinking' if i % 2 == 1 else 'your_turn'
        )
        
        print(f"Move {i+1}: {description}")
        
        # Simulate thinking time
        if i % 2 == 1:  # Black's turn
            lcd_manager.update_game_state(thinking_time=2.0)
            time.sleep(2)
        
        time.sleep(1)
    
    # Show game over
    lcd_manager.show_message("Game complete!", "Thanks for playing", 3.0)
    time.sleep(3)
    
    # Return to idle
    lcd_manager.show_idle()

def simulate_menu_navigation():
    """Simulate menu navigation."""
    lcd_manager = get_lcd_manager()
    
    print("Simulating menu navigation...")
    
    # Show different menu states
    menu_states = [
        ("Main Menu", "> Player vs Robot 1/3"),
        ("Player vs Robot", "> Player Colour 1/3"),
        ("Player Colour", "> White 1/2"),
        ("Robot Level", "> Level 5 5/20"),
        ("Start Game", "Press to start"),
    ]
    
    for title, selection in menu_states:
        lcd_manager.show_message(title, selection, 2.0)
        time.sleep(2.5)
    
    lcd_manager.show_idle()

def main():
    """Main demonstration function."""
    print("Threaded LCD Manager Demo")
    print("=" * 40)
    
    # Start the LCD manager
    start_lcd_manager()
    
    try:
        # Show idle screen
        lcd_manager = get_lcd_manager()
        lcd_manager.show_idle()
        time.sleep(2)
        
        # Run simulations in sequence
        print("\n1. Menu Navigation Simulation")
        simulate_menu_navigation()
        time.sleep(1)
        
        print("\n2. Chess Game Simulation")
        simulate_chess_game()
        time.sleep(1)
        
        print("\n3. Concurrent Operations Demo")
        # Demonstrate concurrent operations
        lcd_manager.show_message("Concurrent demo", "Running...", 0)
        
        # Start a background task
        def background_task():
            for i in range(10):
                lcd_manager.update_game_state(
                    current_player='White' if i % 2 == 0 else 'Black',
                    move_count=i,
                    game_status='thinking',
                    thinking_time=float(i)
                )
                time.sleep(0.5)
        
        # Run background task
        bg_thread = threading.Thread(target=background_task)
        bg_thread.start()
        
        # Do other work in main thread
        for i in range(5):
            print(f"Main thread working... {i+1}/5")
            time.sleep(1)
        
        bg_thread.join()
        
        print("\nDemo completed successfully!")
        lcd_manager.show_message("Demo complete!", "All tests passed", 3.0)
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError in demo: {e}")
    finally:
        # Stop the LCD manager
        stop_lcd_manager()
        print("LCD manager stopped")

if __name__ == "__main__":
    main()
