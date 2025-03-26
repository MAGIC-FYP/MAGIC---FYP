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
    crowd_moves = []
    print(path)
    return path