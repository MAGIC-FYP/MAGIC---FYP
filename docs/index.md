# Files & Functions
## Important stuff:

For full documentation visit [mkdocs.org](https://www.mkdocs.org).
### Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.
* `pip install mkdocs` - might need to install to open
* `pip install mkdocs-material` - might need to install to open

### Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.


## models/player.py
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


## models/graveyard.py
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
        
        Graveyard.revive_piece(piece: chess.Piece):
            Unsure if this works, as unsure if it will know which pawn to take to the graveyard, might have to add the pawn as an  input

            Input: piece (The promoted piece type and player colour)
            Output: Graveyard coord square or None if there are no spare pieces in there
            Purpose: Revives a matching piece from the graveyard for promotion.
                     Removes the first matching piece found and returns its original graveyard square.
            Current how to use:
            promotion_piece = chess.Piece(chess.QUEEN, chess.WHITE)
            revived_square = graveyard.revive_piece(promotion_piece)

    generate_graveyard_coordinates():
        Inputs: None
        Outputs: None
        Purpose: The function will automatically assign the GY locations for all pieces. This will be used by the gantry.

## models/chessAPI.py
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

## gui/chess_gui.py
#### Notes
This file contains all functions for chess GUI handling.

    class Display:
        Purpose: Handles the display of the chess board and graveyard.
        Key Attributes:
                    - board_size: Size of the board in pixels.
                    - logger: Boolean indicating if logging is enabled.
                    - screen_size: Size of the screen in pixels.
                    - screen: Pygame screen object.
                    - selected_square: Boolean indicating if a square is selected.
                    - message: String to be displayed on the screen.
                    - path: Dictionary storing path information for display.
                    - path_extra: Additional path information for display.
                    - show_path: Boolean indicating if paths should be shown.
                    - legal_moves: List of legal moves.
                    - show_mouse_coords: Boolean indicating if mouse coordinates should be shown.
                    - output_state_button: Button for outputting board state.
                    - reset_button: Button for resetting the game.
                    - mouse_loc_button: Button for showing mouse coordinates.
                    - show_path_button: Button for showing paths.
                    - graveyard_squares_white: List of white graveyard squares.
                    - graveyard_squares_black: List of black graveyard squares.
                    - graveyard_squares: Combined list of graveyard squares.

        disp_board(board, graveyard, current_player):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player)
            Outputs: None
            Purpose: Displays the chess board and graveyard.

        _disp_graveyard(graveyard):
            Inputs: graveyard (Graveyard)
            Outputs: None
            Purpose: Displays the graveyard.

        _disp_playing_board(board):
            Inputs: board (chess.Board)
            Outputs: None
            Purpose: Displays the playing board.

        _top_text(current_player):
            Inputs: current_player (Player)
            Outputs: None
            Purpose: Displays the current player's turn at the top of the screen.

        _disp_button(button, button_label):
            Inputs: button (pygame.Rect), button_label (str)
            Outputs: None
            Purpose: Displays a button on the screen with a given label.

        display_promotion_box(board, graveyard, current_player, piece, to_square):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player), piece (chess.Piece), to_square (int)
            Outputs: str
            Purpose: Displays a box with promotion options and returns the selected piece.

        close_disp():
            Inputs: None
            Outputs: None
            Purpose: Closes the display.

        handle_events(board):
            Inputs: board (chess.Board)
            Outputs: bool
            Purpose: Handles the events in the game.

        handle_mouse_click(board, graveyard, current_player):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player)
            Outputs: int
            Purpose: Handles the mouse click events and returns the board coordinates of the mouse click.

        get_next_move_from_click(board, graveyard, current_player):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player)
            Outputs: chess.Move
            Purpose: Handles the mouse click events and returns the next move.

        display_promotion_box(board, graveyard, current_player, piece, to_square):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player), piece (chess.Piece), to_square (int)
            Outputs: str
            Purpose: Displays a box with promotion options and returns the selected piece.

        close_disp():
            Inputs: None
            Outputs: None
            Purpose: Closes the display.

        handle_events(board):
            Inputs: board (chess.Board)
            Outputs: bool
            Purpose: Handles the events in the game.

        handle_mouse_click(board, graveyard, current_player):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player)
            Outputs: int
            Purpose: Handles the mouse click events and returns the board coordinates of the mouse click.

        get_next_move_from_click(board, graveyard, current_player):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player)
            Outputs: chess.Move
            Purpose: Handles the mouse click events and returns the next move.

        display_promotion_box(board, graveyard, current_player, piece, to_square):
            Inputs: board (chess.Board), graveyard (Graveyard), current_player (Player), piece (chess.Piece), to_square (int)
            Outputs: str
            Purpose: Displays a box with promotion options and returns the selected piece.

        close_disp():
            Inputs: None
            Outputs: None
            Purpose: Closes the display.

        handle_events(board):
            Inputs: board (chess.Board)
            Outputs: bool

