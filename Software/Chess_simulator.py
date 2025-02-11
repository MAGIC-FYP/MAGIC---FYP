import pygame
import sys

# Constants for the display
WIDTH, HEIGHT = 800, 800  # Adjusted width since stats panel is removed
SQUARE_SIZE = WIDTH // 8  # Adjust square size for correct board rendering
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)
PIECE_IMAGES = {}
PIECE_SYMBOLS = {
    'r': 'R', 'n': 'N', 'b': 'B', 'q': 'Q', 'k': 'K', 'p': 'P'
}

# Initialize an empty board with custom piece layout
def initialize_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    return board

# Initialize Pygame and the chess board
def load_images():
    pygame.font.init()
    font = pygame.font.SysFont('arial', 64)
    piece_colors = {'w': (255, 255, 255), 'b': (0, 0, 0)}

    for color in ['w', 'b']:
        for symbol, display in PIECE_SYMBOLS.items():
            text_surface = font.render(display, True, piece_colors[color])
            piece_name = f"{color}{symbol}"
            image = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            image.fill((0, 0, 0, 0))  # Transparent background
            image.blit(text_surface, (SQUARE_SIZE // 4, SQUARE_SIZE // 4))  # Center text
            PIECE_IMAGES[piece_name] = image

def draw_board(screen, board):
    # Draw the chessboard
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
            piece = board[row][col]
            if piece:
                piece_image = PIECE_IMAGES[piece]
                screen.blit(piece_image, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def move_piece(board, start_pos, end_pos):
    start_row, start_col = start_pos
    end_row, end_col = end_pos
    piece = board[start_row][start_col]
    if piece:
        board[end_row][end_col] = piece  # Move the piece
        board[start_row][start_col] = None  # Clear the original position

def parse_position(pos):
    col = ord(pos[0].lower()) - ord('a')
    row = 8 - int(pos[1])
    return row, col

def process_single_move(board):
    try:
        user_input = input("Enter move (start end, e.g., 'a2 a4') or 'exit' to quit: ").strip().lower()
        if user_input == "exit":
            return False
        start, end = user_input.split()
        start_pos = parse_position(start)
        end_pos = parse_position(end)
        move_piece(board, start_pos, end_pos)
        return True
    except ValueError:
        print("Invalid input. Please enter a valid move in the format 'a2 a4'.")
        return True

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Emulator")
    clock = pygame.time.Clock()
    board = initialize_board()
    load_images()
    draw_board(screen, board)
    
    # Place initial pieces (example setup)
    board[0][0] = 'br'  # Black rook
    board[0][7] = 'br'  # Black rook
    board[7][0] = 'wr'  # White rook
    board[7][7] = 'wr'  # White rook
    board[1][0] = 'bp'  # Black pawn
    board[6][0] = 'wp'  # White pawn

    # If command-line arguments provided, process them
    if len(sys.argv) == 3:
        start_pos = parse_position(sys.argv[1])
        end_pos = parse_position(sys.argv[2])
        move_piece(board, start_pos, end_pos)

    running = True

    while running:
        screen.fill((0, 0, 0))  # Clear the screen
        draw_board(screen, board)
        pygame.display.flip()  # Update the display
        
        # Handle user input moves
        if not process_single_move(board):
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(60)  # Cap the frame rate

    pygame.quit()

if __name__ == "__main__":
    main()
