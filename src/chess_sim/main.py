import sys
import os
import time
import chess
from models.player import HumanPlayer, ComputerBasic, Stockfish, LichessPlayer
from models.controller import Controller
from models.board import Board
from pathlib import Path
from signal import pause
from dotenv import load_dotenv


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root)) 
from config import CONFIG
from src.display_and_input.chess_menu import ChessMenuBuilder
from src.display_and_input.menu_navigator import MenuNavigator
from src.display_and_input.threaded_lcd_manager import get_lcd_manager, start_lcd_manager, stop_lcd_manager
from src.backend.lichess_manager import LichessGameManager

# Load environment variables from .env file
load_dotenv(project_root / '.env')
API_TOKEN = os.getenv('LICHESS_API_TOKEN')
chess_board = None

if not API_TOKEN:
    print("WARNING: LICHESS_API_TOKEN not found in .env file!")
    print("Please create a .env file from .env.example and add your token.")




def start_game(game_config):
    """
    Start a chess game based on the menu configuration.
    
    Args:
        game_config: Dictionary containing game configuration from menu
    """
    # Get LCD manager for game status display
    lcd_manager = get_lcd_manager()
    
    # Show starting message
    lcd_manager.show_message("Starting game...", "Please wait", 2.0)
    
    board_size = CONFIG.get('models', {}).get('chess_board', {}).get('size_x')
    square_size = CONFIG.get('models', {}).get('chess_board', {}).get('square_size')
    controller = Controller(board_size_cm=board_size, square_size_cm=square_size)
    
    # Get shared lgpio handle from navigator for board
    from src.display_and_input.menu_navigator import MenuNavigator
    navigator_instance = MenuNavigator.get_instance()
    shared_lgpio_handle = navigator_instance.lgpio_handle if navigator_instance else None
    
    # Initialize board with shared lgpio handle
    chess_board = Board(controller, lcd_manager=lcd_manager, lgpio_handle=shared_lgpio_handle)
    
    # Enable game mode for interrupt handling
    lcd_manager.set_game_mode(True)
    
    
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
        
        # Update LCD with game setup
        lcd_manager.set_game_status_mode({
            'game_status': 'player_vs_robot',
            'current_player': white_player,
            'move_count': 0,
            'opponent_name': f'Robot L{robot_level}'
        })
        
    elif game_mode == 'robot_vs_robot':
        # Robot vs Robot mode
        robot1_level = game_config['robot1_level']
        robot2_level = game_config['robot2_level']
        
        white_player = Stockfish(chess.WHITE, robot1_level)
        black_player = Stockfish(chess.BLACK, robot2_level)
        
        chess_board.setup_players(white_player, black_player)
        
        # Update LCD with game setup
        lcd_manager.set_game_status_mode({
            'game_status': 'robot_vs_robot',
            'current_player': white_player,
            'move_count': 0,
            'opponent_name': f'Robot L{robot2_level}'
        })
    
    elif game_mode == 'online_quickmatch':
        # Online Lichess Quickmatch mode
        try:
            # Initialize Lichess manager
            lichess_manager = LichessGameManager(API_TOKEN)
            
            # Get time control settings
            time_minutes = game_config.get('lichess_time', 10)
            increment = game_config.get('lichess_increment', 0)
            rated = game_config.get('lichess_rated', False)
            
            # Create quickmatch and wait for opponent
            chess_board.gantry.center_pieces()
            print("Connecting to Lichess...")

            game_id = lichess_manager.create_quickmatch(
                time_minutes=time_minutes,
                increment_seconds=increment,
                rated=rated
            )
            
            if not game_id:
                print("Failed to create quickmatch")
                lcd_manager.show_message("Quickmatch failed", "Try again later", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Get game information to determine our color
            game_info = lichess_manager.get_game_info(game_id)
            if not game_info:
                print("Failed to get game information")
                lcd_manager.show_message("Game info failed", "Try again later", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            print(f"\n{game_info['white']} ({game_info['white_rating']}) vs {game_info['black']} ({game_info['black_rating']})")
            print(f"Speed: {game_info['speed']} | {'Rated' if game_info['rated'] else 'Casual'}\n")
            
            # Determine our color using authenticated account
            our_username = lichess_manager.get_authenticated_username() or ""
            print(f"Authenticated as: {our_username}")
            
            if game_info['white'].lower() == our_username.lower():
                player_colour = chess.WHITE
                opponent_name = game_info['black']
            else:
                player_colour = chess.BLACK
                opponent_name = game_info['white']
            
            print(f"You are playing as {'White' if player_colour == chess.WHITE else 'Black'}")
            
            # Create game stream for the opponent
            game_stream = lichess_manager.stream_game_state(game_id)
            
            # Setup players
            if player_colour == chess.WHITE:
                white_player = HumanPlayer(chess.WHITE)
                black_player = LichessPlayer(chess.BLACK, game_stream, lichess_manager.client.board)
                black_player.set_opponent_name(opponent_name)
            else:
                white_player = LichessPlayer(chess.WHITE, game_stream, lichess_manager.client.board)
                white_player.set_opponent_name(opponent_name)
                black_player = HumanPlayer(chess.BLACK)
            
            chess_board.setup_players(white_player, black_player)
            
            # Update LCD with game setup
            lcd_manager.set_game_status_mode({
                'game_status': 'online_game',
                'move_count': 0,
                'opponent_name': opponent_name
            })
            
            # Play the game with Board's online method
            game_completed = chess_board.play_game_online(lichess_manager, game_id, player_colour)
            
            # Disable game mode
            lcd_manager.set_game_mode(False)
            
            if game_completed:
                print("Online game completed!")
            else:
                print("Online game interrupted")
                lcd_manager.show_message("Game ended", "Returning to menu", 2.0)
                time.sleep(2)
            
        except Exception as e:
            print(f"Error in online game: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always cleanup GPIO resources
            chess_board.gantry.cleanup()
            # Return to menu display
            navigator_instance = MenuNavigator.get_instance()
            if navigator_instance:
                navigator_instance.navigate_to_root()
        return
    
    elif game_mode == 'online_friend_challenge':
        # Online Lichess Friend Challenge mode
        try:
            # Initialize Lichess manager
            lichess_manager = LichessGameManager(API_TOKEN)
            
            # Get friend username from config
            friend_username = game_config.get('friend_username')
            if not friend_username:
                print("No friend username provided")
                lcd_manager.show_message("No friend set", "Check config", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Get time control settings
            time_minutes = game_config.get('lichess_time', 10)
            increment = game_config.get('lichess_increment', 0)
            rated = game_config.get('lichess_rated', False)
            
            # Center pieces before starting
            chess_board.gantry.center_pieces()
            
            # Show LCD message
            lcd_manager.show_message(f"Challenging", friend_username[:14], 2.0)
            
            # Challenge the friend and wait for acceptance
            print(f"Sending challenge to {friend_username}...")
            game_id = lichess_manager.challenge_user(
                username=friend_username,
                time_minutes=time_minutes,
                increment_seconds=increment,
                rated=rated
            )
            
            if not game_id:
                print("Challenge was declined or timed out")
                lcd_manager.show_message("Challenge failed", "Not accepted", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Get game information to determine our color
            game_info = lichess_manager.get_game_info(game_id)
            if not game_info:
                print("Failed to get game information")
                lcd_manager.show_message("Game info failed", "Try again later", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            print(f"\n{game_info['white']} ({game_info['white_rating']}) vs {game_info['black']} ({game_info['black_rating']})")
            print(f"Speed: {game_info['speed']} | {'Rated' if game_info['rated'] else 'Casual'}\n")
            
            # Determine our color using authenticated account
            our_username = lichess_manager.get_authenticated_username() or ""
            print(f"Authenticated as: {our_username}")
            print(f"game_info['white']: {game_info['white']}")
            if game_info['white'].lower() == our_username.lower():
                player_colour = chess.WHITE
                opponent_name = game_info['black']
            else:
                player_colour = chess.BLACK
                opponent_name = game_info['white']
            
            print(f"You are playing as {'White' if player_colour == chess.WHITE else 'Black'}")
            
            # Create game stream for the opponent
            game_stream = lichess_manager.stream_game_state(game_id)
            
            # Setup players
            if player_colour == chess.WHITE:
                white_player = HumanPlayer(chess.WHITE)
                black_player = LichessPlayer(chess.BLACK, game_stream, lichess_manager.client.board)
                black_player.set_opponent_name(opponent_name)
            else:
                white_player = LichessPlayer(chess.WHITE, game_stream, lichess_manager.client.board)
                white_player.set_opponent_name(opponent_name)
                black_player = HumanPlayer(chess.BLACK)
            
            chess_board.setup_players(white_player, black_player)
            
            # Update LCD with game setup
            lcd_manager.set_game_status_mode({
                'game_status': 'online_game',
                'move_count': 0,
                'opponent_name': opponent_name
            })
            
            # Play the game with Board's online method
            game_completed = chess_board.play_game_online(lichess_manager, game_id, player_colour)
            
            # Disable game mode
            lcd_manager.set_game_mode(False)
            
            if game_completed:
                print("Online game completed!")
            else:
                print("Online game interrupted")
                lcd_manager.show_message("Game ended", "Returning to menu", 2.0)
                time.sleep(2)
            
        except Exception as e:
            print(f"Error in friend challenge: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always cleanup GPIO resources
            chess_board.gantry.cleanup()
            # Return to menu display
            navigator_instance = MenuNavigator.get_instance()
            if navigator_instance:
                navigator_instance.navigate_to_root()
        return
    
    elif game_mode == 'archived_game':
        # Archived game replay mode
        try:
            from pgn_reader import PGNReader, PGNExecutor
            
            # Get the filename from game config
            filename = game_config.get('archived_filename')
            if not filename:
                print("No archived filename provided")
                chess_board.gantry.cleanup()
                lcd_manager.show_message("No file", "Select a game", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Initialize PGN reader and executor
            pgn_reader = PGNReader()
            pgn_executor = PGNExecutor(chess_board, controller, chess_board.gantry, chess_board.path_planner_board, lcd_manager)
            
            # Load the game
            print(f"Loading archived game: {filename}")
            game_data = pgn_reader.read_pgn_file(filename)
            
            if not game_data:
                print(f"Failed to load game from {filename}")
                chess_board.gantry.cleanup()
                lcd_manager.show_message("Load failed", "Invalid PGN", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Display game information
            print(f"\nGame: {game_data['white']} vs {game_data['black']}")
            print(f"Event: {game_data['event']}")
            print(f"Date: {game_data['date']}")
            print(f"Result: {game_data['result']}")
            print(f"Total moves: {game_data['move_count']}")
            print("=" * 50)
            
            # Update LCD with game info
            lcd_manager.set_game_status_mode({
                'game_status': 'archived_game',
                'current_player': None,
                'move_count': 0,
                'opponent_name': f"{game_data['white'][:8]} vs {game_data['black'][:8]}"
            })
            
            # Load game into executor
            if not pgn_executor.load_game(game_data):
                print("Failed to load game into executor")
                chess_board.gantry.cleanup()
                lcd_manager.show_message("Load failed", "Executor error", 3.0)
                time.sleep(3)
                navigator_instance = MenuNavigator.get_instance()
                if navigator_instance:
                    navigator_instance.navigate_to_root()
                return
            
            # Execute the game
            print("Starting game execution...")
            success = pgn_executor.execute_game(delay_between_moves=2.0)
            
            # Disable game mode
            lcd_manager.set_game_mode(False)
            
            if success:
                print("Archived game execution completed successfully!")
                lcd_manager.show_message("Game completed!", "Archive replay done", 3.0)
            else:
                print("Archived game execution failed or was interrupted")
                lcd_manager.show_message("Game failed!", "Archive replay error", 3.0)
            
            time.sleep(3)
            
        except Exception as e:
            print(f"Error in archived game: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always cleanup GPIO resources
            chess_board.gantry.cleanup()
            # Return to menu display
            navigator_instance = MenuNavigator.get_instance()
            if navigator_instance:
                navigator_instance.navigate_to_root()
        return
    
    # Start the game (for offline modes)
    try:
        game_completed = chess_board.play_game_gui()
        
        # Disable game mode
        lcd_manager.set_game_mode(False)
        
        if game_completed:
            print("Game completed successfully!")
        else:
            print("Game was interrupted")
            lcd_manager.show_message("Game ended", "Returning to menu", 2.0)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nGame interrupted by user. Exiting...")
        lcd_manager.set_game_mode(False)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        lcd_manager.set_game_mode(False)
        chess_board.gantry.cleanup()
    finally:
        print("Game session ended.")
        # Return to menu display
        navigator_instance = MenuNavigator.get_instance()
        if navigator_instance:
            navigator_instance.navigate_to_root()
        chess_board.gantry.cleanup()


def main():
    """Main entry point with menu system."""
    print("Initializing Chess Game Menu System...")
    print("Press and hold encoder button for 1 second during game to interrupt")
    
    # Initialize lgpio first (shared by button and gantry to avoid conflicts)
    import lgpio
    lgpio_handle = lgpio.gpiochip_open(0)
    
    # Start the threaded LCD manager
    start_lcd_manager()
    lcd_manager = get_lcd_manager()
    
    # Build the menu structure
    menu_builder = ChessMenuBuilder()
    menu_builder.set_start_game_callback(start_game)
    root_menu = menu_builder.build()
    
    # Create menu navigator with lgpio button
    try:
        navigator = MenuNavigator(root_menu, use_threaded_lcd=True, enable_button=True, lgpio_handle=lgpio_handle)
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
    finally:
        # Stop the LCD manager
        lcd_manager.set_game_mode(False)
        stop_lcd_manager()


if __name__ == "__main__":
    main()