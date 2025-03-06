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
                self.state[target[0]][target[1]] = self.state[position[0]][position[1]]
                self.state[position[0]][position[1]] = None
                if self.turn == 'w':
                    self.turn  = 'b'
                else:
                    self.turn  = 'w'
            else:
                #print(f"\n Not {piece.colour} turn")
                pass
        return True

