from enum import Enum

class GraveyardSquare(Enum):
    '''Enum for graveyard squares numbered 1-32 probs a better approach exists'''
    # White pieces (1-16)
    GY1 = 1   # First white piece
    # ...
    GY32 = 32 # Last black piece

graveyard_coordinates = {
    GraveyardSquare.GY1: (10.0, 50.0),
    # ... 
    GraveyardSquare.GY32: (45.0, 5.0),
}