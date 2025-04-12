import sys
import chess
from models.player import HumanPlayer, ComputerBasic, Stockfish
from models.controller import Controller
from models.board import Board
from pathlib import Path


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root)) 
from config import CONFIG


def main():
    board_size = CONFIG.get('models', {}).get('chess_board', {}).get('size_x')
    square_size = CONFIG.get('models', {}).get('chess_board', {}).get('square_size')
    controller = Controller(board_size_cm=board_size, square_size_cm=square_size)
    chess_board = Board(controller)  

    # Set up the players
    white_player = HumanPlayer(chess.WHITE)
    black_player = ComputerBasic(chess.BLACK, 1)#Stockfish(chess.BLACK, 1)
    chess_board.setup_players(white_player, black_player)
    #chess_board.set_fen('8/8/8/4p1K1/2k1P3/8/8/8 b - - 0 1')
    
    fen = 'r1b2b1r/ppp1pkpp/8/8/2Pn4/2N2qP1/PP1P1P1P/R1B2RK1 w - - 4 11'
    chess_board.set_fen(fen)
    
    # Start the game
    #try:
    chess_board.play_game_gui()
    # except KeyboardInterrupt:
    #     print("\nGame interrupted by user. Exiting...")
    # except Exception as e:
    #     print(f"\nAn error occurred: {e}")
    # finally:
    #     print("Game session ended.")

if __name__ == "__main__":
    main()