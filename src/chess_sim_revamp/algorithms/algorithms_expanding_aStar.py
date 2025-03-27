import algorithms.a_star as aStar
import chess

def square_to_surface_coord(sq: chess.Square, surface_size=[5*12,5*8]):
    return (((sq % 8) + 2) * (surface_size[0] // 12)+(surface_size[1] / (8*2)), (sq // 8) * (surface_size[1] // 8)+(surface_size[1] / (8*2)))

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

def crowd_control(board: chess.Board, move: chess.Move, radius, check_interval = 0.2):
    moves = []
    moved_pieces = []
    moved_pieces_paths = []
    undo_moves = []
    r=radius/2

    obstacle_list = []
    for square in range(64):
        piece = board.piece_at(square)
        if piece and square not in [move.from_square, move.to_square]:
            obstacle_list.append(square_to_surface_coord(square))
    
    start = square_to_surface_coord(move.from_square)
    finish = square_to_surface_coord(move.to_square)

    while r<radius:
        try:
            path = aStar.astar_activate(start, goal= finish, radius = r, obstacle_list=obstacle_list)
        except:

            nearest_piece = None
            nearest_square = None
            min_distance = float('inf')
            for square in range(64):
                piece = board.piece_at(square)
                if piece and square not in [move.from_square, move.to_square]:
                    for path_point in path:
                        distance = ((path_point[0] - square_to_surface_coord(square)[0]) ** 2 + (path_point[1] - square_to_surface_coord(square)[1]) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            nearest_piece = piece
                            nearest_square = square
            if nearest_piece:
                #print(f"Nearest piece to path: {nearest_piece} at distance {min_distance:.2f} at position {square_to_surface_coord(nearest_square)}")
                pass           
            else:
                raise("No pieces found near the path.")
            
            if nearest_piece:
                target_square = None
                min_distance = float('inf')
                for square in range(64):
                    if board.piece_at(square) is None and square not in [move.from_square, move.to_square]:
                        distance = ((square_to_surface_coord(nearest_square)[0] - square_to_surface_coord(square)[0]) ** 2 + (square_to_surface_coord(nearest_square)[1] - square_to_surface_coord(square)[1]) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            target_square = square

                if target_square:
                    #print(f"Target square for {nearest_piece} is at position {square_to_surface_coord(target_square)} at distance {min_distance:.2f}")
                    obstacle_list = []
                    for square in range(64):
                        piece = board.piece_at(square)
                        if piece and square not in [nearest_square, target_square]:
                            obstacle_list.append(square_to_surface_coord(square))
                    moved_pieces_path = aStar.astar_activate(square_to_surface_coord(nearest_square), goal= square_to_surface_coord(target_square), radius = radius, obstacle_list=obstacle_list)
                    board.push(chess.Move(nearest_square, target_square))
                    board.move_stack.pop()
                    moved_pieces.append(chess.Move(nearest_square, target_square))
                    moved_pieces_paths.append(moved_pieces_path)
                else:
                    raise("No target square found for the nearest piece.")

            obstacle_list = []
            for square in range(64):
                piece = board.piece_at(square)
                if piece and square not in [move.from_square, move.to_square]:
                    obstacle_list.append(square_to_surface_coord(square))

        r=r+check_interval
    
    for i in range(len(moved_pieces)):
        board.push(chess.Move(moved_pieces[i].to_square, moved_pieces[i].from_square))
        board.move_stack.pop()
        reversed_path = moved_pieces_paths[i][::-1]
        undo_moves.append(reversed_path)

    return {"moved_pieces_paths": moved_pieces_paths, "path": path, "undo_moves": undo_moves}