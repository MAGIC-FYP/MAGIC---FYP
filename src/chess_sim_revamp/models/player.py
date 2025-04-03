import chess
import requests
import logging
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional

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

    def __init__(self, colour: chess.Color, depth: int = 5): # Depth / Difficulty are Correlated
        super().__init__(colour)
        self.depth = depth
        self.api_endpoint = "https://stockfish.online/api/s/v2.php"
        self.logger = self._create_default_logger

    def _create_default_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        params = {
            "fen": board.fen(),
            "depth": min(self.depth, 16)
        }
        
        try:
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()
            
            result = response.json()
            if not result.get('success', False):
                self.logger.error(f"API Error: {result.get('data', 'Unknown error')}")
                return None

            best_move_uci = result['continuation'].split()[0]
            move = chess.Move.from_uci(best_move_uci)
            
            if move not in board.legal_moves:
                self.logger.warning(f"Suggested move {best_move_uci} is not legal.")
                return None
            
            return move
        
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
        except (ValueError, KeyError) as e:
            self.logger.error(f"Data parsing error: {e}")
        
        return None

class ArchivedPlayers(BasePlayer):
    '''Player for replaying an old chess game from a given move list.'''
    
    def __init__(self, moves: list[str], white_name: str, black_name: str):
        self.moves = [chess.Move.from_uci(move) for move in moves]
        self.white_name = white_name
        self.black_name = black_name
        self.current_move_index = 0

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the next move in the replay sequence."""
        if self.current_move_index < len(self.moves):
            move = self.moves[self.current_move_index]
            self.current_move_index += 1
            return move
        return None  # No more moves

    def reset(self):
        """Reset the replay to the beginning."""
        self.current_move_index = 0

    def get_current_player(self) -> str:
        """Return the current player's name based on move index."""
        return self.white_name if self.current_move_index % 2 == 0 else self.black_name

    def __str__(self) -> str:
        return f"Replay Mode: {self.white_name} (White) vs {self.black_name} (Black)"