import sys
import chess
from models.player import HumanPlayer, ComputerBasic, Stockfish
from models.controller import Controller
from models.board import Board
from pathlib import Path
from signal import pause


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root)) 
from config import CONFIG
from src.display_and_input.chess_menu import ChessMenuBuilder
from src.display_and_input.menu_navigator import MenuNavigator


def start_game(game_config):
    """
    Start a chess game based on the menu configuration.
    
    Args:
        game_config: Dictionary containing game configuration from menu
    """
    board_size = CONFIG.get('models', {}).get('chess_board', {}).get('size_x')
    square_size = CONFIG.get('models', {}).get('chess_board', {}).get('square_size')
    controller = Controller(board_size_cm=board_size, square_size_cm=square_size)
    chess_board = Board(controller)
    
    game_mode = game_config['game_mode']
    
    if game_mode == 'player_vs_robot':
        # Player vs Robot mode
        player_colour = game_config['player_colour']
        robot_level = game_config['robot_level']
        
        if player_colour == chess.WHITE:
            white_player = HumanPlayer(chess.WHITE)
            black_player = Stockfish(chess.BLACK, robot_level)
        else:
            white_player = Stockfish(chess.WHITE, robot_level)
            black_player = HumanPlayer(chess.BLACK)
        
        chess_board.setup_players(white_player, black_player)
        
    elif game_mode == 'robot_vs_robot':
        # Robot vs Robot mode
        robot1_level = game_config['robot1_level']
        robot2_level = game_config['robot2_level']
        
        white_player = Stockfish(chess.WHITE, robot1_level)
        black_player = Stockfish(chess.BLACK, robot2_level)
        
        chess_board.setup_players(white_player, black_player)
    
    # Start the game
    try:
        chess_board.play_game()
    except KeyboardInterrupt:
        print("\nGame interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("Game session ended.")


def main():
    """Main entry point with menu system."""
    print("Initializing Chess Game Menu System...")
    
    # Build the menu structure
    menu_builder = ChessMenuBuilder()
    menu_builder.set_start_game_callback(start_game)
    root_menu = menu_builder.build()
    
    # Create menu navigator with LCD and rotary encoder
    try:
        navigator = MenuNavigator(root_menu)
        navigator.start()
        
        # Keep the program running
        pause()
        
    except KeyboardInterrupt:
        print("\nExiting menu system...")
        if 'navigator' in locals():
            navigator.stop()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if 'navigator' in locals():
            navigator.stop()


if __name__ == "__main__":
    main()