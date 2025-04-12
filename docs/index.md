# Files & Functions
## Important stuff:

For full documentation visit [mkdocs.org](https://www.mkdocs.org).
### Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

### Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.


## player.py
#### Notes
This file is used to set up the players in the game, there are multiple types of chess players. It defines a base class (BasePlayer) and several subclasses to represent human players, simple computer opponents, an AI-powered player using Stockfish, and a replay system for archived games.

Each player class implements the get_move(board) method to move pieces.

    class PlayerType(Enum)
        Purpose: Defines type of player.
                 Currently set as Human = 1, Robot = 2

    class BasePlayer(ABC)
        Purpose: Abstract base class for all types of chess players. All players (human, computer, stockfish, etc.) inherit from this.
        Key Attributes: 
                    - colour: chess.WHITE or chess.BLACK
                    - time_left: (unused, but could store timer info)
                    - captured_pieces: list of captured chess.Piece objects

    class HumanPlayer(BasePlayer)
        Input: Chess Board
        Output: Player Move
        Purpose: Represents a human player who inputs moves manually.

    class ComputerBasic(BasePlayer)
        *UNUSED*
        Purpose: Simple computer player that picks the first legal move.

    class Stockfish(BasePlayer) 
        Purpose: Chess player that uses Stockfish engine via an online API. It can destroy you.
                 Depth is the difficulty
    
    class ArchivedPlayers(BasePlayer)
        Purpose: Simulates a player from a already complete game, is used with the LiChess API
        Key Attributes:
                    - moves: List of moves in UCI string format.
                    - white_name, black_name: Names of players.
                    - current_move_index: Tracks replay progress.


## GRAVEYARD.py
#### Notes
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

## chessAPI.py
#### Notes
Just like the name suggests this file handles all API related functions. All functions are currently only for LiChess.org, however may
use Chess.com eventually. 

Important stuff: 
- API_TOKEN = 'lip_x73cN37xXXVy7EkHCbDa'

(This is the projects personal token, don't want to lose it)

    archived_game(username):
        Input: username
        Output: 
                - moves (List[str]): Cleaned list of moves from the PGN.
                - white_name (str): Name of the white player.
                - black_name (str): Name of the black player.
        Purpose: Retrieve the most recent finished game for a given user and extract the move list and player names.
        How it works:
        - Queries the user's most recent game using client.games.export_by_player.
        - Parses the PGN to extract moves and strip formatting (e.g., move numbers).
        - Returns the move list along with the names of the players.

        This can then be passed to 'class ArchivedPlayers(BasePlayer)' which will set up the preloaded game

    online_game(username):
        Input: username
        Output: None (prints the latest moves to the console, there is a delay to prevent cheating sadly)
        Purpose: Get real time moves from an online game
        How it works:
        - Finds the user’s current live game using export_by_player(..., ongoing=True).
        - Tracks the number of moves already made.
        - In a loop, repeatedly checks for new moves using client.games.export.
        - Prints new moves as they are made by each player (delayed though).

    get_active_game():
        Input: None
        Output: gameId (str or None): Returns the game ID if it’s your turn; otherwise returns None
        Purpose: This function is linked to the API token (will only work with the token owners games)
                 Detect if there is an active game where it's the logged-in user's turn.
                 This function will be used with 'send_move()'
        How it works:
        - Sends a GET request to https://lichess.org/api/account/playing using the API token.
        - Searches the nowPlaying list for any game where isMyTurn is true.
        - Returns the corresponding game ID.

    send_move(game_id, move):
    ### CURRENT STATUS: still building ###

        Input:  - game_id (str): The ID of the active game.
                - move (str): A UCI-format move string (e.g., "e2e4").
        Output: Tuple of (status_code, response_text): HTTP status and Lichess response message. (For debugging).
        Purpose: Send a move to a live game on Lichess.
        How it works:
        - Uses a POST request to the /board/game/{game_id}/move/{move} endpoint with authorization.
        - Returns the result of the request for logging or debugging.