import sys
import chess
from models.player import HumanPlayer, ComputerBasic, Stockfish
from models.controller import Controller
from models.board import Board
from pathlib import Path
import signal, sys


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root)) 
from config import CONFIG

def handle_exit(signum, frame):
    print("Exiting cleanly...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    board_size = CONFIG.get('models', {}).get('chess_board', {}).get('size_x')
    square_size = CONFIG.get('models', {}).get('chess_board', {}).get('square_size')
    controller = Controller(board_size_cm=board_size, square_size_cm=square_size)
    chess_board = Board(controller)  

    # Set up the players
    white_player = HumanPlayer(chess.WHITE)
    #black_player = ComputerBasic(chess.BLACK, 1)
    black_player = Stockfish(chess.BLACK, 1)
    chess_board.setup_players(white_player, black_player)
    chess_board.set_fen('7k/8/8/8/4q3/3P4/8/6K1 w - - 0 1')
    
    # fen = 'rnbqkb1r/pppppppp/7n/8/8/3P4/PPP1PPPP/RNBQKBNR w KQkq - 1 2'
    # chess_board.set_fen(fen)
    
    # Start the game
    try:
        chess_board.play_game_gui()
    except KeyboardInterrupt:
        print("keyboard interrupt")
        chess_board.cleanup(1)

    

    # except Exception as e:
    #     print(f"\nAn error occurred: {e}")
    # finally:
    #     print("Game session ended.")







if __name__ == "__main__":
    main()