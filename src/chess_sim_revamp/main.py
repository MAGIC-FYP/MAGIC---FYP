from models.player import HumanPlayer, ComputerBasic, Stockfish
from models.controller import Controller
from models.board import Board
import chess

def main():
    controller = Controller(board_size_cm=40.0, square_size_cm=5.0)
    chess_board = Board(controller)  

    # Set up the players
    white_player = HumanPlayer(chess.WHITE)
    black_player = ComputerBasic(chess.BLACK, 1)
    chess_board.setup_players(white_player, black_player)
    #chess_board.set_fen('8/8/8/4p1K1/2k1P3/8/8/8 b - - 0 1')
    
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