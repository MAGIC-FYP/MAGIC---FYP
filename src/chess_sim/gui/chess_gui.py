"""
This file contains all functions for chess GUI handling
"""
import os
import pygame
import sys
import chess
import math
import numpy as np
from models.graveyard import Graveyard
from gantry_control.tiles import TileSensor
from gantry_control.gantry import GantryControl
import algorithms.algorithms_expanding_aStar as a_star
import time
from algorithms.algorithms_expanding_aStar import find_path, screen_to_surface_coord, surface_to_screen_coord

# Initialize Pygame once
pygame.init()

colours = [(0, 0, 200), (0, 200, 0), (0, 200, 0)]

class Display:
    def __init__(self, board_size=600, log=False):
        """
        Initialize the display with a default screen size of 600.
        """
        self.board_size = board_size
        self.logger = log
        self.screen_size = (self.board_size+(self.board_size/2), self.board_size+(2*self.board_size/8))
        self.screen = pygame.display.set_mode(self.screen_size)
        self.selected_square = False
        self.message = ""
        self.path = []
        self.path_extra = []
        self.show_path = True
        self.legal_moves=[]
        self.show_mouse_coords = False
        self.output_state_button = pygame.Rect(self.screen_size[0] - 150, (self.screen_size[1]/8)/2 - 20, 140, 30)
        self.reset_button = pygame.Rect(10, (self.screen_size[1]/8)/2 - 20, 70, 30)
        self.mouse_loc_button = pygame.Rect(self.reset_button.right + 10, (self.screen_size[1]/8)/2 - 20, 100, 30)
        self.show_path_button = pygame.Rect(self.output_state_button.left - 90, (self.screen_size[1]/8)/2 - 20, 80, 30)
        self.graveyard_squares_white = [pygame.Rect(i * (self.board_size // 8), j * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8) for i in range(2) for j in range(8)]
        self.graveyard_squares_black = [pygame.Rect((self.board_size // 8) * (10 + i), j * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8) for i in range(2) for j in range(8)]
        self.graveyard_squares = self.graveyard_squares_white + self.graveyard_squares_black
        pygame.display.set_caption('Chess Simulator')

    def disp_board(self, board: chess.Board, graveyard: Graveyard, current_player):
        """
        Display the chess board.
        """
        # Clear the screen
        
        self.screen.fill((220, 220, 220))

        self._disp_graveyard(graveyard)
        self._disp_playing_board(board)
        self._top_text(current_player)
        self._disp_button(self.output_state_button, "Output Board State")
        self._disp_button(self.reset_button, "Reset")
        self._disp_button(self.mouse_loc_button, "Show Coords" if not self.show_mouse_coords else "Hide Coords")
        self._disp_button(self.show_path_button, "Show Path" if not self.show_path else "Hide Path")
        if self.show_path:
            self.display_path()
        
        # Update the display
        pygame.display.update()
        

    def _disp_button(self, button: pygame.Rect, button_label: str):
        """
        Displays a button on the screen with a given label.
        
        This method draws a button with a white background, a black border, and the specified label centered within the button.
        
        Parameters:
        - button: pygame.Rect - The rectangle representing the button's position and size.
        - button_label: str - The text to be displayed on the button.
        """
        pygame.draw.rect(self.screen, (220, 220, 220), button)
        pygame.draw.rect(self.screen, (0, 0, 0), button, 2)  # Black border
        font = pygame.font.Font(None, 16)
        text = font.render(button_label, True, (0, 0, 0))
        text_rect = text.get_rect(center=button.center)
        self.screen.blit(text, text_rect)

    def _top_text(self, current_player):
        """
        Displays the current player's turn at the top of the screen.
        
        This method renders the text indicating whose turn it is (White or Black) and displays it at the top center of the screen.
        
        Parameters:
        - current_player: chess.Player - The current player whose turn it is.
        """
        if self.show_mouse_coords:
            font = pygame.font.Font(None, 30)
            mouse_x, mouse_y = screen_to_surface_coord(pygame.mouse.get_pos(), self.screen_size)
            self.message = f"Mouse Coodinates: {mouse_x:.1f}, {mouse_y:.1f}"
        else:
            font = pygame.font.Font(None, 36)
            self.message = "White's Turn"
            if current_player.colour == chess.BLACK:
                self.message = "Black's Turn"
        text = font.render(f"{self.message}", True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.screen_size[0] // 2, (self.board_size/9)/2))
        self.screen.blit(text, text_rect)

    def display_path(self):
        """
        Displays the path of a move on the board.
        
        This method draws a line on the board to visualize the path of a move. It takes a list of tuples, each tuple representing the start and end coordinates of a line segment.
        
        Parameters:
        - path: List[Tuple[int, int]] - A list ofx tuples, each tuple containing the start and end coordinates of a line segment.
        """
        #self.path = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
        inc = 1
        moved_pieces_paths = self.path
        colour = 0
        for path in moved_pieces_paths:
            for i in range(len(path) - 1):
                a = surface_to_screen_coord((path[i][0], path[i][1]), self.screen_size)
                b = surface_to_screen_coord((path[i+1][0], path[i+1][1]), self.screen_size)
                self.draw_arrow(self.screen, colours[colour], a, b)  # Draw a blue line for the path
                font = pygame.font.Font(None, 25)
                text = font.render(str(inc), True, (255, 0,0))
                text_rect = text.get_rect(center=(((a[0] + b[0]*2) // 3)+10, ((a[1] + b[1]) // 2)+10))
                self.screen.blit(text, text_rect)
                inc = inc+1
            colour = colour + 1
                
        
        pygame.display.update()
        
    def draw_arrow(self, screen, color, start, end, width=3, arrow_size=10):
        """Draws a line with an arrowhead."""
    
        # Draw the main line
        pygame.draw.line(screen, color, start, end, width)

        # Calculate the direction of the arrow
        angle = math.atan2(end[1] - start[1], end[0] - start[0])  # Get angle of the line
        
        # Calculate arrowhead points
        arrow_points = [
            (end[0] - arrow_size * math.cos(angle - math.pi / 6),  # Left wing
            end[1] - arrow_size * math.sin(angle - math.pi / 6)),

            (end[0] - arrow_size * math.cos(angle + math.pi / 6),  # Right wing
            end[1] - arrow_size * math.sin(angle + math.pi / 6)),

            end  # Arrow tip
        ]

        # Draw the arrowhead as a polygon
        pygame.draw.polygon(screen, color, arrow_points)
        return

    def _disp_graveyard(self, graveyard: Graveyard):
        """
        helps display function draw graveyard
        """
        graveyard_positions = [(self.graveyard_squares_white, (255, 255, 255), graveyard.get_white_pieces_positions()),
                              (self.graveyard_squares_black, (0, 0, 0), graveyard.get_black_pieces_positions())]

        for squares, border_color, positions in graveyard_positions:
            for square in squares:
                pygame.draw.rect(self.screen, border_color, square, 3)  # Draw border
            
            for piece in positions:
                font = pygame.font.Font(None, 64)
                text_color = (255, 255, 255) if squares == self.graveyard_squares_white else (5, 5, 5)
                text = font.render(piece[1].symbol(), True, text_color)
                text_rect = text.get_rect(center=(piece[0][0] * (self.board_size // 8)-(self.board_size / 16), piece[0][1] * (self.board_size // 8)+(self.board_size / 16)))
                self.screen.blit(text, text_rect)

    def _disp_playing_board(self, board: chess.Board):
        """
        Displays the playing board with all pieces and highlights selected and legal moves.
        
        This method iterates through each square on the board, draws the square, checks if there's a piece on the square, and if so, draws the piece. It also highlights the square if it's the selected square or if it's a legal move.
        
        Parameters:
        - board: chess.Board - The current state of the chess board.
        """
        for row in range(8):
            for col in range(8):
                self._draw_square(row, col)
                piece = board.piece_at(chess.square(col, row))
                self._highlight_selected_square(col, row, board)
                self._highlight_legal_moves(col, row, board)
                self._highlight_previous_move(col, row, board)
                
                if piece:
                    self._draw_piece(piece, col, row)

    def _highlight_previous_move(self, col, row, board):
        """
        Highlights the square of the previous move with a yellow border.
        
        This method checks if there is a previous move in the move stack of the board. If there is, it gets the last move and checks if the from_square or to_square of the move matches the current square. If it does, it highlights the square with a yellow border.
        
        Parameters:
        - col: int - The column of the square.
        - row: int - The row of the square.
        - board: chess.Board - The current state of the chess board.
        """
        if board.move_stack:
            last_move = board.move_stack[-1]
            if last_move.from_square == col + row * 8 or last_move.to_square == col + row * 8:
                pygame.draw.rect(self.screen, (220, 220, 0), ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8), 5)  # Highlight the square with a yellow border

    def _display_rank_file(self, col, row):
        """
        Displays the rank and file of each square to the right of the square.
        
        This method displays the rank and file of each square to the right of the square.
        
        Parameters:
        - col: int - The column of the square.
        - row: int - The row of the square.
        """
        topness = 20
        font = pygame.font.Font(None, 15)
        text = font.render(f"{chr(97 + col)}{row + 1}", True, (0, 0, 0))
        text_rect = text.get_rect(center=((col + 2) * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // topness), row * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // 8) - (self.board_size // topness)))
        self.screen.blit(text, text_rect)

    def _get_square_color(self, row, col):
        """
        Returns the color of a square based on its position.
        
        This method determines the color of a square on the board based on its row and column. It alternates between two colors for each row and column to create a checkered pattern.
        
        Parameters:
        - row: int - The row of the square.
        - col: int - The column of the square.
        
        Returns:
        - tuple - A tuple representing the RGB color of the square.
        """
        return (119, 149, 86) if (row + col) % 2 == 0 else (235, 236, 208)

    def _draw_square(self, row, col):
        """
        Draws a square on the board.
        
        This method draws a square on the board based on its row and column. It uses the color determined by _get_square_color.
        
        Parameters:
        - row: int - The row of the square.
        - col: int - The column of the square.
        """
        square_color = self._get_square_color(row, col)
        pygame.draw.rect(self.screen, square_color, ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
        self._display_rank_file(col, row)

    def _draw_piece(self, piece, col, row):
        """
        Draws a piece on the board.
        
        This method draws a piece on the board based on its position and color. It uses a font to render the piece symbol and places it in the center of the square.
        
        Parameters:
        - piece: chess.Piece - The piece to be drawn.
        - col: int - The column of the piece.
        - row: int - The row of the piece.
        """
        font = pygame.font.Font(None, 64)
        if piece.color == chess.WHITE:
            text = font.render(piece.symbol(), True, (255, 255, 255))
        else:
            text = font.render(piece.symbol(), True, (5, 5, 5))
        text_rect = text.get_rect(center=((col + 2) * (self.board_size // 8) + (self.board_size // 16), row * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // 8)))
        self.screen.blit(text, text_rect)

    def _highlight_selected_square(self, col, row, board: chess.Board):
        """
        Highlights the selected square on the board.
        
        This method checks if the current square is the selected square and if the piece on the square is of the current player's color. If so, it highlights the square.
        
        Parameters:
        - col: int - The column of the square.
        - row: int - The row of the square.
        - board: chess.Board - The current state of the chess board.
        """
        piece = board.piece_at(chess.square(col, row))
        if piece and piece.color == board.turn:
            if self.selected_square != False and self.selected_square == chess.square(col, row):
                pygame.draw.rect(self.screen, (195, 195, 0), ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))

    def _highlight_legal_moves(self, col, row, board: chess.Board):
        """
        Highlights legal moves on the board.
        
        This method checks if the current square is a legal move for the current player. If so, it highlights the square or draws a circle on it if it's an empty square.
        
        Parameters:
        - col: int - The column of the square.
        - row: int - The row of the square.
        - board: chess.Board - The current state of the chess board.
        """
        if self.legal_moves and chess.square(col, row) in self.legal_moves:
            piece = board.piece_at(chess.square(col, row))
            if piece:
                gray = 80
                colour = (119-gray, 149-gray, 86-gray) if (row + col) % 2 == 0 else (235-gray, 236-gray, 208-gray)
                pygame.draw.rect(self.screen, colour, ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
            else:
                gray = 60
                colour = (119-gray, 149-gray, 86-gray) if (row + col) % 2 == 0 else (235-gray, 236-gray, 208-gray)
                pygame.draw.circle(self.screen, colour, ((col + 2) * (self.board_size // 8) + (self.board_size // 16), row * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // 8)), self.board_size // 40)
                    
    def handle_events(self):
        """
        Handle the events in the game.
        Ensures the window closes even if an error occurs during event processing.
        """
        try:
            for event in pygame.event.get():
                
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        except Exception as e:
            print(f"An unexpected error occurred during event handling: {e}")
            # Ensure Pygame resources are released and the application exits
            pygame.quit()
            sys.exit(1) # Exit with an error code to indicate abnormal termination
        return True  # Return True to keep the game running
    
    def handle_mouse_click(self, board: chess.Board, graveyard: Graveyard, current_player):
        """
        Handle the mouse click events.
        """
        while True:
            self.disp_board(board, graveyard, current_player)  # Display the board before handling events
            self.handle_events()  # Handle any events before checking for mouse clicks
            event = pygame.event.wait()  # Wait for an event 
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # Adjust for squares moved over 2 squares to the right
                adjusted_mouse_x = mouse_x - (self.board_size // 4)
                # Check if the click is within the board boundaries
                if 0 <= adjusted_mouse_x <= self.board_size and self.board_size / 9 <= mouse_y <= self.board_size + self.board_size / 9:
                    # Convert mouse position to board coordinates
                    board_x = adjusted_mouse_x // (self.board_size // 8)
                    board_y = (mouse_y - (self.board_size // 8)) // (self.board_size // 8)
                    return board_y * 8 + board_x  # Return the board coordinates of the mouse click as a single number 0-63
                elif self.output_state_button.collidepoint(mouse_x, mouse_y):
                    # Output board state functionality
                    print(f"Board State: {board.fen()}")

                elif self.reset_button.collidepoint(mouse_x, mouse_y):
                    # Reset board functionality
                    self.selected_square = False
                    self.legal_moves = []
                    self.path = {"moved_pieces_paths": [], "path": [], "undo_moves": []}
                    board.reset()
                    graveyard.reset()
                    if self.logger:
                        self.logger.log("Reset Board")
                        self.logger.log(f"New fen: {board.fen()}")

                elif self.mouse_loc_button.collidepoint(mouse_x, mouse_y):
                    self.show_mouse_coords = not self.show_mouse_coords

                elif self.show_path_button.collidepoint(mouse_x, mouse_y):
                    self.show_path = not self.show_path
                
                self.disp_board(board, graveyard, current_player)

    def get_move_from_surface_gui(self, board: chess.Board, Surface: TileSensor, gantry: GantryControl, graveyard: Graveyard ,current_player):
        try:
            path_const = (3.5/5)
            prev_bitmap = np.zeros((8, 8))
            for rank_idx in range(8): # Iterate through ranks (rows) from 0 to 7
                for file_idx in range(8): # Iterate through files (columns) from 0 to 7                
                    square_index = rank_idx * 8 + file_idx
                    if board.piece_at(square_index):
                        prev_bitmap[rank_idx, file_idx] = 1 # Piece is present


            change = 0
            from_square = None
            while change == 0:
                cur_bitmap = np.array(Surface.get_sensor_bitmap())[:, 1:9]
                dif_bitmap = np.zeros((8, 8))
                for i in range(8):
                    for j in range(8):
                        if cur_bitmap[i][j] != prev_bitmap[i][j]:
                            dif_bitmap[i, j] = 1

                            from_square = chess.square(j, i)
                change = np.sum(dif_bitmap) 
                if from_square:
                    if board.piece_at(from_square):
                    # i = board.piece_at(from_square)
                    # j = current_player.colour
                        if board.piece_at(from_square).color != current_player.colour:

                            change = 0
                            to_square = from_square
                            while change == 0:
                                cur_bitmap = np.array(Surface.get_sensor_bitmap())[:, 1:9]
                                dif_bitmap = np.zeros((8, 8))
                                for i in range(8):
                                    for j in range(8):
                                        if cur_bitmap[i][j] - prev_bitmap[i][j] == -1:
                                            dif_bitmap[i, j] = 1

                                            from_square = chess.square(j, i)
                                change = np.sum(dif_bitmap) 
                            move = chess.Move(from_square, to_square)
                            print(f"move human takes: {move}")
                            return move
                            
            piece = board.piece_at(from_square)
            if piece:       
                self.selected_square = from_square
                if piece.color == current_player.colour:
                    self.legal_moves = [move.to_square for move in board.legal_moves if move.from_square == from_square]
                    self.disp_board(board, graveyard, current_player)
            prev_bitmap = cur_bitmap

            timer = 0
            change = 0
            prev_to_square = None
            to_square = None
            while timer < 4:

                while change == 0:
                    cur_bitmap = Surface.get_sensor_bitmap()
                    dif_bitmap = np.zeros((8, 8))
                    for i in range(8):
                        for j in range(8):
                            if cur_bitmap[i][j+1] != prev_bitmap[i][j]:
                                dif_bitmap[i, j] = 1
                                to_square = chess.square(j, i)
                    if to_square in self.legal_moves:
                        change = int(np.sum(dif_bitmap))
                    else: 
                        time.sleep(0.5)
                        gantry.chime()
                        time.sleep(0.5)
                        prev_to_square = to_square
                        while change == 0:
                            cur_bitmap = Surface.get_sensor_bitmap()
                            dif_bitmap = np.zeros((8, 8))
                            for i in range(8):
                                for j in range(8):
                                    if cur_bitmap[i][j+1] != prev_bitmap[i][j]:
                                        dif_bitmap[i, j] = 1
                                        to_square = chess.square(j, i)
                            change = int(np.sum(dif_bitmap))
                        if  to_square == prev_to_square:
                            print("illegal move")
                            
                            # path = a_star.crowd_control(board, chess.Move(to_square, from_square), graveyard, 2)
                            # if path == False:
                            #     gantry.chime()
                            #     return False
                            
                            # if path["moved_pieces_paths"]:
                            #     gantry.move(path["moved_pieces_paths"][0][0][0]*path_const, path["moved_pieces_paths"][0][0][1]*path_const, 30)
                            #     for point in path["moved_pieces_paths"][0][1:]:
                            #         gantry.move(point[0]*path_const, point[1]*path_const, 4)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(True)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.4)

                            # if path["path"]:
                            #     gantry.move(path["path"][0][0][0]*path_const, path["path"][0][0][1]*path_const, 30)
                            #     for point in path["path"][0][1:]:
                            #         gantry.move(point[0]*path_const, point[1]*path_const, 4)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(True)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.4)

                            # if path["undo_moves"]:
                            #     gantry.move(path["undo_moves"][0][0][0]*path_const, path["undo_moves"][0][0][1]*path_const, 30)
                            #     for point in path["undo_moves"][0][1:]:
                            #         gantry.move(point[0]*path_const, point[1]*path_const, 4)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(True)
                            #     time.sleep(0.3)
                            #     gantry.electromagnet(False)
                            #     time.sleep(0.4)
                            
                            # gantry.move(17.5, 14, 10)

                            # return False

                        
                if  to_square == prev_to_square:
                    prev_to_square = to_square
                    
                    timer = timer + 1
                    change = 0
                else:
                    timer = 0
                    prev_to_square = to_square
                    print("timer reset")
                    change = 0
                

            
                

            move = chess.Move(from_square, to_square)
            print(f"move: {move}")

            return move  
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            board.cleanup(1)
                    
    def get_next_move_from_click(self, board: chess.Board, graveyard: Graveyard, current_player):
        """
        This method handles the mouse click events and returns the next move.
        It first waits for a click on a piece, then highlights the legal moves for that piece.
        After that, it waits for a click on the target square and returns the move.
        """
        while True:
            position = self.handle_mouse_click(board, graveyard, current_player)
            piece = board.piece_at(position)
            if piece:
                self.selected_square = position
                if piece.color == current_player.colour:
                    self.legal_moves = [move.to_square for move in board.legal_moves if move.from_square == position]
                    self.disp_board(board, graveyard, current_player)
                    target = self.handle_mouse_click(board, graveyard, current_player)
                    self.selected_square = False
                    self.legal_moves = []

                    promotion = None
                    if piece.piece_type == chess.PAWN and (
                        (piece.color == chess.WHITE and target > 55) or 
                        (piece.color == chess.BLACK and target < 8)
                    ):
                        # Display a little box on the GUI with a piece to promote
                        promotion = self.display_promotion_box(current_player, piece, target)
                        promotion = chess.Piece.from_symbol(promotion).piece_type # Can directly link the buttons to be chess.QUEEN etc
                    move = chess.Move(from_square=position, to_square=target, promotion = promotion)
                    return(move)
    
    def display_promotion_box(self, current_player, piece: chess.Piece, to_square):
        """
        This method displays a box with the options for promotion and returns the selected piece.
        Ensures the window closes even if an error occurs during event processing within the promotion box.
        """
        promotion_options = ['Q', 'R', 'B', 'N']  # Changed 'K' to 'N' as Knight is valid promotion option
        box_width = 50 * len(promotion_options)  # Make the box long, not tall
        box_height = 50 
        
        # Center the box on screen
        to_square_rect = pygame.Rect(
            (to_square % 8 + 2) * (self.board_size // 8),
            (to_square // 8) * (self.board_size // 8),
            self.board_size // 8,
            self.board_size // 8
        )
        promotion_box = pygame.Rect(
            to_square_rect.centerx - box_width // 2,
            to_square_rect.centery - box_height // 2,
            box_width,
            box_height
        )

        #removing old piece and showing pawn
        gray = 80
        colour = (119-gray, 149-gray, 86-gray) if (to_square // 8 + to_square % 8) % 2 == 0 else (235-gray, 236-gray, 208-gray)
        pygame.draw.rect(self.screen, colour, ((to_square % 8 + 2) * (self.board_size // 8), to_square // 8 * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
        self._draw_piece(piece, to_square % 8, to_square // 8)

        while True:
            # Draw the box
            pygame.draw.rect(self.screen, (220, 220, 220), promotion_box)
            pygame.draw.rect(self.screen, (0, 0, 0), promotion_box, 2)  # Add border
            
            # Draw the piece options
            font = pygame.font.Font(None, 64)
            for i, piece_symbol in enumerate(promotion_options): # Renamed 'piece' to 'piece_symbol' to avoid conflict
                piece_color = (255, 255, 255) if current_player.colour == chess.WHITE else (5, 5, 5)
                text = font.render(piece_symbol, True, piece_color)
                text_rect = text.get_rect(center=(
                    promotion_box.left + (i + 0.5) * box_width // len(promotion_options),
                    promotion_box.centery
                ))
                self.screen.blit(text, text_rect)
            
            # Draw a small triangle pointing at the target square
            triangle_points = [
                (promotion_box.centerx-20, promotion_box.bottom),
                (to_square_rect.centerx, to_square_rect.bottom),
                (promotion_box.centerx+20, promotion_box.bottom)  # Adjust the height of the triangle
            ]
            pygame.draw.polygon(self.screen, (0, 0, 0), triangle_points)
            
            pygame.display.update()
            
            # Handle events
            try:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        if promotion_box.collidepoint(mouse_pos):
                            # Calculate which piece was clicked
                            relative_x = mouse_pos[0] - promotion_box.left
                            piece_index = int(relative_x // (box_width // len(promotion_options)))
                            if 0 <= piece_index < len(promotion_options):
                                return promotion_options[piece_index]
                    
                    elif event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
            except Exception as e:
                print(f"An unexpected error occurred during promotion box event handling: {e}")
                pygame.quit()
                sys.exit(1) # Exit with an error code to indicate abnormal termination
            
            time.sleep(0.01)  # Prevent high CPU usage
        
    def close_disp(self):
        pygame.quit()
        sys.exit()
