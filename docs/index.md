# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.


## Content Tabs

This is some examples of content tabs.



## GRAVEYARD.py
### Notes
King will never be in the grave so we will have a queen already located in the graveyard.

Odd = W, Even = B

Edge columns will contain the pawns as they will never come back once they are killed.
The inner column on either side of the board will contain the other pieces.
From W perspective, B queen will be next to them, likewise for the B opponent.
Then it'll go, queen 2, rook 1 & 2, bishop 1 & 2, knight 1 & 2.

At the start of the game each piece is given a spot in the grave, as pieces are removed the allocated spots change based on available places in the graveyard.

    class GraveyardSquare(Enum)
        Inputs: None
        Outputs: dict mapping GraveyardSquare → (x, y) positions
        Purpose: Defines and returns the physical layout (coordinates) of all 32 graveyard squares on the board.
        Enum is used for graveyard squares numbered 1-32

    class Graveyard()
        Graveyard.__init__()
            Inputs: None
            Outputs: None
            Purpose: Initialises the graveyard with empty squares and places one white and one black queen by default.

        Graveyard.reset()
            Inputs: None
            Outputs: None
            Purpose: Clears all graveyard positions and resets it back to the initial state with one queen for each color.
                     This is done by setting each spot to False as they are empty at the start.

        Graveyard.get_lowest_available(piece)
            Inputs: piece: chess.Piece
            Outputs: GraveyardSquare or None
            Purpose: Finds the lowest-numbered available graveyard square that matches the piece type and color.
                     A piece is removed from the board, the system determines: colour and type, it then finds the lowest avaible spot for the piece type.
        
        Graveyard.place_piece_at(coord, piece)
            Inputs: coord: tuple, piece: chess.Piece
            Outputs: bool
            Purpose: Attempts to place a given piece at a specific coordinate in the graveyard. Returns success status.

        Graveyard.remove_piece_at(coord)
            Inputs: coord: tuple
            Outputs: bool
            Purpose: Removes a piece from a specific graveyard coordinate. Returns whether removal was successful.

        Graveyard.place_piece(piece)
            Inputs: piece: chess.Piece
            Outputs: (x, y) coordinate or None
            Purpose: Automatically finds a free spot for the captured piece and places it in the graveyard.

        Graveyard.get_coord_column_row(graveyard_square)
            Inputs: graveyard_square: GraveyardSquare
            Outputs: (column, row) or string
            Purpose: Converts internal coordinates of a square to a (column, row) format for display/logging.

        Graveyard.piece_at(coord)
            Inputs: coord: tuple
            Outputs: chess.Piece or None
            Purpose: Returns the piece located at the given coordinate, if any.

        Graveyard.get_white_pieces_positions()
            Inputs: None
            Outputs: List of ((col, row), piece) tuples
            Purpose: Returns the locations and types of all white pieces currently in the graveyard.

        Graveyard.get_black_pieces_positions()
            Inputs: None
            Outputs: List of ((col, row), piece) tuples
            Purpose: Returns the locations and types of all black pieces currently in the graveyard.

        Graveyard.get_empty_squares()
            Inputs: None
            Outputs: List of empty (col, row) tuples
            Purpose: Lists all currently unoccupied squares in the graveyard.

        Graveyard.get_surface_from_gy_coord(coord, surface_size=[60, 40])
            Inputs: coord: (int, int), optional surface_size: [int, int]
            Outputs: (x, y)
            Purpose: Converts grid (col, row) into pixel/surface position for rendering on a 2D interface. Can help with debugging

        Graveyard.pre_loaded_graveyard(fen)
            Inputs: fen: str
            Outputs: None
            Purpose: Goes through a given FEN string and determines which pieces have been captured, and places them in the graveyard.

    generate_graveyard_coordinates():
        Inputs: None
        Outputs: None
        Purpose: The function will automatically assign the GY locations for all pieces. This will be used by the gantry.

