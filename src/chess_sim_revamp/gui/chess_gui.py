"""
This file contains all functions for chess GUI handling
"""

import pygame
import sys
import chess

# Initialize Pygame once
pygame.init()

class Display:
    def __init__(self, board_size=600):
        """
        Initialize the display with a default screen size of 600.
        """
        self.board_size = board_size
        self.screen_size = (self.board_size+(self.board_size/2), self.board_size+(self.board_size/8))
        self.screen = pygame.display.set_mode(self.screen_size)
        self.selected_square = False
        self.message = ""
        self.legal_moves=[]
        self.output_button = pygame.Rect(self.screen_size[0] - 150, (self.screen_size[1]/8)/2 - 20, 140, 30)
        self.graveyard_squares_white = [pygame.Rect(i * (self.board_size // 8), j * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8) for i in range(2) for j in range(8)]
        self.graveyard_squares_black = [pygame.Rect((self.board_size // 8) * (10 + i), j * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8) for i in range(2) for j in range(8)]
        self.graveyard_squares = self.graveyard_squares_white + self.graveyard_squares_black
        pygame.display.set_caption('Chess Simulator')

    def disp_board(self, board, current_player):
        """
        Display the chess board.
        """
        # Clear the screen
        self.screen.fill((220, 220, 220))

        # Draw graveyard squares
        for square in self.graveyard_squares_white:
            pygame.draw.rect(self.screen, (255, 255, 255), square, 3)  # White border
        for square in self.graveyard_squares_black:
            pygame.draw.rect(self.screen, (0, 0, 0), square, 3)  # Black border

        # Draw the board
        for row in range(8):
            for col in range(8):
                colour = (119, 149, 86) if (row + col) % 2 == 0 else (235, 236, 208)
                pygame.draw.rect(self.screen, colour, ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
                piece = board.piece_at(chess.square(col, row))
                if piece and piece.color == board.turn:
                    # Highlight selected position square yellow if selected_square is not empty
                    
                    if self.selected_square != False and self.selected_square == chess.square(col, row):
                        
                        pygame.draw.rect(self.screen, (195, 195, 0), ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
                
                # Highlights squares of legal moves

                if self.legal_moves and chess.square(col, row) in self.legal_moves:
                    if piece:
                        gray = 80
                        colour = (119-gray, 149-gray, 86-gray) if (row + col) % 2 == 0 else (235-gray, 236-gray, 208-gray)
                        pygame.draw.rect(self.screen, colour, ((col + 2) * (self.board_size // 8), row * (self.board_size // 8) + (self.board_size // 8), self.board_size // 8, self.board_size // 8))
                    else:
                        gray = 60
                        colour = (119-gray, 149-gray, 86-gray) if (row + col) % 2 == 0 else (235-gray, 236-gray, 208-gray)
                        pygame.draw.circle(self.screen, colour, ((col + 2) * (self.board_size // 8) + (self.board_size // 16), row * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // 8)), self.board_size // 40)
                        
                if piece:
                    font = pygame.font.Font(None, 64)
                    if piece.color == chess.WHITE:
                        text = font.render(piece.symbol(), True, (255, 255, 255))
                    else:
                        text = font.render(piece.symbol(), True, (5, 5, 5))
                    text_rect = text.get_rect(center=((col + 2) * (self.board_size // 8) + (self.board_size // 16), row * (self.board_size // 8) + (self.board_size // 16) + (self.board_size // 8)))
                    self.screen.blit(text, text_rect)

        # Add text at top
        font = pygame.font.Font(None, 36)
        self.message = "White's Turn"
        if current_player.colour == chess.BLACK:
            self.message = "Black's Turn"
        text = font.render(f"{self.message}", True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.screen_size[0] // 2, (self.board_size/9)/2))
        self.screen.blit(text, text_rect)

        # Output board state button
        pygame.draw.rect(self.screen, (220, 220, 220), self.output_button)
        pygame.draw.rect(self.screen, (0, 0, 0), self.output_button, 2)  # Black border
        font = pygame.font.Font(None, 16)
        text = font.render("Output Board State", True, (0, 0, 0))
        text_rect = text.get_rect(center=self.output_button.center)
        self.screen.blit(text, text_rect)

        
        # Update the display
        pygame.display.update()  # Update the display after drawing the board

    def handle_events(self, board):
        """
        Handle the events in the game.
        """
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return True  # Return True to keep the game running
    
    def handle_mouse_click(self, board):
        """
        Handle the mouse click events.
        """
        while True:
            
            self.handle_events(board) # Handle any events before checking for mouse clicks
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
                elif self.output_button.collidepoint(mouse_x, mouse_y):
                    # Output board state functionality
                    print(f"Board State: {board.fen()}")
                    
                
    def get_next_move_from_click(self, board, current_player):
        """
        This method handles the mouse click events and returns the next move.
        It first waits for a click on a piece, then highlights the legal moves for that piece.
        After that, it waits for a click on the target square and returns the move.
        """
        while True:
            position = self.handle_mouse_click(board)
            piece = board.piece_at(position)
            if piece:
                self.selected_square = position
                if piece.color == current_player.colour:
                    self.legal_moves = [move.to_square for move in board.legal_moves if move.from_square == position]
                    self.disp_board(board,current_player)
                    target = self.handle_mouse_click(board)
                    self.selected_square = False
                    self.legal_moves = []
                    move = chess.Move(from_square=position, to_square=target)
                    return(move)
    
   
