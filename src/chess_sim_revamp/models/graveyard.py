from enum import Enum
import chess

class GraveyardSquare(Enum):
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

    def place_piece_at(self, coord, piece: chess.Piece):
        matching_squares = [square for square, pos in self.gy_coords.items() 
                       if pos == coord]
    
        if matching_squares:
            graveyard_square = matching_squares[0]  # Get the first matching square
            if not self.occupied_position[graveyard_square]:
                self.occupied_position[graveyard_square] = piece
                return True
            else:
                print(f"Square {graveyard_square.name} is already occupied.")
                return False
        else:
            print(f"Invalid graveyard coordinate: {coord}")
            return False

    def remove_piece_at(self, coord):
        matching_squares = [square for square, pos in self.gy_coords.items() 
                       if pos == coord]
    
        if matching_squares:
            graveyard_square = matching_squares[0]  # Get the first matching square
            if self.occupied_position[graveyard_square]:
                self.occupied_position[graveyard_square] = False
                return True
            else:
                print(f"Square not occupied.")
                return False
        else:
            print(f"Invalid graveyard coordinate: {coord}")
            return False
        
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
        
    def piece_at(self, coord):
        """
        Retrieves the piece at the given graveyard coordinate.

        :param coord: The (x, y) coordinate of the graveyard square.
        :return: The piece at the given coordinate, or None if empty.
        """
        matching_squares = [square for square, pos in self.gy_coords.items() if pos == coord]

        if matching_squares:
            graveyard_square = matching_squares[0]
            return self.occupied_position.get(graveyard_square, None)
        else:
            return None
    
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
    
    def get_empty_squares(self):
        """Returns a list of all empty squares in the graveyard."""
        empty_squares = []
        for sq, piece in self.occupied_position.items():
            if not piece:
                empty_squares.append(self.get_coord_column_row(sq))
        return empty_squares
    
    def get_surface_from_gy_coord(self, coord, surface_size= [5*12,5*8]):
        return (coord[0] * (surface_size[0] // 12)-(surface_size[1] / (8*2)), coord[1] * (surface_size[1] // 8)-(surface_size[1] / (8*2)))

    def pre_loaded_graveyard(self, fen):  # Dont think its reading the global file correctly
        """Determines which pieces have been captured and places them in the graveyard."""
        print('Gameloading')
        print('FEN:', fen)
        # List of all pieces (both colors) at the start of a game
        initial_pieces = list("QRRBBNNPPPPPPPPqrrbbnnpppppppp")

        # Extract letters from FEN (ignoring slashes and expanding empty spaces)
        letters = []
        for char in fen:
            if char.isdigit():
                letters.extend([" "] * int(char))  # Convert numbers to spaces
            elif char != "/":
                letters.append(char)

        # Remove pieces that are still on the board
        for piece in letters:
            if piece in initial_pieces:
                initial_pieces.remove(piece)
        print('To place:', initial_pieces)
        # The remaining pieces need to be placed in the graveyard
        # Convert to chess.Piece objects before placing
        piece_mapping = {
            'P': chess.PAWN, 'N': chess.KNIGHT, 'B': chess.BISHOP,
            'R': chess.ROOK, 'Q': chess.QUEEN, 'K': chess.KING
        }

        for piece_symbol in initial_pieces:
            color = chess.WHITE if piece_symbol.isupper() else chess.BLACK
            piece_type = piece_mapping[piece_symbol.upper()]
            piece_obj = chess.Piece(piece_type, color)
            self.place_piece(piece_obj)
            print("BANG")
        print('Graveyard occupation:', self.occupied_position)

    def revive_piece(self, piece: chess.Piece):
        for square, occupied in self.occupied_position.items():
            if isinstance(occupied, chess.Piece) and occupied.piece_type == piece.piece_type and occupied.color == piece.color:
                self.occupied_position[square] = False  # Free up the spot
                return square  # Or return coord if needed
        print('Not in graveyard, please place that piece on the board')
        return None  # No matching piece found

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