## algorithms/a_star.py
#### Notes
This file contains the implementation of the A* pathfinding algorithm.

    astar(map, start_pos, end_pos, allow_diagonal_movement = True, surface_size=[5*12,5*8], res = 100):
        Inputs:
            - map (list of lists): 2D representation of the environment.
            - start_pos (list of two ints): Starting position of the path.
            - end_pos (list of two ints): Ending position of the path.
            - allow_diagonal_movement (bool): Flag to allow diagonal movement.
            - surface_size (list of two ints): Size of the surface in pixels.
            - res (int): Resolution of the surface.
        Outputs:
            - list of tuples: The path from start to end.
        Purpose: Finds the shortest path between two points in a 2D environment using the A* algorithm.
        How it works:
            - Initializes the start and end nodes.
            - Uses a priority queue to explore the environment.
            - Calculates the cost of reaching each node and the heuristic cost to the end.
            - Backtracks from the end node to find the shortest path.

    simplify_path(points, epsilon=1.0):
        Inputs:
            - points (list of tuples): List of (x, y) coordinates representing the path.
            - epsilon (float): Sensitivity threshold to control the simplification.
        Outputs:
            - list of tuples: Simplified list of (x, y) points.
        Purpose: Simplifies a given path by removing intermediate points in straight segments.
        How it works:
            - Finds the point with the maximum distance from the line formed by the first and last points.
            - Recursively simplifies the two halves if the maximum distance is greater than epsilon.
            - Merges results, excluding the duplicate point at the junction.

    perpendicular_distance(point, start, end):
        Inputs:
            - point (tuple of two ints): Point to calculate distance for.
            - start (tuple of two ints): Starting point of the line.
            - end (tuple of two ints): Ending point of the line.
        Outputs:
            - float: The perpendicular distance from the point to the line.
        Purpose: Calculates the perpendicular distance from a point to a line.
        How it works:
            - Uses the formula for perpendicular distance to calculate the distance.

    calculate_h_cost(pos1, pos2):
        Inputs:
            - pos1 (tuple of two ints): First position.
            - pos2 (tuple of two ints): Second position.
        Outputs:
            - float: The heuristic cost using octile distance.
        Purpose: Calculates the heuristic cost using octile distance.
        How it works:
            - Uses the formula for octile distance to calculate the heuristic cost.

    convert_to_grid_coords(pos, surface_size, res):
        Inputs:
            - pos (tuple of two ints): Position to convert.
            - surface_size (list of two ints): Size of the surface in pixels.
            - res (int): Resolution of the surface.
        Outputs:
            - list of two ints: Converted position in grid coordinates.
        Purpose: Converts a position from pixel coordinates to grid coordinates.
        How it works:
            - Divides the position by the resolution to get the grid coordinates.

    is_within_bounds(target, surface_size=[5*12,5*8]):
        Inputs:
            - target (tuple of two ints): Position to check.
            - surface_size (list of two ints): Size of the surface in pixels.
        Outputs:
            - bool: True if the target is within bounds, False otherwise.
        Purpose: Checks if a position is within the bounds of the surface.
        How it works:
            - Checks if the target position is within the bounds of the surface size.

    Node:
        Attributes:
            - parent (Node): Parent node.
            - position (tuple of two ints): Position of the node.
            - g (int): Cost from the start node to this node.
            - h (int): Heuristic cost from this node to the end node.
            - f (int): Total cost of the node (g + h).
        Methods:
            - __eq__(other): Checks if two nodes are equal.
            - __repr__(): Represents the node as a string.
            - __lt__(other): Compares two nodes based on their f value.
            - __gt__(other): Compares two nodes based on their f value.

## algorithms/algorithms_expanding_aStar.py
#### Overview
This module handles pathfinding and obstacle avoidance for chess piece movement, including interactions between the main board and graveyard areas. It uses A* pathfinding with dynamic obstacle management to plan piece trajectories.

