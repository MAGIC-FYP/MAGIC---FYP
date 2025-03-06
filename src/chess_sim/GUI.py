"""
This file contains all functions for chess GUI handling
"""

import pygame
import sys

# Initialize Pygame once
pygame.init()

class Display:
    def __init__(self, screen_size=600):
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size+(self.screen_size/8)))
        self.selected_square = False
        pygame.display.set_caption('Chess Simulator')

    def disp_board(self, board):
        # Clear the screen
        self.screen.fill((255, 255, 255))

        # Draw the board
        for row in range(8):
            for col in range(8):
                color = (105, 105, 105) if (row + col) % 2 == 0 else (255, 255, 255)
                pygame.draw.rect(self.screen, color, (col * (self.screen_size // 8), row * (self.screen_size // 8) + (self.screen_size // 8), self.screen_size // 8, self.screen_size // 8))

                # Highlight selected position square yellow if selected_square is not empty
                if self.selected_square != False and self.selected_square == (row, col):
                    pygame.draw.rect(self.screen, (185, 185, 0), (col * (self.screen_size // 8), row * (self.screen_size // 8) + (self.screen_size // 8), self.screen_size // 8, self.screen_size // 8))

                # Draw pieces
                piece = board.state[row][col]
                if piece:
                    font = pygame.font.Font(None, 64)
                    text = font.render(piece.get_symbol(), True, (0, 0, 0))
                    text_rect = text.get_rect(center=(col * (self.screen_size // 8) + (self.screen_size // 16), row * (self.screen_size // 8) + (self.screen_size // 16) + (self.screen_size // 8)))
                    self.screen.blit(text, text_rect)

        # Add text that says "Click piece or target"
        font = pygame.font.Font(None, 36)
        str = "Target"
        if self.selected_square == False:
            str = "Piece"
        text = font.render(f"Select {str}", True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.screen_size // 2, (self.screen_size/9)/2))
        self.screen.blit(text, text_rect)

        # Update the display
        pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return True  # Return True to keep the game running
    
    def handle_mouse_click(self):
        while True:
            event = pygame.event.wait()  # Wait for an event
            self.handle_events()  # Handle any events before checking for mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # Convert mouse position to board coordinates
                board_x = mouse_x // (self.screen_size // 8)
                board_y = (mouse_y - (self.screen_size // 8)) // (self.screen_size // 8)
                return (board_y, board_x)

    def get_next_move_from_click(self, board):
        postion = self.handle_mouse_click()
        self.selected_square = postion
        self.disp_board(board)
        target = self.handle_mouse_click()
        self.selected_square = False
        return(postion, target)