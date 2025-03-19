from enum import Enum

class GraveyardSquare(Enum):
    '''
    Enum for graveyard squares numbered 1-32

    King will never be in the grave so we will have a queen alread located in the GY.
    Odd = W, Even = B

    Edge columns will contain the pawns as they will never come back once they are killed.
    The inner column on either side of the board will contain the other pieces.
    From W perspective, B queen will be next to them, likewise for    B opponent.
    Then it'll go, queen 2, rook 1 & 2, bishop 1 & 2, knight 1 & 2
    '''
    # Queens
    W_Q1 = 1
    B_Q1 = 2
    W_Q2 = 3
    B_Q2 = 4
    
    # Rooks
    W_R1 = 5
    B_R1 = 6
    W_R2 = 7
    B_R2 = 8

    # Bishops
    W_B1 = 9
    B_B1 = 10
    W_B2 = 11
    B_B2 = 12

    # Knights
    W_N1 = 13
    B_N1 = 14
    W_N2 = 15
    B_N2 = 16

    # Pawns
    W_P1 = 17
    B_P1 = 18
    W_P2 = 19
    B_P2 = 20
    W_P3 = 21
    B_P3 = 22
    W_P4 = 23
    B_P4 = 24
    W_P5 = 25
    B_P5 = 26
    W_P6 = 27
    B_P6 = 28
    W_P7 = 29
    B_P7 = 30
    W_P8 = 31
    B_P8 = 32

class Graveyard():
    def __init__(self):
        self.gy_coords = generate_graveyard_coordinates()
        self.occupied_position = {} # Set up a dictionary for the pieces
        for sq in GraveyardSquare:
            self.occupied_position[sq] = False  # Set each spot to False as they are empty at the start
    
    def get_lowest_available(self, piece):
        """Finds the lowest available spot within the correct category"""
        if piece in GraveyardSquare:
            base_type = piece.name.split("_")[1]  # Extract type (P, N, B, etc.)
            color = "WHITE" if "W" in piece.name else "BLACK"

            # Get all spots of this type and color
            possible_spots = []

            for sq in GraveyardSquare:
                if base_type in sq.name and color in sq.name:
                    possible_spots.append(sq)  # Add valid spots to the list
            
            # Find the lowest available one
            for spot in possible_spots:
                if not self.occupied_position[spot]:  
                    return spot  
        return None  # No available spot left

    def place_piece(self, piece):
        """Places a captured piece in the lowest available spot within its category."""
        lowest_spot = self.get_lowest_available(piece)
        if lowest_spot is None:
            print(f"No available graveyard spot for {piece.name}")
            return None
        
        self.occupied_position[lowest_spot] = piece  # Mark as occupied
        return self.gy_coords[lowest_spot]  # Return the new position


'''This function will automatically assign the GY locations for all pieces'''
def generate_graveyard_coordinates():
    graveyard_coords = {}
    square_size = 5  # Each square is 5x5 cm, will change when we make board
    white_x, black_x = 2.5, 57.5  # Pawn columns, 1 & 12

    # Place white pawns (GY17-31) in column 1
    for i in range(8):
        y_coord = 2.5 + (i * square_size)
        graveyard_coords[GraveyardSquare(GraveyardSquare.W_P1.value + 2*i)] = (white_x, y_coord)  # White pawn

    # Place black pawns (GY18-32) in column 12
    for i in range(8):
        y_coord = 2.5 + (i * square_size)
        graveyard_coords[GraveyardSquare(GraveyardSquare.B_P1.value + 2*i)] = (black_x, y_coord)  # Black pawn

    # Non-pawn pieces (GY1-GY16) based on predefined locations
    piece_positions = {
        GraveyardSquare.W_Q1: (7.5, 37.5),
        GraveyardSquare.B_Q1: (52.5, 2.5),
        GraveyardSquare.W_Q2: (7.5, 32.5),
        GraveyardSquare.B_Q2: (52.5, 7.5),
        GraveyardSquare.W_R1: (7.5, 27.5),
        GraveyardSquare.B_R1: (52.5, 12.5),
        GraveyardSquare.W_R2: (7.5, 22.5),
        GraveyardSquare.B_R2: (52.5, 17.5),
        GraveyardSquare.W_B1: (7.5, 17.5),
        GraveyardSquare.B_B1: (52.5, 22.5),
        GraveyardSquare.W_B2: (7.5, 12.5),
        GraveyardSquare.B_B2: (52.5, 27.5),
        GraveyardSquare.W_N1: (7.5, 7.5),
        GraveyardSquare.B_N1: (52.5, 32.5),
        GraveyardSquare.W_N2: (7.5, 2.5),
        GraveyardSquare.B_N2: (52.5, 37.5)
    }
    
    graveyard_coords.update(piece_positions)
    
    return graveyard_coords

graveyard_coordinates = generate_graveyard_coordinates()