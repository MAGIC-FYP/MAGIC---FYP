import chess
import numpy as np
from typing import List, Optional, Tuple
from models.player import BasePlayer, HumanPlayer
from models.controller import Controller
from models.graveyard import Graveyard
from gui.chess_gui import Display
from models.log import logger
from gantry_control.tiles import TileSensor
from gantry_control.gantry import GantryControl
from algorithms.path_planner import Board as PathPlannerBoard
import time
from algorithms.algorithms_expanding_aStar import find_path, crowd_control

class Board:
    def __init__(self, controller: Controller):
        self.board = chess.Board()
        self.controller = controller
        self.graveyard = Graveyard()
        self.logger = logger()
        self.Surface = TileSensor()
        self.gantry = GantryControl(max_x=36, min_x=1.75, max_y=32, min_y=-1.6)
        self.path = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.path_extra = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.white_player: Optional[BasePlayer] = None
        self.black_player: Optional[BasePlayer] = None
        self.current_player: Optional[BasePlayer] = None
        self.move_history: List[chess.Move] = []
        self.dead_pieces: List[chess.Piece] = []
        self.path_planner_board = PathPlannerBoard()

        self.gantry.initialise()
        self.gantry.home()

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)
        self.current_player = self.white_player if self.board.turn == chess.WHITE else self.black_player
        self.graveyard.pre_loaded_graveyard(fen)  # Pass FEN to detect captured pieces
    
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
            if self.board.piece_at(move.to_square): #piece has been captured
                self.dead_pieces.append(self.board.piece_at(move.to_square))
                piece = self.board.piece_at(move.to_square)
                self.graveyard.place_piece(piece)

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

    def get_move_from_surface(self, board: chess.Board):

        prev_bitmap = np.zeros((8, 8))
        for rank_idx in range(8): # Iterate through ranks (rows) from 0 to 7
            for file_idx in range(8): # Iterate through files (columns) from 0 to 7                
                square_index = rank_idx * 8 + file_idx
                if board.piece_at(square_index):
                    prev_bitmap[rank_idx, file_idx] = 1 # Piece is present


        change = 0
        while change == 0:
            cur_bitmap = np.array(self.Surface.get_sensor_bitmap())[:, 1:9]
            dif_bitmap = np.zeros((8, 8))
            for i in range(8):
                for j in range(8):
                    if cur_bitmap[i][j] != prev_bitmap[i][j]:
                        dif_bitmap[i, j] = 1
                        from_square = chess.square(j, i)
            change = np.sum(dif_bitmap)        
        prev_bitmap = cur_bitmap


        change = 0
        while change == 0:
            cur_bitmap = self.Surface.get_sensor_bitmap()
            dif_bitmap = np.zeros((8, 8))
            for i in range(8):
                for j in range(8):
                    if cur_bitmap[i][j+1] != prev_bitmap[i][j]:
                        dif_bitmap[i, j] = 1
                        to_square = chess.square(j, i)
            change = np.sum(dif_bitmap) 

        move = chess.Move(from_square, to_square)
        print(f"move: {move}")
        # The 'bitmap' variable now holds the 8x8 representation as requested.
        # For example, bitmap[0][0] corresponds to a1, bitmap[0][7] to h1,
        # bitmap[7][0] to a8, and bitmap[7][7] to h8.

        return move
    
    def cleanup(self, exit_code: int):
        self.gantry.cleanup()
        self.Surface.close()
        if exit_code == 1:
            self.logger.log("Keyboard interrupt")
        self.logger.log("cleaning up")
        self.logger.end_log()
        display.close_disp()
        pygame.quit()
        sys.exit(exit_code)
    
    def play_game_gui(self) -> None:
        path_const = (3.5/5)
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return
            
        print("Starting new chess game!")
        self.logger.log("Starting new chess game")

        display = Display(log= self.logger)
        
        #while not self.is_game_over():
        while True:
            print("\n" + "-" * 40)
            print(f"Current player: ({'White' if self.current_player == self.white_player else 'Black'})")
            display.disp_board(self.board, self.graveyard, self.current_player)
            self.logger.log(f"board fen:\t{self.board.fen()}")
            if type(self.current_player) == HumanPlayer:
                #move = display.get_next_move_from_click(self.board, self.graveyard, self.current_player)
                #move = self.get_move_from_surface(self.board)
                move = False
                while move == False:
                    move = display.get_move_from_surface_gui(self.board, self.Surface, self.gantry, self.graveyard, self.current_player)
                    
                    
                
            else:
                move = self.current_player.get_move(self.board)

            if move:
                self.logger.log(f"attempted move:\t{move}")
                self.path_planner_board.place_from_fen(self.board.fen())
                if self.make_move(move):
                    if type(self.current_player) != HumanPlayer:
                        self.path = self.path_planner_board.get_full_path_simpli(chess.Move.uci(move))
                        self.logger.log(f"Path:\t{self.path}")
                        if self.path == False:
                            break
                        display.path = self.path 
                        display.disp_board(self.board, self.graveyard, self.current_player)
                        print(self.path)
                        self.logger.log(f"path success")

                        for path in self.path:
                            self.gantry.move(path[0][0]*path_const, path[0][1]*path_const, 10)
                            self.gantry.electromagnet(True)
                            time.sleep(0.3)

                            for point in path:
                                
                                self.gantry.move(point[0]*path_const, point[1]*path_const, 4)
                                
                            self.gantry.electromagnet(False)
                            time.sleep(0.3)
                            self.gantry.electromagnet(True)
                            time.sleep(0.3)
                            self.gantry.electromagnet(False)
                            time.sleep(0.4)
                        
                        self.gantry.move(10, 10, 10)
                    
                    self.switch_player()
                else:
                    print("Invalid move.")
            else:
                print("No legal moves available.")
                break

        result = self.board.result()

        if result == "1-0":
            self.logger.log("Game over, result: White wins")
            print("White wins!")
        elif result == "0-1":
            self.logger.log("Game over, result: Black wins")
            print("Black wins!")
        elif result == "1/2-1/2":
            self.logger.log("Game over, result: Draw")
            print("It's a draw!")
        self.logger.end_log()
        display.close_disp()

            
