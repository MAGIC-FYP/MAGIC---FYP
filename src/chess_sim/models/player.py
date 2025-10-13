import chess
import requests
import logging
import time
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


class LichessPlayer(BasePlayer):
    '''Player that connects to Lichess for online gameplay - represents the remote opponent'''
    
    def __init__(self, colour: chess.Color, game_stream, board_client):
        """
        Initialize Lichess opponent player.
        
        Args:
            colour: Chess color of this player
            game_stream: Iterator from client.board.stream_game_state()
            board_client: Berserk board client for making moves
        """
        super().__init__(colour)
        self.game_stream = game_stream
        self.board_client = board_client
        self.opponent_name = "Lichess Opponent"
        self.last_moves = []
        
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Wait for opponent's move from Lichess stream."""
        print(f"Waiting for {self.opponent_name}'s move...")
        print(f"DEBUG: Current board state: {board.fen()}")
        print(f"DEBUG: Last known moves: {self.last_moves}")
        
        try:
            # Stream returns events, we need to wait for a gameState with new move
            for event in self.game_stream:
                print(f"DEBUG: Received event type: {event['type']}")
                
                if event['type'] == 'gameFull':
                    # First event - contains full game state
                    state = event['state']
                    moves_str = state.get('moves', '')
                    print(f"DEBUG: gameFull event - moves: {moves_str}")
                    if moves_str:
                        self.last_moves = moves_str.split()
                    print(f"DEBUG: Updated last_moves to: {self.last_moves}")
                    # Continue to wait for actual new moves
                    continue
                    
                elif event['type'] == 'gameState':
                    # Game state update - check for new moves
                    moves_str = event.get('moves', '')
                    current_moves = moves_str.split() if moves_str else []
                    print(f"DEBUG: gameState event - current moves: {current_moves}")
                    print(f"DEBUG: Comparing lengths: current={len(current_moves)}, last={len(self.last_moves)}")
                    
                    # Check if there's a new move
                    if len(current_moves) > len(self.last_moves):
                        # New move detected
                        new_move_uci = current_moves[-1]
                        self.last_moves = current_moves
                        
                        try:
                            move = chess.Move.from_uci(new_move_uci)
                            print(f"{self.opponent_name} played: {new_move_uci}")
                            return move
                        except ValueError:
                            print(f"Invalid move from Lichess: {new_move_uci}")
                            continue
                    else:
                        print(f"DEBUG: No new move detected (same length or shorter)")
                    
                    # Check if game ended
                    status = event.get('status')
                    if status in ['mate', 'resign', 'stalemate', 'timeout', 'draw', 'outoftime', 'cheat', 'noStart', 'unknownFinish', 'variantEnd']:
                        print(f"Game ended on Lichess. Status: {status}")
                        return None
                        
        except Exception as e:
            print(f"Error streaming opponent move: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        return None
    
    def set_opponent_name(self, name: str):
        """Set the opponent's name for display purposes."""
        self.opponent_name = name