#### Coordinate Systems
1. **Chess Square Coordinates**: Standard 0-63 chess board representation
2. **Surface Coordinates**: Pixel-based coordinates for pathfinding
3. **Screen Coordinates**: Display coordinates for rendering

### Core Functions

#### Coordinate Conversion Functions
    square_to_surface_coord(sq: chess.Square, surface_size=[5*12,5*8])
        Inputs: 
            - sq: chess square (0-63)
            - surface_size: dimensions of playing surface
        Outputs: (x, y) surface coordinates
        Purpose: Converts chess board positions to pathfinding coordinates

    surface_to_square_coord(coord, surface_size=[5*12,5*8])
        Inputs: surface coordinates
        Outputs: chess square (0-63)
        Purpose: Converts pathfinding coordinates back to board positions

    screen_to_surface_coord(coord, screen_size, surface_size=[5*12,5*8])
        Inputs: screen pixel coordinates
        Outputs: surface coordinates
        Purpose: Maps display pixels to pathfinding space

    is_on_playing_surface(coord, surface_size=[5*12,5*8])
        Inputs: coordinates to check
        Outputs: boolean
        Purpose: Determines if coordinates are within main board bounds

#### Pathfinding Functions
    find_path(move: chess.Move, board: chess.Board)
        Inputs:
            - move: chess move to plan
            - board: current board state
        Outputs: List of path coordinates
        Purpose: Finds obstacle-free path for a chess move using A*

    get_obstacle_list(board: chess.Board, move, graveyard: Graveyard, ...)
        Inputs:
            - board: current board state
            - move: planned move
            - graveyard: graveyard instance
            - exclusion/inclusion lists
        Outputs: List of obstacle coordinates
        Purpose: Compiles all obstacles for pathfinding

#### Main Crowd Control Function
    crowd_control(board: chess.Board, move: chess.Move, graveyard: Graveyard, ...)
        Inputs:
            - board: current board state
            - move: attempted move
            - graveyard: graveyard instance
            - radius: search radius
            - check_interval: radius increment
            - surface_size: dimensions
            - log: logging flag
        Outputs: Dictionary containing:
            - moved_pieces_paths: paths for temporarily moved pieces
            - path: final main path
            - undo_moves: reversal paths
        Purpose: Main function that:
            1. Attempts direct path
            2. Identifies and temporarily moves blocking pieces
            3. Returns complete movement plan

### Helper Functions (Internal)

#### Movement Management
    _move_piece_between_surfaces(board, graveyard, from_square, to_square)
        Purpose: Handles piece transfers between board and graveyard
        Returns: Moved piece object

    _undo_all_moves(board, graveyard, state)
        Purpose: Reverts all temporary moves after pathfinding

#### Path Analysis
    _find_nearest_pieces(board, graveyard, path, state, move)
        Purpose: Identifies pieces blocking the path
        Returns: Tuple of (nearest_piece, nearest_square, nearest_pieces)

    _find_target_square(board, graveyard, path, state, nearest_square)
        Purpose: Finds valid relocation spots for blocking pieces
        Returns: Tuple of (target_square, better_square)

#### Utility Functions
    _check_timeout(state, log)
        Purpose: Monitors operation duration
        Returns: True if timeout reached

    _update_nearest_pieces(...)
        Purpose: Distance calculations for obstacle identification

    _evaluate_square(...)
        Purpose: Scores potential relocation squares

    _move_piece_and_record_path(...)
        Purpose: Executes and records temporary piece movements

### Algorithm Characteristics
1. **Dynamic Radius**: Expands search radius incrementally
2. **Temporary Relocation**: Can move blocking pieces to:
   - Empty board squares
   - Graveyard positions
3. **Time-aware**: Includes timeout protection
4. **Bidirectional**: Handles both board and graveyard interactions

### Usage Example
```python
# Initialize components
board = chess.Board()
graveyard = Graveyard()
move = chess.Move(chess.E2, chess.E4)  # Sample move

# Get movement plan
result = crowd_control(
    board=board,
    move=move,
    graveyard=graveyard,
    radius=3,
    check_interval=0.2
)

# Execute movements
if result:
    main_path = result["path"]
    temp_moves = result["moved_pieces_paths"]
    undo_paths = result["undo_moves"]
