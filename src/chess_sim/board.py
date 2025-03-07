from typing import Optional, List, Union
from pieces import King, Pawn, Knight, Bishop, Rook, Queen, Piece

class Board:
    def __init__(self, extended: bool = False, state: Optional[List[List[Optional[Piece]]]] = None):
        self.state = state
        if self.state is None:

            self.K = King('w')
            self.Q = Queen('w')
            self.R = Rook('w')
            self.R2 = Rook('w')
            self.B = Bishop('w')
            self.B2 = Bishop('w')
            self.N = Knight('w')
            self.N2 = Knight('w')
            self.k = King('b')
            self.q = Queen('b')
            self.r = Rook('b')
            self.r2 = Rook('b')
            self.b = Bishop('b')
            self.b2 = Bishop('b')
            self.n = Knight('b')
            self.n2 = Knight('b')
            self.white_pawns = [Pawn('w') for _ in range(8)]
            self.black_pawns = [Pawn('b') for _ in range(8)]
            self.turn = 'w'
            self.w_king_pos = (0,4)
            self.b_king_pos = (7,4)

            if extended:
                self.state = [[None for _ in range(12)] for _ in range(8)]
                self.state[0] = [None, None, self.R, self.N, self.B, self.Q, self.K, self.B2, self.N2, self.R2, None, None]
                self.state[1] = [None, None] + self.white_pawns + [None, None]
                self.state[6] = [None, None] + self.black_pawns + [None, None]
                self.state[7] = [None, None, self.r, self.n, self.b, self.q, self.k, self.b2, self.n2, self.r2, None, None]
            else:
                self.state = [[None for _ in range(8)] for _ in range(8)]
                self.state[0] = [self.R, self.N, self.B, self.Q, self.K, self.B, self.N, self.R]
                self.state[1] = self.white_pawns
                self.state[6] = self.black_pawns
                self.state[7] = [self.r, self.n, self.b, self.q, self.k, self.b, self.n, self.r]

    def print_ascii(self):
        print("\n")
        for row in self.state:
            # Convert None to '-' and join elements with spaces
            row_str = ' '.join('-' if piece is None else str(piece.get_symbol()) for piece in row)
            print(row_str)
    
    def print_url(self):
        """
        prints url or board like same as from chess.com e.g. "RNBQKBNR/-PPPP-PP/P-------/--------/----pP--/--------/pppp-ppp/rnbqkbnr/"
        """
        for row in self.state:
            # Convert None to '-' and join elements with spaces
            row_str = ''.join('-' if piece is None else str(piece.get_symbol()) for piece in row)
            print(row_str, end="/")
        print("\n")

    def load_from_url(self, ascii_string: str):
        """
        loads state into board from url "RNBQKBNR/-PPPP-PP/P-------/--------/----pP--/--------/pppp-ppp/rnbqkbnr/"
        """
        # Clear the current state
        self.state = [[None for _ in range(8)] for _ in range(8)]  # Fixed to 8x8 board
        
        ascii_rows = ascii_string.split("/")  # Split the input string into rows
        for i, row in enumerate(ascii_rows):
            row = list(row)
            j = 0  # Initialize column index
            for j in range(len(row)):
                if row[j].isdigit():
                    j += 1  # Skip empty squares
                elif row[j] != '-':
                    self.state[i][j] = self.get_piece_from_symbol(row[j])  # Corrected indexing
                    if self.state[i][j].symbol == 'K':
                        if self.state[i][j].colour == 'w':
                            self.w_king_pos = (i,j)
                        else:
                            self.b_king_pos = (i,j)
                    j += 1  # Move to the next column

    def get_all_legal_moves(self, position: tuple):
        """
        This method calculates all the legal moves for a given position on the board.
        It iterates over all the squares on the board and checks if the move is legal.
        If it is, it adds the square to the list of legal moves.
        """
        legal_moves = []
        # Ensure position is a tuple
        if isinstance(position, tuple) and len(position) == 2:
            for row in range(8):
                for col in range(8):
                    if self.move(position, (row, col), check_move=True):
                        legal_moves.append((row, col))
        return legal_moves
    
    def get_piece_from_symbol(self, symbol: str) -> Optional[Piece]:
        # Map symbols to piece classes
        piece_map = {
            'K': King('w'),  # White King
            'k': King('b'),  # Black King
            'Q': Queen('w'),  # White Queen
            'q': Queen('b'),  # Black Queen
            'R': Rook('w'),  # White Rook
            'r': Rook('b'),  # Black Rook
            'B': Bishop('w'),  # White Bishop
            'b': Bishop('b'),  # Black Bishop
            'N': Knight('w'),  # White Knight
            'n': Knight('b'),  # Black Knight
            'P': Pawn('w'),  # White Pawn
            'p': Pawn('b')   # Black Pawn
        }
        return piece_map.get(symbol, None)  # Return None if symbol is not found

    def move(self, position: tuple, target: tuple, legal_required: bool = True, check_move: bool = False):
        if legal_required:
            # Get the piece at the starting position
            piece = self.state[position[0]][position[1]]
            # Check if there's actually a piece at the starting position
            if piece is None:
                return False
            # Use the piece's is_legal method
            
            legal = piece.is_legal(position, target, self.state)
            if not legal:
                if check_move == False:
                    print("\n Non-legal move")
                return False
        
        if check_move == False:
            if self.turn == piece.colour:
                
                # Handels castling
                if piece.symbol in ['K'] and piece.castle_rook:
                    direction = 1 if target[1] > position[1] else -1
                    self.state[target[0]][target[1]] = self.state[position[0]][position[1]]
                    self.state[position[0]][position[1]] = None
                    self.state[position[0]][position[1]+direction] = self.state[piece.castle_rook[0]][piece.castle_rook[1]]
                    self.state[piece.castle_rook[0]][piece.castle_rook[1]] = None
                
                # Handels all other cases
                else:
                    self.state[target[0]][target[1]] = self.state[position[0]][position[1]]
                    self.state[position[0]][position[1]] = None

                if piece.symbol == 'K':
                    piece.has_moved = True

                if piece.symbol == 'R':
                    piece.has_moved = True

                

                if self.turn == 'w':
                    if self.b_king_pos in self.get_all_legal_moves(self.state[target[0]][target[1]]):
                        self.state[self.b_king_pos[0]][self.b_king_pos[1]].in_check = True
                    else:
                        self.state[self.b_king_pos[0]][self.b_king_pos[1]].in_check = False
                    self.turn  = 'b'
                else:
                    if self.w_king_pos in self.get_all_legal_moves(self.state[target[0]][target[1]]):
                        self.state[self.w_king_pos[0]][self.w_king_pos[1]].in_check = True
                    else:
                        self.state[self.w_king_pos[0]][self.w_king_pos[1]].in_check = False
                    self.turn  = 'w'
            else:
                #print(f"\n Not {piece.colour} turn")
                pass
        return True

