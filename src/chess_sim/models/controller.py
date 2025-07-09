import chess
from typing import List, Tuple, Union
from models.graveyard import GraveyardSquare, graveyard_coordinates
    

class Controller:
    def __init__(self, board_size_cm: float = 40.0, square_size_cm: float = 5.0):
        self.calibrated = False
        self.moving = False
        self.board_size_cm = board_size_cm
        self.square_size_cm = square_size_cm
    
    def calibrate(self) -> None:
        '''CALIBRATION LOGIC'''
        print("Calibrating gantry system...")
        self.calibrated = True
        print("Calibration complete.")

    def detect_piece_locations(self):
        '''
        DETECTION WITH HALL EFFECT SENSORS/COPPER TRACES
        Return a dict of square to piece mapping
        '''
        pass

    def move_piece(self, from_square: Union[chess.Square, GraveyardSquare], to_square: Union[chess.Square, GraveyardSquare]) -> bool:
        '''Control gantry to physically move a piece'''
        if not self.calibrated:
            raise RuntimeError("Cannot move: Gantry not calibrated")
        
        from_x, from_y = self._square_to_coordinates(from_square)
        to_x, to_y = self._square_to_coordinates(to_square)
        
        path = self._plan_path((from_x, from_y), (to_x, to_y))
        
        print(f"Moving piece from ({from_x}, {from_y}) to ({to_x}, {to_y})")
        success = self._execute_move(path)
        
        return success
    
    def _square_to_coordinates(self, square) -> Tuple[int, int]:
        '''Convert a chess square to physical coordinates'''
        
        if isinstance(square, chess.Square):
            file_idx = chess.square_file(square)  # 0-7 for A-H
            rank_idx = chess.square_rank(square)  # 0-7 for 1-8
            
            # NEED to change once GANTRY specs are known 5cm per square etc as this is just going to corner not center
            x = file_idx * self.square_size_cm
            y = rank_idx * self.square_size_cm
            
        elif isinstance(square, GraveyardSquare):
            pass
            
        else:
            raise ValueError(f"Unknown square type: {type(square)}")
            
        return (x, y)
    
    def _plan_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]: # List of coordinates to go to in order
        pass
    
    def _execute_move(self, coords: List[Tuple[Tuple[int, int], Tuple[int, int]]]) -> True:
        '''Execute a G-Code command on the robot'''
        self.moving = True
        '''ADD G-CODE EXECUTION LOGIC'''
        self.moving = False
