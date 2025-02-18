import numpy as np
from abc import ABC, abstractmethod
from typing import Literal

"""
Chess pieces classes and methods to be used in external files.
Note that the position of a piece is stored by the board class.
Currently pieces are only able defined in this way to be used a representitive obj
"""

class Pawn():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'P' if self.colour == 'w' else 'p'
    def is_legal(self, position: str) -> bool:
        return True

class Knight():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'N' if self.colour == 'w' else 'n'
    def is_legal(self, position: tuple, target: tuple, state: list[list[str]]) -> bool:
        return True

class Bishop():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'B' if self.colour == 'w' else 'b'
    def is_legal(self, position: tuple, target: tuple, state: list[list[str]]) -> bool:
        return True

class Rook():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'R' if self.colour == 'w' else 'r'
    def is_legal(self, position: tuple, target: tuple, state: list[list[str]]) -> bool:
        return True

class Queen():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'Q' if self.colour == 'w' else 'q'
    def is_legal(self, position: tuple, target: tuple, state: list[list[str]]) -> bool:
        return True

class King():
    def __init__(self, colour):
        self.colour = colour
    def get_symbol(self):
        return 'K' if self.colour == 'w' else 'k'
    def is_legal(self, position: tuple, target: tuple, state: list[list[str]]) -> bool:
        return True
