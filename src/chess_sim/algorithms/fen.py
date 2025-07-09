import random

MOVES = {
    'K': [(0, -1, 1), (1, -1, 1), (1, 0, 1), (1, 1, 1),
          (0, 1, 1), (-1, 1, 1), (-1, 0, 1), (-1, -1, 1)],
    'Q': [(0, -1, 7), (1, -1, 7), (1, 0, 7), (1, 1, 7),
          (0, 1, 7), (-1, 1, 7), (-1, 0, 7), (-1, -1, 7)],
    'R': [(0, -1, 7), (1, 0, 7), (0, 1, 7), (-1, 0, 7)],
    'B': [(1, -1, 7), (1, 1, 7), (-1, 1, 7), (-1, -1, 7)],
    'N': [(1, -2, 1), (2, -1, 1), (2, 1, 1), (1, 2, 1),
          (-1, 2, 1), (-2, 1, 1), (-2, -1, 1), (-1, -2, 1)],
    'P': [(-1, -1, 1), (1, -1, 1)], 
    'p': [(-1, 1, 1), (1, 1, 1)]   
}

piece_config = {
    'Q': 1, 'q': 1,
    'R': 2, 'r': 2,
    'B': 2, 'b': 2,
    'N': 2, 'n': 2,
    'P': 8, 'p':8
}

MOVES['k'] = MOVES['K']
MOVES['q'] = MOVES['Q']
MOVES['r'] = MOVES['R']
MOVES['b'] = MOVES['B']
MOVES['n'] = MOVES['N']

def _get_empty_square(board):
    while True:
        x = random.randint(0, 7)
        y = random.randint(0, 7)
        if board[y][x] == '':
            return x, y

def _is_valid_position(board, x, y, piece, white_bishop_color, black_bishop_color):
    if piece == 'P' and y == 0: return False
    if piece == 'P' and y == 7: return False
    if piece == 'p' and y == 0: return False
    if piece == 'p' and y == 7: return False

    op_king = 'k' if piece.isupper() else 'K'

    if piece in MOVES:
        for dx, dy, max_range in MOVES[piece]:
            for step in range(1, max_range + 1):
                px, py = x + step * dx, y + step * dy
                if 0 <= px < 8 and 0 <= py < 8:
                    target_piece = board[py][px]
                    if target_piece == op_king:
                        return False
                    if target_piece != '':
                        break
                else:
                    break

    square_color = 'w' if (x + y) % 2 == 0 else 'b'

    if piece == 'B':
        if white_bishop_color is not None and white_bishop_color == square_color:
            return False
    elif piece == 'b':
         if black_bishop_color is not None and black_bishop_color == square_color:
            return False

    return True

def _board_to_fen(board):
    fen = ''
    for y in range(8):
        empty_count = 0
        for x in range(8):
            piece = board[y][x]
            if piece == '':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen += str(empty_count)
                    empty_count = 0
                fen += piece
        if empty_count > 0:
            fen += str(empty_count)
        if y < 7:
            fen += '/'
    fen += ' w - - 0 1'
    return fen

def generate_random_fen(piece_counts = piece_config, total_pieces=None):
    board = [['' for _ in range(8)] for _ in range(8)]

    piece_pool = []
    for piece, count in piece_counts.items():
        if piece in 'PNBRQpnbrq' and isinstance(count, int) and count > 0:
            piece_pool.extend([piece] * count)
        elif piece in 'Kk':
             print(f"Warning: Kings ('K', 'k') are added automatically and should not be in piece_counts. Ignoring '{piece}'.")

    max_possible_pieces = len(piece_pool) + 2

    if total_pieces is None:
        num_pieces_to_place = max_possible_pieces
    else:
        if not isinstance(total_pieces, int) or total_pieces < 2:
            print("Error: total_pieces must be an integer >= 2.")
            return None
        num_pieces_to_place = min(total_pieces, max_possible_pieces)
        if total_pieces > max_possible_pieces:
             print(f"Warning: Requested total_pieces ({total_pieces}) is more than available pieces ({max_possible_pieces}). Placing {max_possible_pieces} pieces.")

    bk_x, bk_y = _get_empty_square(board)
    board[bk_y][bk_x] = 'k'

    while True:
        wk_x, wk_y = _get_empty_square(board)
        if abs(wk_x - bk_x) > 1 or abs(wk_y - bk_y) > 1:
            board[wk_y][wk_x] = 'K'
            break

    random.shuffle(piece_pool)
    pieces_placed_count = 2
    white_bishop_square_color = None
    black_bishop_square_color = None

    pieces_to_select_from = piece_pool[:num_pieces_to_place - 2]

    for piece in pieces_to_select_from:
        attempts = 0
        max_attempts = 200

        while attempts < max_attempts:
            x, y = _get_empty_square(board)

            temp_wbc = white_bishop_square_color
            temp_bbc = black_bishop_square_color

            if _is_valid_position(board, x, y, piece, temp_wbc, temp_bbc):
                board[y][x] = piece
                pieces_placed_count += 1

                square_color = 'w' if (x + y) % 2 == 0 else 'b'
                if piece == 'B' and white_bishop_square_color is None:
                    white_bishop_square_color = square_color
                elif piece == 'b' and black_bishop_square_color is None:
                    black_bishop_square_color = square_color

                break
            attempts += 1
        else:
            print(f"Warning: Could not find a valid position for piece '{piece}' after {max_attempts} attempts. Skipping.")

    return _board_to_fen(board)




