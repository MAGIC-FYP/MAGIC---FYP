import chess
from typing import List, Optional, Tuple
from models.player import BasePlayer, HumanPlayer
from models.controller import Controller
from models.graveyard import GraveyardSquare
from gui.chess_gui import Display

class Board:
    def __init__(self, controller: Controller):
        self.board = chess.Board()
        self.controller = controller
        self.white_player: Optional[BasePlayer] = None
        self.black_player: Optional[BasePlayer] = None
        self.current_player: Optional[BasePlayer] = None
        self.move_history: List[chess.Move] = []
    
    def setup_players(self, white_player: BasePlayer, black_player: BasePlayer) -> None:
        '''Set up the players for this game'''
        self.white_player = white_player
        self.black_player = black_player
        self.current_player = self.white_player  # White moves first

    def switch_player(self) -> None:
        '''Switch the current player'''
        self.current_player = self.black_player if self.current_player == self.white_player else self.white_player

    def make_move(self, move: chess.Move) -> bool:
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            return True
        return False
    
    def is_game_over(self) -> bool:
        return self.board.is_game_over()
    
    def play_game(self) -> None:
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return
            
        print("Starting new chess game!")

        # # Ensure the controller is calibrated
        # if not self.controller.calibrated:
        #     self.controller.calibrate()
        
        while not self.is_game_over():
            print("\n" + "-" * 40)
            print(f"Current player: ({'White' if self.current_player == self.white_player else 'Black'})")
            print(self.board)  # Display the board

            move = self.current_player.get_move(self.board)

            if move:
                if self.make_move(move):
                    self.switch_player()
                else:
                    print("Invalid move.")
            else:
                print("No legal moves available.")
                break
        
        print("\n" + "=" * 40)
        print("Game over!")
        print(self.board)
    
    def play_game_gui(self) -> None:
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return
            
        print("Starting new chess game!")

        # # Ensure the controller is calibrated
        # if not self.controller.calibrated:
        #     self.controller.calibrate()
        display = Display()
        
        while not self.is_game_over():
            print("\n" + "-" * 40)
            print(f"Current player: ({'White' if self.current_player == self.white_player else 'Black'})")
            display.disp_board(self.board, self.current_player)

            if type(self.current_player) == HumanPlayer:
                move = display.get_next_move_from_click(self.board, self.current_player)
                move = chess.Move(move[0], move[1])
            else:
                move = self.current_player.get_move(self.board)

            if move:
                if self.make_move(move):
                    self.switch_player()
                else:
                    print("Invalid move.")
            else:
                print("No legal moves available.")
                break

            
