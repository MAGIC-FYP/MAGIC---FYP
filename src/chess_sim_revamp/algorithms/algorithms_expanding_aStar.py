import algorithms.a_star as aStar
import chess
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

def get_obstacle_list(board: chess.Board, move, graveyard: Graveyard):
    obstacle_list = []
    from_square = move[0]
    to_square = move[1]
    for square in range(64):
        piece = board.piece_at(square)
        if piece and square_to_surface_coord(square) not in [from_square, to_square]:
            obstacle_list.append(square_to_surface_coord(square))
    for piece in graveyard.get_black_pieces_positions():
        obstacle_list.append(graveyard.get_surface_from_gy_coord(piece[0]))
    for piece in graveyard.get_white_pieces_positions():
        obstacle_list.append(graveyard.get_surface_from_gy_coord(piece[0]))
    return obstacle_list


def crowd_control(board: chess.Board, move: chess.Move, graveyard: Graveyard,radius, check_interval = 0.2, surface_size=[5*12,5*8]):
    moves = []
    moved_pieces = []
    unavailable_squares=[]
    moved_pieces_paths = []
    undo_moves = []
    r=1


    start = square_to_surface_coord(move.from_square)
    finish = square_to_surface_coord(move.to_square)
    unavailable_squares.append(start)
    unavailable_squares.append(finish)

    obstacle_list = get_obstacle_list(board, (start, finish), graveyard)

    while r<radius:
        try:
            path = aStar.astar_activate(start, goal= finish, radius = r, obstacle_list=obstacle_list)
            r=r+check_interval
        except:

            #find neerest piece to path
            nearest_piece = None
            nearest_square = None
            min_distance = float('inf')
            for square in range(64):
                piece = board.piece_at(square)
                if piece and square not in [move.from_square, move.to_square]:
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
            min_distance = float('inf')
            for square in range(64):
                if board.piece_at(square) is None and square_to_surface_coord(square) not in unavailable_squares:
                    for path_point in path:
                        for i in range(10):
                            point_along_line = (path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                                            path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9)
                            distance_to_path = ((point_along_line[0] - square_to_surface_coord(square)[0]) ** 2 + 
                                        (point_along_line[1] - square_to_surface_coord(square)[1]) ** 2) ** 0.5
                            if distance_to_path > 5:
                                distance = ((nearest_square[0] - square_to_surface_coord(square)[0]) ** 2 + (nearest_square[1] - square_to_surface_coord(square)[1]) ** 2) ** 0.5
                                if distance < min_distance:
                                    min_distance = distance
                                    target_square = square_to_surface_coord(square)

            for square in graveyard.get_empty_squares():
                if graveyard.get_surface_from_gy_coord(square) not in unavailable_squares:
                    for path_point in path:
                        for i in range(10):
                            point_along_line = (path_point[0] + (path[i % len(path)][0] - path_point[0]) * i / 9, 
                                            path_point[1] + (path[i % len(path)][1] - path_point[1]) * i / 9)
                            distance_to_path = ((point_along_line[0] - graveyard.get_surface_from_gy_coord(square)[0]) ** 2 + 
                                        (point_along_line[1] - graveyard.get_surface_from_gy_coord(square)[1]) ** 2) ** 0.5
                            if distance_to_path > 4:
                                distance = ((nearest_square[0] - graveyard.get_surface_from_gy_coord(square)[0]) ** 2 + (nearest_square[1] - graveyard.get_surface_from_gy_coord(square)[1]) ** 2) ** 0.5
                                if distance <= min_distance:
                                    min_distance = distance
                                    target_square = graveyard.get_surface_from_gy_coord(square)

            if target_square:
                #print(f"Target square for {nearest_piece} is at position {square_to_surface_coord(target_square)} at distance {min_distance:.2f}")
                obstacle_list = get_obstacle_list(board, (nearest_square, target_square), graveyard)
                moved_pieces_path = aStar.astar_activate(nearest_square, goal= target_square, radius = radius, obstacle_list=obstacle_list)
                
                
                if (surface_size[0]/6 < nearest_square[0]< surface_size[0] - surface_size[0]/6): 
                    if(surface_size[0]/6 < target_square[0]< surface_size[0] - surface_size[0]/6):
                        board.push(chess.Move(surface_to_square_coord(nearest_square), surface_to_square_coord(target_square)))
                        board.move_stack.pop()
                    else:
                        board.remove_piece_at(surface_to_square_coord(nearest_square))
                        graveyard.place_piece_at(target_square, nearest_piece)
                else:
                    if(surface_size[0]/6 < target_square[0]< surface_size[0] - surface_size[0]/6):
                        graveyard.remove_piece_at(nearest_square)
                        board.set_piece_at(surface_to_square_coord(target_square), nearest_piece)
                    else:
                        graveyard.remove_piece_at(nearest_square)
                        graveyard.place_piece_at(target_square, nearest_piece)
                
                moved_pieces.append((nearest_square, target_square))
                moved_pieces_paths.append(moved_pieces_path)
            else:
                raise("No target square found for the nearest piece.")

            obstacle_list = get_obstacle_list(board, (start, finish), graveyard)

        
    
    for i in range(len(moved_pieces)):

        if (surface_size[0]/6 < nearest_square[0]< surface_size[0] - surface_size[0]/6): 
            if(surface_size[0]/6 < target_square[0]< surface_size[0] - surface_size[0]/6):
                board.push(chess.Move(surface_to_square_coord(target_square), surface_to_square_coord(nearest_square)))
                board.move_stack.pop()
            else:
                graveyard.remove_piece_at(target_square)
                board.set_piece_at(surface_to_square_coord(nearest_square), nearest_piece)
        else:
            if(surface_size[0]/6 < target_square[0]< surface_size[0] - surface_size[0]/6):
                board.remove_piece_at(surface_to_square_coord(target_square))
                graveyard.place_piece_at(nearest_square, nearest_piece)
            else:
                graveyard.remove_piece_at(target_square)
                graveyard.place_piece_at(nearest_square, nearest_piece)

        reversed_path = moved_pieces_paths[i][::-1]
        undo_moves.append(reversed_path)

    return {"moved_pieces_paths": moved_pieces_paths, "path": path, "undo_moves": undo_moves}