from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional
import chess
from stockfish import Stockfish

class PlayerType(Enum):
    HUMAN = 1
    COMPUTER = 2

class BasePlayer(ABC):
    '''Abstract base class for chess players.'''
    
    def __init__(self, colour: chess.Color):
        self.colour = colour
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
    
class Stockfish(BasePlayer):
    '''Stockfish chess player implementation'''

    def __init__(self, colour: chess.Color, difficulty: int = 10, depth: int = 5): #I want depth to be optional but defult to 5, also difficulty to default to 10
        super().__init__(colour)
        self.engine = Stockfish("/usr/local/bin/stockfish") # This will need changing as its set up for Alex 
        self.difficulty = difficulty
        self.depth = depth

        self.engine.set_skill_level(self.difficulty)  # Set difficulty level
        self.engine.set_depth(self.depth)  # Set search depth

    def get_move(self, board):
        self.engine.set_fen_position(board.fen()) #Get board state
        evaluation = self.engine.get_evaluation()  # Evaluate the board, not currently used, but can give a live score of the board
        best_move = self.engine.get_best_move()  # Return the top move

        move = chess.Move.from_uci(best_move)   #Untested
        if move in board.legal_moves:
            return move
        else:
            return "No valid moves found"  # Better handling for empty moves