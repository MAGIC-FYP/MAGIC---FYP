import sys
import os
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
from src.backend.lichess_manager import LichessGameManager
from pgn_reader import PGNReader, PGNExecutor

# Load environment variables from .env file
load_dotenv(project_root / '.env')
API_TOKEN = os.getenv('LICHESS_API_TOKEN')

if not API_TOKEN:
    print("WARNING: LICHESS_API_TOKEN not found in .env file!")
    print("Please create a .env file from .env.example and add your token.")


def play_online_game(chess_board, lichess_manager, game_id, player_colour):
    """
    Special game loop for online Lichess games.
    Sends human moves to Lichess and receives opponent moves via stream.
    """
    print("Starting online game!")
    print("Type 'resign' to resign the game\n")
    
    while not chess_board.is_game_over():
        print("\n" + "-" * 40)
        current_player = chess_board.current_player
        print(f"Current player: ({'White' if current_player.colour == chess.WHITE else 'Black'})")
        print(chess_board.board)
        
        # Get move from current player
        move = current_player.get_move(chess_board.board)
        
        if move:
            if chess_board.make_move(move):
                # If it's the human player's move, send it to Lichess
                if isinstance(current_player, HumanPlayer):
                    success = lichess_manager.make_move(game_id, move)
                    if not success:
                        print("Failed to send move to Lichess. Game may desync.")
                
                chess_board.switch_player()
            else:
                print("Invalid move.")
        else:
            # Move is None - either game ended or error occurred
            print("No move available or game ended.")
            break
    
    print("\n" + "=" * 40)
    print("Game over!")
    print(chess_board.board)
    
    # Show result
    result = chess_board.board.result()
    if result == "1-0":
        print("White wins!")
    elif result == "0-1":
        print("Black wins!")
    elif result == "1/2-1/2":
        print("It's a draw!")


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
            print("Connecting to Lichess...")
            game_id = lichess_manager.create_quickmatch(
                time_minutes=time_minutes,
                increment_seconds=increment,
                rated=rated
            )
            
            if not game_id:
                print("Failed to create quickmatch")
                return
            
            # Get game information to determine our color
            game_info = lichess_manager.get_game_info(game_id)
            if not game_info:
                print("Failed to get game information")
                return
            
            print(f"\n{game_info['white']} ({game_info['white_rating']}) vs {game_info['black']} ({game_info['black_rating']})")
            print(f"Speed: {game_info['speed']} | {'Rated' if game_info['rated'] else 'Casual'}\n")
            
            # Determine which color we are playing
            # Note: You'll need to get the actual username - for now we'll ask
            our_username = input("Enter your Lichess username: ").strip()
            
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
            
            # If game already has moves (unlikely for quickmatch), apply them
            if game_info['moves']:
                temp_board = chess.Board()
                for move_uci in game_info['moves']:
                    temp_board.push_uci(move_uci)
                chess_board.set_fen(temp_board.fen())
                # Update last_moves for LichessPlayer
                lichess_player = white_player if isinstance(white_player, LichessPlayer) else black_player
                lichess_player.last_moves = game_info['moves']
            
            # Play the game with custom online loop
            play_online_game(chess_board, lichess_manager, game_id, player_colour)
            return
            
        except Exception as e:
            print(f"Error in online game: {e}")
            import traceback
            traceback.print_exc()
            return
    
    elif game_mode == 'archived_game':
        # Archived game replay mode
        try:
            filename = game_config.get('archived_filename')
            if not filename:
                print("No archived game filename specified")
                return
            
            # Initialize PGN reader and executor
            pgn_reader = PGNReader()
            pgn_executor = PGNExecutor(chess_board, controller)
            
            # Load the game
            game_data = pgn_reader.read_pgn_file(filename)
            if not game_data:
                print(f"Failed to load archived game: {filename}")
                return
            
            # Load game into executor
            if not pgn_executor.load_game(game_data):
                print("Failed to load game into executor")
                return
            
            # Execute the game
            print("Starting archived game execution...")
            print("Press Ctrl+C to stop execution")
            
            success = pgn_executor.execute_game(delay_between_moves=2.0)
            
            if success:
                print("Archived game execution completed successfully!")
            else:
                print("Archived game execution was interrupted or failed")
            
            return
            
        except KeyboardInterrupt:
            print("\nArchived game execution interrupted by user")
            return
        except Exception as e:
            print(f"Error in archived game: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Start the game (for offline modes that require players)
    if game_mode in ['player_vs_robot', 'robot_vs_robot']:
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