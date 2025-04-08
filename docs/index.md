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
    class GraveyardSquare(Enum)
        Inputs: None
        Outputs: dict mapping GraveyardSquare → (x, y) positions
        Purpose: Defines and returns the physical layout (coordinates) of all 32 graveyard squares on the board.

    class Graveyard()
        Graveyard.__init__()
            Inputs: None
            Outputs: None
            Purpose: Initialises the graveyard with empty squares and places one white and one black queen by default.

        Graveyard.reset()
            Inputs: None
            Outputs: None
            Purpose: Clears all graveyard positions and resets it back to the initial state with one queen for each color.

        Graveyard.get_lowest_available(piece)
            Inputs: piece: chess.Piece
            Outputs: GraveyardSquare or None
            Purpose: Finds the lowest-numbered available graveyard square that matches the piece type and color.

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
            Purpose: Converts grid (col, row) into pixel/surface position for rendering on a 2D interface.

        Graveyard.pre_loaded_graveyard(fen)
            Inputs: fen: str
            Outputs: None
            Purpose: Parses a FEN string, determines which pieces have been captured, and places them in the graveyard.

    preLoadedGraveyard()
        Inputs: None
        Outputs: int (always returns 0)
        Purpose: Placeholder; doesn’t currently do anything useful. May be legacy or stub function.

