import algorithms.a_star as aStar
import chess
import time
import numpy as np
from models.graveyard import Graveyard



def square_to_surface_coord(sq: chess.Square, surface_size=[5*12,5*8]):
    return (((sq % 8) + 2) * (surface_size[0] // 12)+(surface_size[1] / (8*2)), (sq // 8) * (surface_size[1] // 8)+(surface_size[1] / (8*2)))

def surface_to_square_coord(coord, surface_size=[5*12,5*8]):
    x = (coord[0] - (surface_size[1] / (8*2))) * (12 / surface_size[0]) - 2
    y = (coord[1] - (surface_size[1] / (8*2))) * (8 / surface_size[1])
    return int(x) + int(y) * 8

def screen_to_surface_coord(coord, screen_size, surface_size=[5*12,5*8]):
    screen_size = (screen_size[0], screen_size[1]- screen_size[1]/9)
    return (coord[0] * (surface_size[0] / screen_size[0]), (coord[1] * (surface_size[1] / screen_size[1]))-5)

def surface_to_screen_coord(coord, screen_size, surface_size=[5*12,5*8]):
    adjusted_screen_size = (screen_size[0], screen_size[1] - screen_size[1]/8)
    return ((coord[0] * adjusted_screen_size[0] / surface_size[0]), ((coord[1]+5) * adjusted_screen_size[1] / surface_size[1]))

def is_on_playing_surface(coord, surface_size=[5*12,5*8]):
    t = (coord[0]-(surface_size[0]/6))
    return (0<t) and (t < ((surface_size[0]*2/3)))

def find_path(move: chess.Move, board: chess.Board):
    obstacle_list = []
    for square in range(64):
        piece = board.piece_at(square)
        if piece and square not in [move.from_square, move.to_square]:
            obstacle_list.append(square_to_surface_coord(square))


    start = square_to_surface_coord(move.from_square)
    finish = square_to_surface_coord(move.to_square)
    print(start,finish)
    path = aStar.astar_activate(start, goal= finish, radius = 2, obstacle_list=obstacle_list)
  
    print(path)
    return path

def get_obstacle_list(board: chess.Board, move, graveyard: Graveyard, points_to_exclude=[], points_to_include=[]):
    obstacle_list = []
    from_square = move[0]
    to_square = move[1]
    for square in range(64):
        piece = board.piece_at(square)
        coords = square_to_surface_coord(square)
        if piece and coords not in [from_square, to_square] and coords not in points_to_exclude:
            obstacle_list.append(coords)
    for piece in graveyard.get_black_pieces_positions():
        coords = graveyard.get_surface_from_gy_coord(piece[0])
        if coords not in points_to_exclude:
            obstacle_list.append(coords)
    for piece in graveyard.get_white_pieces_positions():
        coords = graveyard.get_surface_from_gy_coord(piece[0])
        if coords not in points_to_exclude:
            obstacle_list.append(coords)
    for point in points_to_include:
        obstacle_list.append(point)
    return obstacle_list


def crowd_control(board: chess.Board, move: chess.Move, graveyard: Graveyard, radius, 
                 check_interval=0.2, surface_size=[5*12,5*8], log=False):
    """Main function to handle crowd control around chess moves."""
    # Initialize data structures
    state = {
        'moved_pieces': [],
        'start': square_to_surface_coord(move.from_square),
        'finish': square_to_surface_coord(move.to_square),
        'unavailable_squares': [square_to_surface_coord(move.from_square), 
                               square_to_surface_coord(move.to_square)],
        'unavailable_pieces': [],
        'moved_pieces_paths': [],
        'undo_moves': [],
        'radius': radius,
        'r': 1,
        'close_piece_dist': (surface_size[0]/12) * np.sqrt(2),
        'piece_dist_tolerance': 0.2,
        'time_out': 10,
        'start_time': time.time()

    }
    
    start = state['start']
    finish = state['finish']
    obstacle_list = get_obstacle_list(board, (start, finish), graveyard)
    
    # Try direct path first
    try:
        path = aStar.astar_activate(start, goal=finish, radius=radius, obstacle_list=obstacle_list)
        return {"moved_pieces_paths": [], "path": path, "undo_moves": []}
    except:
        pass
    
    # Main pathfinding loop
    while state['r'] < radius:
        try:
            path = aStar.astar_activate(start, goal=finish, radius=state['r'], 
                                        obstacle_list=obstacle_list)
            state['r'] += check_interval
        except:
            if _check_timeout(state, log):
                return False
            
            # Find nearest pieces to path
            nearest_piece, nearest_square, nearest_pieces = _find_nearest_pieces(
                board, graveyard, path, state, move
            )
            
            if not nearest_piece:
                raise Exception("No pieces found near the path.")
            
            state['unavailable_squares'].append(nearest_square)
            
            print(f"nearest_pieces: {nearest_pieces}\n")
            # Find target square to move the piece to
            target_square, better_square = _find_target_square(
                board, graveyard, path, state, nearest_square
            )
            
            if target_square:
                if better_square:
                    target_square = better_square
                
                # Move the piece and record the path
                _move_piece_and_record_path(
                    board, graveyard, nearest_square, target_square, 
                    state, radius, start, finish
                )
            else:
                state['unavailable_pieces'].append(nearest_square)
            
            obstacle_list = get_obstacle_list(board, (start, finish), graveyard)
    
    # Undo all moves and record reversed paths
    _undo_all_moves(board, graveyard, state)
    
    return {
        "moved_pieces_paths": state['moved_pieces_paths'], 
        "path": path, 
        "undo_moves": state['undo_moves']
    }

# Helper functions

def _check_timeout(state, log):
    """Check if the operation has timed out."""
    if state['start_time'] + state['time_out'] <= time.time():
        if log:
            log.log(f"crowd_control time out: took longer then {state['time_out']} seconds")
        return True
    return False

def _find_nearest_pieces(board, graveyard, path, state, move):
    """Find pieces nearest to the given path."""
    nearest_piece = None
    nearest_pieces = []
    nearest_square = None
    min_distance = float('inf')
    
    # Check board pieces
    for square in range(64):
        piece = board.piece_at(square)
        if piece and square not in [move.from_square, move.to_square] and square_to_surface_coord(square) not in state['unavailable_pieces']:
            min_distance, nearest_piece, nearest_square, nearest_pieces = _update_nearest_pieces(
                path, square_to_surface_coord(square), piece, 
                min_distance, nearest_piece, nearest_square, nearest_pieces, 
                state['close_piece_dist'], state['piece_dist_tolerance']
            )
    
    # Check graveyard pieces
    for piece_type in ['black', 'white']:
        pieces = graveyard.get_black_pieces_positions() if piece_type == 'black' else graveyard.get_white_pieces_positions()
        for piece in pieces:
            if piece and graveyard.get_surface_from_gy_coord(piece[0]) not in state['unavailable_pieces']:
                surface_coord = graveyard.get_surface_from_gy_coord(piece[0])
                min_distance, nearest_piece, nearest_square, nearest_pieces = _update_nearest_pieces(
                    path, surface_coord, piece, 
                    min_distance, nearest_piece, nearest_square, nearest_pieces, 
                    state['close_piece_dist'], state['piece_dist_tolerance']
                )
    
    return nearest_piece, nearest_square, nearest_pieces

def _update_nearest_pieces(path, square_coord, piece, min_distance, 
                          nearest_piece, nearest_square, nearest_pieces, 
                          close_piece_dist, piece_dist_tolerance):
    """Update the nearest pieces list based on distance calculations."""
    for path_point in path:
        for i in range(10):
            point_along_line = (
                path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9
            )
            distance = ((point_along_line[0] - square_coord[0]) ** 2 + 
                       (point_along_line[1] - square_coord[1]) ** 2) ** 0.5
            
            if distance <= min_distance:
                min_distance = distance
                nearest_piece = piece
                nearest_square = square_coord
            
            if (close_piece_dist - piece_dist_tolerance <= distance <= close_piece_dist + piece_dist_tolerance) and (piece, square_coord) not in nearest_pieces:
                nearest_pieces.append((piece, square_coord))
    
    return min_distance, nearest_piece, nearest_square, nearest_pieces

def _find_target_square(board, graveyard, path, state, nearest_square):
    """Find a suitable target square to move a blocking piece to."""
    target_square = None
    better_square = None
    min_distance = float('inf')
    min_distance_better = float('inf')
    
    # Check board squares
    for square in range(64):
        surface_square = square_to_surface_coord(square)
        if (board.piece_at(square) is None) and (surface_square not in state['unavailable_squares']):
            min_distance, target_square, min_distance_better, better_square = _evaluate_square(
                path, surface_square, nearest_square, min_distance, target_square, 
                min_distance_better, better_square, board, graveyard, 
                state['unavailable_squares'], state['radius'], state['start'], state['finish']
            )
    
    # Check graveyard squares
    for square in graveyard.get_empty_squares():
        surface_square = graveyard.get_surface_from_gy_coord(square)
        if surface_square not in state['unavailable_squares']:
            min_distance, target_square, min_distance_better, better_square = _evaluate_square(
                path, surface_square, nearest_square, min_distance, target_square, 
                min_distance_better, better_square, board, graveyard, 
                state['unavailable_squares'], state['radius'], state['start'], state['finish']
            )
    
    return target_square, better_square

def _evaluate_square(path, surface_square, nearest_square, min_distance, target_square, 
                    min_distance_better, better_square, board, graveyard, 
                    unavailable_squares, radius, start, finish):
    """Evaluate a potential target square for moving a piece."""
    for path_point in path:
        for i in range(10):
            point_along_line = (
                path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9
            )
            distance_to_path = ((point_along_line[0] - surface_square[0]) ** 2 + 
                              (point_along_line[1] - surface_square[1]) ** 2) ** 0.5
            
            if distance_to_path > 5:
                distance = ((nearest_square[0] - surface_square[0]) ** 2 + 
                           (nearest_square[1] - surface_square[1]) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    target_square = surface_square
    
    try:
        if distance < min_distance_better:
            obstacle_list = get_obstacle_list(
                board, (start, finish), graveyard, 
                points_to_exclude=[nearest_square], 
                points_to_include=[surface_square]
            )
            path = aStar.astar_activate(
                start, goal=finish, radius=radius, 
                obstacle_list=obstacle_list
            )
            if path:
                min_distance_better = distance
                better_square = surface_square
    except:
        pass
    
    return min_distance, target_square, min_distance_better, better_square

def _move_piece_and_record_path(board, graveyard, nearest_square, target_square, 
                              state, radius, start, finish):
    """Move a piece to a target square and record the path."""
    try:
        obstacle_list = get_obstacle_list(
            board, (nearest_square, target_square), graveyard, 
            points_to_include=[start, finish]
        )
        moved_pieces_path = aStar.astar_activate(
            nearest_square, goal=target_square, radius=radius, 
            obstacle_list=obstacle_list
        )
    except:
        state['unavailable_pieces'].append(nearest_square)
        return
    
    # Move the piece between board and graveyard
    moved_piece = _move_piece_between_surfaces(
        board, graveyard, nearest_square, target_square
    )
    
    # Record the move
    state['moved_pieces'].append((nearest_square, target_square, moved_piece))
    state['moved_pieces_paths'].append(moved_pieces_path)

def _move_piece_between_surfaces(board, graveyard, from_square, to_square):
    """Move a piece between board and graveyard surfaces."""
    if is_on_playing_surface(from_square):
        moved_piece = board.piece_at(surface_to_square_coord(from_square)) 
        if is_on_playing_surface(to_square):
            board.remove_piece_at(surface_to_square_coord(from_square))
            board.set_piece_at(surface_to_square_coord(to_square), moved_piece)
        else:
            board.remove_piece_at(surface_to_square_coord(from_square))
            graveyard.place_piece_at(to_square, moved_piece)
    else:
        moved_piece = graveyard.piece_at(from_square)
        if is_on_playing_surface(to_square):
            graveyard.remove_piece_at(from_square)
            board.set_piece_at(surface_to_square_coord(to_square), moved_piece)
        else:
            graveyard.remove_piece_at(from_square)
            graveyard.place_piece_at(to_square, moved_piece)
    return moved_piece

def _undo_all_moves(board, graveyard, state):
    """Undo all temporary moves made during pathfinding."""
    for i in range(len(state['moved_pieces']) - 1, -1, -1):
        nearest_square = state['moved_pieces'][i][0]
        target_square = state['moved_pieces'][i][1]
        piece = state['moved_pieces'][i][2]
        
        if is_on_playing_surface(nearest_square):
            if is_on_playing_surface(target_square):
                board.remove_piece_at(surface_to_square_coord(target_square))
                board.set_piece_at(surface_to_square_coord(nearest_square), piece)
            else:
                graveyard.remove_piece_at(target_square)
                board.set_piece_at(surface_to_square_coord(nearest_square), piece)
        else:
            if is_on_playing_surface(target_square):
                board.remove_piece_at(surface_to_square_coord(target_square))
                graveyard.place_piece_at(nearest_square, piece)
            else:
                graveyard.remove_piece_at(target_square)
                graveyard.place_piece_at(nearest_square, piece)
        
        reversed_path = state['moved_pieces_paths'][i][::-1]
        state['undo_moves'].append(reversed_path)