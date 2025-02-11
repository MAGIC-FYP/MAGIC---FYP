class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position

    def get_color(self):
        return self.color

    def get_position(self):
        return self.position

    def move(self, position, is_legal):
        self.position = position



class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True

class Bishop(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True

class Queen(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

    def is_legal(self, position):
        return True
