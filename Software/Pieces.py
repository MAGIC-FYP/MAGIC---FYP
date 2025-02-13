from abc import ABC, abstractmethod
from typing import Literal
import numpy as np


class Board:
    def __init__(self, rows: int = 8, cols: int = 8, populate: bool = True, state: np.array = None, outted: np.array = []):
        self.rows = rows
        self.cols = cols
        self.outted = outted
        if state is None:
            self.grid = np.full((rows, cols), " ")
        else:
            self.grid = state
        self.white_start = [
            "R", "N", "B", "Q", "K", "B", "N", "R"
        ]
        self.black_start = [
            "r", "n", "b", "q", "k", "b", "n", "r"
        ]
        self.white_pawns = [
            "P", "P", "P", "P", "P", "P", "P", "P"
        ]
        self.black_pawns = [
            "p", "p", "p", "p", "p", "p", "p", "p"
        ]
        if populate:
            self.populate()

    def populate(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.grid[i][j] = ""


    def print_ascii(self):
        header = "   " + " ".join(str(col) for col in range(self.cols))
        print(header)
        for i in range(self.rows):
            row_display = [cell if cell != "" else "-" for cell in self.grid[i]]
            print("".join(row_display))

class Piece(ABC):
    def __init__(self, colour: Literal['b', 'w'], position: str):
        self.colour = colour
        self.position = position

    def get_colour(self) -> Literal['b', 'w']:
        return self.colour

    def get_position(self):
        return self.position

    def get_symbol(self) -> str:
        return self.symbol

    def check_surroundings(self, board: Board) -> bool:
        pass        

    @abstractmethod
    def is_legal(self, position: str) -> bool:
        pass

    def move(self, position: str, legal_required: bool = True) -> str:
        if legal_required and not self.is_legal(position):
            return f"Illegal move for {self.__class__.__name__}: {position}"
        self.position = position
        return f"Moved to {position}"


class Pawn(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

class Knight(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

class Bishop(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

class Rook(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

class Queen(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

class King(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, position)

    def is_legal(self, position):
        return True

def main():
    board = Board()
    board.print_ascii()
    

if __name__ == "__main__":
    main()