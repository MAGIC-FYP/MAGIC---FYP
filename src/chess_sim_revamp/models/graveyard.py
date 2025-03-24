from enum import Enum
import chess

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
    w_Q1 = 1
    b_Q1 = 2
    w_Q2 = 3
    b_Q2 = 4
    
    # Rooks
    w_R1 = 5
    b_R1 = 6
    w_R2 = 7
    b_R2 = 8

    # Bishops
    w_B1 = 9
    b_B1 = 10
    w_B2 = 11
    b_B2 = 12

    # Knights
    w_N1 = 13
    b_N1 = 14
    w_N2 = 15
    b_N2 = 16

    # Pawns
    w_P1 = 17
    b_P1 = 18
    w_P2 = 19
    b_P2 = 20
    w_P3 = 21
    b_P3 = 22
    w_P4 = 23
    b_P4 = 24
    w_P5 = 25
    b_P5 = 26
    w_P6 = 27
    b_P6 = 28
    w_P7 = 29
    b_P7 = 30
    w_P8 = 31
    b_P8 = 32

class Graveyard():
    def __init__(self):
        self.gy_coords = generate_graveyard_coordinates()
        self.occupied_position = {} # Set up a dictionary for the pieces
        for sq in GraveyardSquare:
            self.occupied_position[sq] = False  # Set each spot to False as they are empty at the start
        # Add one queen for each color
        self.occupied_position[GraveyardSquare.w_Q1] = chess.Piece(chess.QUEEN, chess.WHITE)
        self.occupied_position[GraveyardSquare.b_Q1] = chess.Piece(chess.QUEEN, chess.BLACK)
        
    def reset(self):
        """resets graveyard"""
        for sq in GraveyardSquare:
            self.occupied_position[sq] = False  # Set each spot to False as they are empty at the start
        # Add one queen for each color
        self.occupied_position[GraveyardSquare.w_Q1] = chess.Piece(chess.QUEEN, chess.WHITE)
        self.occupied_position[GraveyardSquare.b_Q1] = chess.Piece(chess.QUEEN, chess.BLACK)

    def get_lowest_available(self, piece: chess.Piece):
        """Finds the lowest available spot within the correct category"""
        #if piece in GraveyardSquare:
        base_type = piece.symbol().upper() 
        color = "w" if piece.color else "b"

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

    def place_piece(self, piece: chess.Piece):
        """Places a captured piece in the lowest available spot within its category."""
        lowest_spot = self.get_lowest_available(piece)
        if lowest_spot is None:
            print(f"No available graveyard spot for {piece.symbol()}")
            return None
        
        self.occupied_position[lowest_spot] = piece  # Mark as occupied
        return self.gy_coords[lowest_spot]  # Return the new position
    
    def get_coord_column_row(self, graveyard_square: GraveyardSquare):
        """
        Converts the graveyard square to column-row format.
        """
        if graveyard_square in self.gy_coords:
            x, y = self.gy_coords[graveyard_square]
            column = int((x - 2.5) / 5) + 1  # Convert x to column (1-12)
            row = int((y - 2.5) / 5) + 1  # Convert y to row (1-8)
            return (column, row)
        else:
            return "Invalid graveyard square."
        
    def get_white_pieces_positions(self):
        """Returns a list of tuples containing the positions (x, y) of all white pieces in the graveyard."""
        white_pieces_positions = []
        for sq, piece in self.occupied_position.items():
            if piece and piece.color == chess.WHITE:
                white_pieces_positions.append((self.get_coord_column_row(sq), piece))
        return white_pieces_positions

    def get_black_pieces_positions(self):
        """Returns a list of tuples containing the positions (x, y) of all black pieces in the graveyard."""
        black_pieces_positions = []
        for sq, piece in self.occupied_position.items():
            if piece and piece.color == chess.BLACK:
                black_pieces_positions.append((self.get_coord_column_row(sq), piece))
        return black_pieces_positions
    
    

'''This function will automatically assign the GY locations for all pieces'''
def generate_graveyard_coordinates():
    graveyard_coords = {}
    square_size = 5  # Each square is 5x5 cm, will change when we make board
    white_x, black_x = 2.5, 57.5  # Pawn columns, 1 & 12

    # Place white pawns (GY17-31) in column 1
    for i in range(8):
        y_coord = 2.5 + (i * square_size)
        graveyard_coords[GraveyardSquare(GraveyardSquare.w_P1.value + 2*i)] = (white_x, y_coord)  # White pawn

    # Place black pawns (GY18-32) in column 12
    for i in range(8):
        y_coord = 2.5 + (i * square_size)
        graveyard_coords[GraveyardSquare(GraveyardSquare.b_P1.value + 2*i)] = (black_x, y_coord)  # Black pawn

    # Non-pawn pieces (GY1-GY16) based on predefined locations
    piece_positions = {
        GraveyardSquare.w_Q1: (7.5, 37.5),
        GraveyardSquare.b_Q1: (52.5, 2.5),
        GraveyardSquare.w_Q2: (7.5, 32.5),
        GraveyardSquare.b_Q2: (52.5, 7.5),
        GraveyardSquare.w_R1: (7.5, 27.5),
        GraveyardSquare.b_R1: (52.5, 12.5),
        GraveyardSquare.w_R2: (7.5, 22.5),
        GraveyardSquare.b_R2: (52.5, 17.5),
        GraveyardSquare.w_B1: (7.5, 17.5),
        GraveyardSquare.b_B1: (52.5, 22.5),
        GraveyardSquare.w_B2: (7.5, 12.5),
        GraveyardSquare.b_B2: (52.5, 27.5),
        GraveyardSquare.w_N1: (7.5, 7.5),
        GraveyardSquare.b_N1: (52.5, 32.5),
        GraveyardSquare.w_N2: (7.5, 2.5),
        GraveyardSquare.b_N2: (52.5, 37.5)
    }
    
    graveyard_coords.update(piece_positions)
    
    return graveyard_coords

graveyard_coordinates = generate_graveyard_coordinates()