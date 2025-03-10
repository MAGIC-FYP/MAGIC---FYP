from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional
import chess

class PlayerType(Enum):
    HUMAN = 1
    COMPUTER = 2

class BasePlayer(ABC):
    '''Abstract base class for chess players.'''
    
    def __init__(self, color: chess.Color):
        self.color = color
        self.time_left = None
        self.captured_pieces: List[chess.Piece] = []
    
    def capture_piece(self, piece: chess.Piece) -> None:
        self.captured_pieces.append(piece)

    def get_captured_pieces(self) -> List[chess.Piece]:
        return self.captured_pieces
    
    @abstractmethod
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        '''Get the next move from this player.'''
        pass
    
    def __str__(self) -> str:
        return f"{'White' if self.color else 'Black'} player"


class HumanPlayer(BasePlayer):
    '''Human chess player implementation'''
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        ''' Get move input from human player '''
        while True:
            move_str = input("Enter your move (e.g. e2e4): ")
            try:
                move = chess.Move.from_uci(move_str)
                if move in board.legal_moves:
                    return move
                print("Invalid move. Please try again.")
            except ValueError:
                print("Invalid format. Please use UCI notation (e.g. 'e2e4').")


class ComputerBasic(BasePlayer):
    '''Computer chess player implementation'''
    
    def __init__(self, colour: chess.Color, difficulty: int):
        super().__init__(colour)
        self.difficulty = difficulty  
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        ''' 
        Get move from computer player currently just returns the first legal move can make 
        another class for more advanced engine or add more logic here with more difficulty levels
        '''
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
            
        print("Computer is thinking...")
        return legal_moves[0]