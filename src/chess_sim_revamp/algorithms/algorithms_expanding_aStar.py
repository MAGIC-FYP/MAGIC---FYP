import algorithms.a_star as aStar
import chess
import time
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


def crowd_control(board: chess.Board, move: chess.Move, graveyard: Graveyard,radius, check_interval = 0.2, surface_size=[5*12,5*8], log=False):
    moves = []
    moved_pieces = []
    unavailable_squares=[]
    unavailable_pieces = []
    moved_pieces_paths = []
    undo_moves = []
    r=1
    time_out = 10

    start = square_to_surface_coord(move.from_square)
    finish = square_to_surface_coord(move.to_square)
    unavailable_squares.append(start)
    unavailable_squares.append(finish)

    obstacle_list = get_obstacle_list(board, (start, finish), graveyard)
    start_time = time.time()
    while r<radius:
        try:
            path = aStar.astar_activate(start, goal= finish, radius = r, obstacle_list=obstacle_list)
            r=r+check_interval
        except:
            if start_time+time_out <= time.time():
                log.log(f"crowd_control time out: took longer then {time_out} seconds")
                return False
            #find neerest piece to path
            nearest_piece = None
            nearest_square = None
            min_distance = float('inf')
            for square in range(64):
                piece = board.piece_at(square)
                if piece and square not in [move.from_square, move.to_square] and square_to_surface_coord(square) not in unavailable_pieces:
                    for path_point in path:
                        for i in range(10):
                            point_along_line = (path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                                               path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9)
                            distance = ((point_along_line[0] - square_to_surface_coord(square)[0]) ** 2 + 
                                        (point_along_line[1] - square_to_surface_coord(square)[1]) ** 2) ** 0.5
                            if distance <= min_distance:
                                min_distance = distance
                                nearest_piece = piece
                                nearest_square = square_to_surface_coord(square)

            for piece in graveyard.get_black_pieces_positions():
                if piece and graveyard.get_surface_from_gy_coord(piece[0]) not in unavailable_pieces:
                    for path_point in path:
                        distance = ((path_point[0] - graveyard.get_surface_from_gy_coord(piece[0])[0]) ** 2 + (path_point[1] - graveyard.get_surface_from_gy_coord(piece[0])[1]) ** 2) ** 0.5
                        if distance <= min_distance:
                                min_distance = distance
                                nearest_piece = piece
                                nearest_square = graveyard.get_surface_from_gy_coord(piece[0])

            #also check white graveyard pieces
            for piece in graveyard.get_white_pieces_positions():
                for path_point in path:
                    distance = ((path_point[0] - graveyard.get_surface_from_gy_coord(piece[0])[0]) ** 2 + (path_point[1] - graveyard.get_surface_from_gy_coord(piece[0])[1]) ** 2) ** 0.5
                    if distance < min_distance:
                            min_distance = distance
                            nearest_piece = piece
                            nearest_square = graveyard.get_surface_from_gy_coord(piece[0])

            if nearest_piece:
                unavailable_squares.append(nearest_square)
                pass           
            else:
                raise("No pieces found near the path.")
            
            target_square = None
            better_square = None
            min_distance = float('inf')
            min_distance_better = float('inf')
            for square in range(64):
                surface_square = square_to_surface_coord(square)
                if (board.piece_at(square) is None) and (surface_square not in unavailable_squares):

                    for path_point in path:
                        for i in range(10):
                            point_along_line = (path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                                            path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9)
                            distance_to_path = ((point_along_line[0] - surface_square[0]) ** 2 + 
                                        (point_along_line[1] - surface_square[1]) ** 2) ** 0.5
                            if distance_to_path > 5:
                                distance = ((nearest_square[0] - surface_square[0]) ** 2 + (nearest_square[1] - surface_square[1]) ** 2) ** 0.5
                                if distance < min_distance:
                                    min_distance = distance
                                    target_square = surface_square
                    try:
                        if distance < min_distance_better:
                            obstacle_list = get_obstacle_list(board, (start, finish), graveyard, points_to_exclude= [nearest_square], points_to_include= [square_to_surface_coord(square)])
                            path = aStar.astar_activate(start, goal= finish, radius = radius, obstacle_list=obstacle_list)
                            if path:
                                min_distance_better = distance
                                better_square = surface_square
                    except:
                        pass

            for square in graveyard.get_empty_squares():
                surface_square = graveyard.get_surface_from_gy_coord(square)
                if surface_square not in unavailable_squares:
                    for path_point in path:
                        for i in range(10):
                            point_along_line = (path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                                            path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9)
                            distance_to_path = ((point_along_line[0] - surface_square[0]) ** 2 + 
                                        (point_along_line[1] - surface_square[1]) ** 2) ** 0.5
                            if distance_to_path > 4:
                                distance = ((nearest_square[0] - surface_square[0]) ** 2 + (nearest_square[1] - surface_square[1]) ** 2) ** 0.5
                                if distance <= min_distance:
                                    min_distance = distance
                                    target_square = surface_square
                    try:
                        if distance < min_distance_better:
                            obstacle_list = get_obstacle_list(board, (start, finish), graveyard, points_to_exclude= [nearest_square], points_to_include= [square_to_surface_coord(square)])
                            path = aStar.astar_activate(start, goal= finish, radius = radius, obstacle_list=obstacle_list)
                            if path:
                                min_distance_better = distance
                                better_square = surface_square
                    except:
                        pass

            
            if target_square:
                if better_square:
                    target_square = better_square

                #print(f"Target square for {nearest_piece} is at position {square_to_surface_coord(target_square)} at distance {min_distance:.2f}")
                try:
                    obstacle_list = get_obstacle_list(board, (nearest_square, target_square), graveyard, points_to_include= [start, finish])
                    moved_pieces_path = aStar.astar_activate(nearest_square, goal= target_square, radius = radius, obstacle_list=obstacle_list)
                except:
                    unavailable_pieces.append(nearest_square)
                    continue
                
                
                if is_on_playing_surface(nearest_square):
                    moved_piece = board.piece_at(surface_to_square_coord(nearest_square)) 
                    if is_on_playing_surface(target_square):
                        board.remove_piece_at(surface_to_square_coord(nearest_square))
                        board.set_piece_at(surface_to_square_coord(target_square), moved_piece)
                    else:
                        board.remove_piece_at(surface_to_square_coord(nearest_square))
                        graveyard.place_piece_at(target_square, moved_piece)
                else:
                    moved_piece = graveyard.piece_at(nearest_square)
                    if is_on_playing_surface(target_square):
                        graveyard.remove_piece_at(nearest_square)
                        board.set_piece_at(surface_to_square_coord(target_square), moved_piece)
                    else:
                        graveyard.remove_piece_at(nearest_square)
                        graveyard.place_piece_at(target_square, moved_piece)
                
                moved_pieces.append((nearest_square, target_square, moved_piece))
                moved_pieces_paths.append(moved_pieces_path)
            else:
                unavailable_pieces.append(nearest_square)

            obstacle_list = get_obstacle_list(board, (start, finish), graveyard)

        
    
    for i in range(len(moved_pieces) - 1, -1, -1): 

        nearest_square = moved_pieces[i][0]
        target_square = moved_pieces[i][1]
        piece = moved_pieces[i][2]
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

        reversed_path = moved_pieces_paths[i][::-1]
        undo_moves.append(reversed_path)

    return {"moved_pieces_paths": moved_pieces_paths, "path": path, "undo_moves": undo_moves}