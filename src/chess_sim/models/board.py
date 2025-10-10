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
from config import load_config
from algorithms.algorithms_expanding_aStar import find_path, crowd_control
config = load_config()

class Board:
    def __init__(self, controller: Controller, lcd_manager=None):
        self.board = chess.Board()
        self.controller = controller
        self.graveyard = Graveyard()
        self.logger = logger()
        self.Surface = TileSensor()
        self.lcd_manager = lcd_manager  # Reference to LCD manager for interrupt checking
        
        # Initialize gantry with interrupt callback
        self.gantry = GantryControl(max_x=36, min_x=1.75, max_y=32, min_y=-1.6)
        if self.lcd_manager:
            # Set interrupt callback so gantry can check for interrupts during movements
            self.gantry.set_interrupt_callback(lambda: self.lcd_manager.is_game_interrupt_requested())
        
        self.path = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.path_extra = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.white_player: Optional[BasePlayer] = None
        self.black_player: Optional[BasePlayer] = None
        self.current_player: Optional[BasePlayer] = None
        self.move_history: List[chess.Move] = []
        self.dead_pieces: List[chess.Piece] = []
        self.path_planner_board = PathPlannerBoard()
        self.next_graveyard = None
        self.is_capture = False
        self.lcd_manager = lcd_manager  # Reference to LCD manager for interrupt checking
        try:
            self.gantry.cleanup()
        except:
            pass
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
                self.next_graveyard = self.graveyard.get_lowest_available(piece)
                self.graveyard.place_piece(piece)
                self.is_capture = True
                
            else:
                self.next_graveyard = None
                self.is_capture = False
            self.board.push(move)
            self.move_history.append(move)
            
            return True
        return False
    
    def is_game_over(self) -> bool:
        return self.board.is_game_over()
    
    def play_game(self) -> bool:
        """Play a chess game. Returns True if game completed normally, False if interrupted."""
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return False
              
        print("Starting new chess game!")
        
        while not self.is_game_over():
            # Check for game interrupt
            if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                print("\nGame interrupted by user")
                self.lcd_manager.clear_game_interrupt()
                return False
            
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
        return True
    
    def reset(self):
        self.board.reset()
        self.current_player = self.white_player if self.board.turn == chess.WHITE else self.black_player
        self.graveyard.reset()
        self.move_history = []
        self.dead_pieces = []
        self.path = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.path_extra = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        self.next_graveyard = None
        self.is_capture = False
        self.gantry.home()

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
    
    def play_game_gui(self) -> bool:
        """Play a chess game with GUI. Returns True if game completed normally, False if interrupted."""
        quick_speed = config['gantry']['quick_speed']
        slow_speed = config['gantry']['slow_speed']
        path_const = (3.5/5)
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return False
            
        print("Starting new chess game!")
        self.logger.log("Starting new chess game")

        display = Display(log= self.logger)
        self.gantry.center_pieces()
        #while not self.is_game_over():
        while self.is_game_over() == False:
            # Check for game interrupt
            if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                print("\nGame interrupted by user")
                self.logger.log("Game interrupted by user")
                # display.close_disp()
                self.lcd_manager.clear_game_interrupt()
                return False

            print("\n" + "-" * 40)
            print(f"Current player: ({'White' if self.current_player == self.white_player else 'Black'})")
            display.disp_board(self.board, self.graveyard, self.current_player)

            self.logger.log(f"board fen:\t{self.board.fen()}")
            if type(self.current_player) == HumanPlayer:
                #move = display.get_next_move_from_click(self.board, self.graveyard, self.current_player)
                #move = self.get_move_from_surface(self.board)
                move = False
                while move == False:
                    display.legal_moves = []
                    display.selected_square = False
                    display.path = []
                    move = display.get_move_from_surface_gui(self.board, self.Surface, self.gantry, self.graveyard, self.current_player)
                    
                
            else:
                move = self.current_player.get_move(self.board)

            if move:
                self.logger.log(f"attempted move:\t{move}")
                self.path_planner_board.place_from_fen(self.board.fen())
                if self.make_move(move):
                    display.legal_moves = []
                    display.selected_square = False
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
                            # Check for interrupt before each path segment
                            if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                                print("\nGame interrupted during gantry movement")
                                self.logger.log("Game interrupted during gantry movement")
                                self.lcd_manager.clear_game_interrupt()
                                self.gantry.electromagnet(False)  # Release piece
                                return False
                            
                            move_result = self.gantry.move(path[0][0]*path_const, path[0][1]*path_const, quick_speed)
                            if move_result == False:
                                # Movement was interrupted
                                self.gantry.electromagnet(False)
                                return False
                            
                            self.gantry.electromagnet(True)
                            time.sleep(0.3)

                            for point in path[:-1]:
                                move_result = self.gantry.move(point[0]*path_const, point[1]*path_const, slow_speed)
                                if move_result == False:
                                    self.gantry.electromagnet(False)
                                    return False
                                
                            move_result = self.gantry.move(path[len(path)-1][0]*path_const, path[len(path)-1][1]*path_const, slow_speed, drag_compensation=True)
                            if move_result == False:
                                self.gantry.electromagnet(False)
                                return False
                            
                            self.gantry.electromagnet(False)
                            time.sleep(0.1)
                            self.gantry.electromagnet(True)
                            time.sleep(0.3)
                            self.gantry.electromagnet(False)
                            time.sleep(0.1)
                        
                        #self.gantry.move(10, 10, 10)
                    else:
                        if self.is_capture:
                            if self.current_player == self.white_player:
                                self.gantry.move(36.75, 1.75, quick_speed)
                                while self.Surface.get_sensor_bitmap()[0][9] == 0:
                                    time.sleep(0.1)
                                print("Placing piece in graveyard")
                                self.gantry.electromagnet(True)
                                time.sleep(0.3)
                                self.gantry.move(36.75, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                self.gantry.move(self.graveyard.sq_to_gy_coord(self.next_graveyard)[0]*path_const, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                self.gantry.electromagnet(False)
                                time.sleep(0.1)
                            else:
                                self.gantry.move(5.25, 26.25, quick_speed)
                                while self.Surface.get_sensor_bitmap()[7][0] == 0:
                                    time.sleep(0.1)
                                print("Placing piece in graveyard")
                                self.gantry.electromagnet(True)
                                time.sleep(0.3)
                                self.gantry.move(5.25, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                self.gantry.move(self.graveyard.sq_to_gy_coord(self.next_graveyard)[0]*path_const, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                self.gantry.electromagnet(False)
                                time.sleep(0.1)
                    self.switch_player()
                else:
                    print("Invalid move.")
            else:
                print("No legal moves available.")
                break

        result = self.board.result()

        if result == "1-0":
            self.logger.log("Game over, result: White wins")
            display.board_message = "White wins!"
            print("White wins!")
        elif result == "0-1":
            self.logger.log("Game over, result: Black wins")
            display.board_message = "Black wins!"
            print("Black wins!")
        elif result == "1/2-1/2":
            self.logger.log("Game over, result: Draw")
            display.board_message = "Draw!"
            print("It's a draw!")
        
        display.disp_board(self.board, self.graveyard, self.current_player)
        for _ in range(3):
            self.gantry.chime()
            time.sleep(0.1)
        self.logger.end_log()
        self.gantry.cleanup()
        time.sleep(360)
        display.close_disp()
        return True

    def play_game_online(self, lichess_manager, game_id, player_colour) -> bool:
        """
        Play an online Lichess game with physical gantry control.
        Sends human moves to Lichess and receives opponent moves via stream.
        Executes opponent moves on the physical board using the gantry.
        Returns True if game completed normally, False if interrupted.
        """
        from models.player import LichessPlayer
        
        quick_speed = config['gantry']['quick_speed']
        slow_speed = config['gantry']['slow_speed']
        path_const = (3.5/5)
        
        if not self.white_player or not self.black_player:
            print("Players not set up. Please call setup_players() first.")
            return False
        self.gantry.center_pieces()
        print("Starting online chess game!")
        self.logger.log("Starting online chess game")
        
        display = Display(log=self.logger)
        
        try:
            while not self.is_game_over():
                # Check for game interrupt
                if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                    print("\nGame interrupted by user")
                    self.logger.log("Online game interrupted by user")
                    # display.close_disp()
                    self.lcd_manager.clear_game_interrupt()
                    return False
                    
                print("\n" + "-" * 40)
                print(f"Current player: ({'White' if self.current_player == self.white_player else 'Black'})")
                
                # Update display
                display.disp_board(self.board, self.graveyard, self.current_player)
                self.logger.log(f"board fen:\t{self.board.fen()}")
                
                # Get move from current player
                if isinstance(self.current_player, HumanPlayer):
                    # Human player - get move from physical board
                    move = False
                    while move == False:
                        display.legal_moves = []
                        display.selected_square = False
                        display.path = []
                        move = display.get_move_from_surface_gui(
                            self.board, 
                            self.Surface, 
                            self.gantry, 
                            self.graveyard, 
                            self.current_player
                        )
                else:
                    # Opponent move - get from Lichess stream
                    move = self.current_player.get_move(self.board)
                
                if move:
                    self.logger.log(f"attempted move:\t{move}")
                    self.path_planner_board.place_from_fen(self.board.fen())
                    
                    if self.make_move(move):
                        display.legal_moves = []
                        display.selected_square = False
                        
                        # Handle move execution on physical board
                        if isinstance(self.current_player, LichessPlayer):
                            # Opponent's move from Lichess - execute on gantry
                            path = self.path_planner_board.get_full_path_simpli(chess.Move.uci(move))
                            self.logger.log(f"Path:\t{path}")
                            
                            if path == False:
                                print("Failed to get path for opponent move")
                                break
                                
                            display.path = path
                            display.disp_board(self.board, self.graveyard, self.current_player)
                            print(path)
                            self.logger.log(f"path success")
                            
                            # Execute gantry movements
                            for path_segment in path:
                                # Check for interrupt before each path segment
                                if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                                    print("\nOnline game interrupted during gantry movement")
                                    self.logger.log("Online game interrupted during gantry movement")
                                    self.lcd_manager.clear_game_interrupt()
                                    self.gantry.electromagnet(False)  # Release piece
                                    return False
                                
                                move_result = self.gantry.move(path_segment[0][0]*path_const, path_segment[0][1]*path_const, quick_speed)
                                if move_result == False:
                                    self.gantry.electromagnet(False)
                                    return False
                                
                                self.gantry.electromagnet(True)
                                time.sleep(0.3)
                                
                                for point in path_segment[:-1]:
                                    move_result = self.gantry.move(point[0]*path_const, point[1]*path_const, slow_speed)
                                    if move_result == False:
                                        self.gantry.electromagnet(False)
                                        return False
                                
                                move_result = self.gantry.move(path_segment[len(path_segment)-1][0]*path_const, path_segment[len(path_segment)-1][1]*path_const, slow_speed, drag_compensation=True)
                                if move_result == False:
                                    self.gantry.electromagnet(False)
                                    return False
                                
                                self.gantry.electromagnet(False)
                                time.sleep(0.1)
                                self.gantry.electromagnet(True)
                                time.sleep(0.3)
                                self.gantry.electromagnet(False)
                                time.sleep(0.1)
                        
                        else:
                            # Human player's move - send to Lichess and handle graveyard if capture
                            success = lichess_manager.make_move(game_id, move)
                            if not success:
                                print("Failed to send move to Lichess. Game may desync.")
                            
                            if self.is_capture:
                                if self.current_player.colour == chess.WHITE:
                                    self.gantry.move(36.75, 1.75, quick_speed)
                                    while self.Surface.get_sensor_bitmap()[0][9] == 0:
                                        time.sleep(0.1)
                                    print("Placing piece in graveyard")
                                    self.gantry.electromagnet(True)
                                    time.sleep(0.3)
                                    self.gantry.move(36.75, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                    self.gantry.move(self.graveyard.sq_to_gy_coord(self.next_graveyard)[0]*path_const, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                    self.gantry.electromagnet(False)
                                    time.sleep(0.1)
                                else:
                                    self.gantry.move(5.25, 26.25, quick_speed)
                                    while self.Surface.get_sensor_bitmap()[7][0] == 0:
                                        time.sleep(0.1)
                                    print("Placing piece in graveyard")
                                    self.gantry.electromagnet(True)
                                    time.sleep(0.3)
                                    self.gantry.move(5.25, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                    self.gantry.move(self.graveyard.sq_to_gy_coord(self.next_graveyard)[0]*path_const, self.graveyard.sq_to_gy_coord(self.next_graveyard)[1]*path_const, slow_speed)
                                    self.gantry.electromagnet(False)
                                    time.sleep(0.1)
                        
                        self.switch_player()
                    else:
                        print("Invalid move.")
                else:
                    # Move is None - either game ended or error occurred
                    print("No move available or game ended.")
                    break
            
            # Game over
            print("\n" + "=" * 40)
            result = self.board.result()
            
            if result == "1-0":
                self.logger.log("Online game over, result: White wins")
                display.board_message = "White wins!"
                print("White wins!")
            elif result == "0-1":
                self.logger.log("Online game over, result: Black wins")
                display.board_message = "Black wins!"
                print("Black wins!")
            elif result == "1/2-1/2":
                self.logger.log("Online game over, result: Draw")
                display.board_message = "Draw!"
                print("It's a draw!")
            
            display.disp_board(self.board, self.graveyard, self.current_player)
            
            # Celebration chime
            for _ in range(3):
                self.gantry.chime()
                time.sleep(0.1)
            
            self.logger.end_log()
            time.sleep(5)
            display.close_disp()
            return True
            
        except Exception as e:
            print(f"Error in online game: {e}")
            self.logger.log(f"Error in online game: {e}")
            display.close_disp()
            raise

            
