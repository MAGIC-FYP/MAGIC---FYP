"""
Chess pieces classes and methods to be used in external files.
Note that the position of a piece is stored by the board class.
Currently pieces are only able defined in this way to be used a representitive obj
"""

class Piece:
    def __init__(self, colour: str):
        self.colour = colour
        
    def get_symbol(self) -> str:
        return self.symbol.upper() if self.colour == 'w' else self.symbol.lower()
    
    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        raise NotImplementedError("Subclasses must implement is_legal")
    
    def is_friendly(self, piece: 'Piece') -> bool:
        if piece is None:
            return False
        return piece.colour == self.colour

class Pawn(Piece):
    symbol = 'P'
    
    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        row_diff = target[0] - position[0]
        col_diff = target[1] - position[1]
        
        # Direction depends on color (white moves up, black moves down)
        direction = 1 if self.colour == 'w' else -1
        start_row = 1 if self.colour == 'w' else 6
        
        # Basic one square forward move
        if col_diff == 0 and row_diff == direction and state[target[0]][target[1]] is None:
            return True
            
        # Initial two square move
        if position[0] == start_row and col_diff == 0 and row_diff == 2 * direction:
            if state[target[0]][target[1]] is None and state[position[0] + direction][position[1]] is None:
                return True
                
        # Capture diagonally
        if abs(col_diff) == 1 and row_diff == direction:
            target_piece = state[target[0]][target[1]]
            if target_piece is not None and not self.is_friendly(target_piece):
                return True
                
        return False

class Knight(Piece):
    symbol = 'N'
    
    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        row_diff = abs(target[0] - position[0])
        col_diff = abs(target[1] - position[1])
        
        # Knight moves in L-shape: 2 squares in one direction and 1 in the other
        if (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2):
            target_piece = state[target[0]][target[1]]
            return target_piece is None or not self.is_friendly(target_piece)
        return False

class Bishop(Piece):
    symbol = 'B'
    
    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        row_diff = target[0] - position[0]
        col_diff = target[1] - position[1]
        
        # Bishop moves diagonally
        if abs(row_diff) != abs(col_diff):
            return False
            
        # Check path for obstacles
        row_step = 1 if row_diff > 0 else -1
        col_step = 1 if col_diff > 0 else -1
        
        current_row = position[0] + row_step
        current_col = position[1] + col_step
        
        while current_row != target[0]:
            if state[current_row][current_col] is not None:
                return False
            current_row += row_step
            current_col += col_step
            
        target_piece = state[target[0]][target[1]]
        return target_piece is None or not self.is_friendly(target_piece)

class Rook(Piece):
    symbol = 'R'

    def __init__(self, colour: str):
        super().__init__(colour)
        self.has_moved = False
    
    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        row_diff = target[0] - position[0]
        col_diff = target[1] - position[1]
        
        # Rook moves horizontally or vertically
        if row_diff != 0 and col_diff != 0:
            return False
            
        # Check path for obstacles
        if row_diff != 0:
            step = 1 if row_diff > 0 else -1
            for row in range(position[0] + step, target[0], step):
                if state[row][position[1]] is not None:
                    return False
        else:
            step = 1 if col_diff > 0 else -1
            for col in range(position[1] + step, target[1], step):
                if state[position[0]][col] is not None:
                    return False
                    
        target_piece = state[target[0]][target[1]]
        return target_piece is None or not self.is_friendly(target_piece)

class Queen(Piece):
    symbol = 'Q'

    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        # Queen combines Rook and Bishop movements
        rook = Rook(self.colour)
        bishop = Bishop(self.colour)
        return rook.is_legal(position, target, state) or bishop.is_legal(position, target, state)

class King(Piece):
    symbol = 'K'
    def __init__(self, colour: str):
        super().__init__(colour)
        self.has_moved = False
        self.castle_rook = False

    def is_legal(self, position: tuple, target: tuple, state: list[list['Piece']]) -> bool:
        row_diff = abs(target[0] - position[0])
        col_diff = abs(target[1] - position[1])
        
        # King moves one square in any direction
        if row_diff <= 1 and col_diff <= 1:
            target_piece = state[target[0]][target[1]]
            return target_piece is None or not self.is_friendly(target_piece)
        
        # Check for castling
        can_castle = self.can_castle(position, target, state)
        if can_castle:
            self.castle_rook = can_castle
            return True
        else:
            self.castle_rook = False
        return False

    def can_castle(self, position: tuple, target: tuple, state: list[list['Piece']]) -> tuple:
        # Ensure the king is moving two squares horizontally
        target_piece = state[target[0]][target[1]]

        if target != (position[0], 2) and target != (position[0], 6):
            return None
        
        direction = 1 if target[1] > position[1] else -1

        if direction == 1:
            target_piece = state[position[0]][7]
            if target_piece:
                if target_piece.symbol == 'R':
                    if target_piece.colour == self.colour:
                        if state[position[0]][5] is None and state[position[0]][6] is None:
                            print("kingside")
                            return (position[0], 7)
        else:
            target_piece = state[position[0]][0]
            if target_piece:
                if target_piece.symbol == 'R':
                    if target_piece.colour == self.colour:
                        if state[position[0]][3] is None and state[position[0]][2] is None and state[position[0]][1] is None:
                            print("queenside")
                            return (position[0], 0)
        
        # Return the position of the rook if castling is possible
        return None
