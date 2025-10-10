from enum import Enum
import chess

class GraveyardSquare(Enum):
    # White pieces
    w_PQ = 1
    w_GY2 = 2
    w_GY3 = 3
    w_GY4 = 4
    w_GY5 = 5
    w_GY6 = 6
    w_GY7 = 7
    w_GY8 = 8
    w_GY9 = 9
    w_GY10 = 10
    w_GY11 = 11
    w_GY12 = 12
    w_GY13 = 13
    w_GY14 = 14
    w_GY15 = 15
    w_GY16 = 16

    # Black pieces
    b_PQ = 17
    b_GY2 = 18
    b_GY3 = 19
    b_GY4 = 20
    b_GY5 = 21
    b_GY6 = 22
    b_GY7 = 23
    b_GY8 = 24
    b_GY9 = 25
    b_GY10 = 26
    b_GY11 = 27
    b_GY12 = 28
    b_GY13 = 29
    b_GY14 = 30
    b_GY15 = 31
    b_GY16 = 32
    
class Graveyard():
    def __init__(self):
        self.gy_coords = generate_graveyard_coordinates()
        self.occupied_position = {} # Set up a dictionary for the pieces
        for sq in GraveyardSquare:
            self.occupied_position[sq] = False  # Set each spot to False as they are empty at the start
        # Add one queen for each color
        self.occupied_position[GraveyardSquare.w_PQ] = chess.Piece(chess.QUEEN, chess.WHITE)
        self.occupied_position[GraveyardSquare.b_PQ] = chess.Piece(chess.QUEEN, chess.BLACK)
        
    def reset(self):
        for sq in GraveyardSquare:
            self.occupied_position[sq] = False  # Set each spot to False as they are empty at the start
        # Add one queen for each color
        self.occupied_position[GraveyardSquare.w_PQ] = chess.Piece(chess.QUEEN, chess.WHITE)
        self.occupied_position[GraveyardSquare.b_PQ] = chess.Piece(chess.QUEEN, chess.BLACK)

    def get_lowest_available(self, piece: chess.Piece):
        """Finds the lowest available spot within the correct category"""
        color = "w" if piece.color else "b"
        possible_spots = []

        for sq in GraveyardSquare:
            if color in sq.name:
                possible_spots.append(sq) 
        
        for spot in possible_spots:
            if not self.occupied_position[spot]:  
                return spot  
        return None 
        
    def place_piece(self, piece: chess.Piece):
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
        square_size = 5  #CHANGE THIS TO CONFIG FILE

        if graveyard_square in self.gy_coords:
            x, y = self.gy_coords[graveyard_square]
            column = int((x - (square_size/2)) / (square_size)) + 1  # Convert x to column (1-12)
            row = int((y - (square_size/2)) / (square_size)) + 1  # Convert y to row (1-8)
            return (column, row)
        else:
            return "Invalid graveyard square."      
    
    def get_white_pieces_positions(self):
        white_pieces_positions = []
        for sq, piece in self.occupied_position.items():
            if piece and piece.color == chess.WHITE:
                white_pieces_positions.append((self.get_coord_column_row(sq), piece))
        return white_pieces_positions

    def get_black_pieces_positions(self):
        black_pieces_positions = []
        for sq, piece in self.occupied_position.items():
            if piece and piece.color == chess.BLACK:
                black_pieces_positions.append((self.get_coord_column_row(sq), piece))
        return black_pieces_positions
    

    def pre_loaded_graveyard(self, fen):  # Dont think its reading the global file correctly
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
        # print('To place:', initial_pieces)
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
            #print("BANG")
        #print('Graveyard occupation:', self.occupied_position)
    
    def sq_to_gy_coord(self, sq):
        return graveyard_coordinates[sq]

    def pos_to_gy_coord(self, pos):
        
        return [(pos[0][0]*5)-2.5, (pos[0][1]*5)-2.5]


def generate_graveyard_coordinates():
    graveyard_coords = {}
    square_size = 5  #CHANGE THIS TO CONFIG FILE

    #Column coordinates for the graveyard
    white_x = square_size/2
    black_x = 11 * square_size + square_size/2

    # White
    y_coord = 8*square_size - square_size/2
    for i in range(1,17):
        if i < 9:
            graveyard_coords[GraveyardSquare(i)] = (white_x, y_coord)
            y_coord -= square_size
        else:
            y_coord += square_size
            graveyard_coords[GraveyardSquare(i)] = (white_x + square_size, y_coord)

    # Black
    y_coord = square_size/2
    for i in range(17,33):
        if i < 25:
            graveyard_coords[GraveyardSquare(i)] = (black_x, y_coord)
            y_coord += square_size
        else:
            y_coord -= square_size
            graveyard_coords[GraveyardSquare(i)] = (black_x - square_size, y_coord)
            

    return graveyard_coords

graveyard_coordinates = generate_graveyard_coordinates()
#print(graveyard_coordinates)