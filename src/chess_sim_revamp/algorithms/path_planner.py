import numpy as np
import chess
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from typing import List, Tuple
from fen import generate_random_fen
import networkx as nx

class Piece:
    def __init__(self, piece_id: int, x: float, y: float, piece_type: str = 'P', color: str = 'w', diameter: float = 40.0):
        self.id = piece_id
        self.x = x
        self.y = y
        self.piece_type = piece_type
        self.color = color
        self.diameter = diameter
        self.radius = diameter / 2
        self.original_position = (x, y)
    
    def distance_to(self, other_piece) -> float:
        return np.sqrt((self.x - other_piece.x)**2 + (self.y - other_piece.y)**2)
    
    def collides_with(self, other_piece) -> bool:
        return self.distance_to(other_piece) < (self.radius + other_piece.radius)
    
    def move_to(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def move_by(self, dx: float, dy: float):
        self.x += dx
        self.y += dy
    
    def __repr__(self):
        return f"Piece(id={self.id}, x={self.x:.1f}, y={self.y:.1f})"

class Board:
    def __init__(self, width: int = 12, height: int = 8, square_size: float = 50.0):
        self.pychess_board = None
        self.width = width
        self.height = height
        self.square_size = square_size
        self.board_width = width * square_size
        self.board_height = height * square_size
        self.gy1_count = None
        self.gy2_count = None
        self.gy11_count = None
        self.gy12_count = None
        self.pieces = {} 
        self.captured_pieces = {'w': [], 'b': []}
        self.piece_colors = {
            'w': 'white',
            'b': 'black'
        }
        self.piece_symbols = {
            'P': '♟', 'N': '♞', 'B': '♝', 'R': '♜', 'Q': '♛', 'K': '♚',
            'p': '♙', 'n': '♘', 'b': '♗', 'r': '♖', 'q': '♕', 'k': '♔'
        }
        self.standard_piece_counts = {
            'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1,
            'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1, 'k': 1
        }
        self.piece_locations = {
            'active': {},
            'captured_w': {},
            'captured_b': {},
            'promotion': {
                'white_queen': (75, 375),
                'black_queen': (525, 25)
            }
        }
    
    def add_piece(self, piece_id: int, x: float, y: float, piece_type: str = 'P', color: str = 'w') -> Piece:
        piece = Piece(piece_id, x, y, piece_type, color)
        self.pieces[piece_id] = piece
        return piece
    
    def get_piece_at_position(self, x: float, y: float, tolerance: float = 1.0) -> Piece:
        for piece in self.pieces.values():
            if abs(piece.x - x) <= tolerance and abs(piece.y - y) <= tolerance:
                return piece
            
        for color in ['w', 'b']:
            for piece_info in self.piece_locations[f'captured_{color}'].values():
                if abs(piece_info['position'][0] - x) <= tolerance and abs(piece_info['position'][1] - y) <= tolerance:
                    return piece_info
                
        return None

    def place_from_fen(self, fen: str) -> None:
        self.pychess_board = chess.Board(fen)
        self.pieces.clear()
        self.captured_pieces = {'w': [], 'b': []}
        self.piece_locations = {
            'active': {},
            'captured_w': {},
            'captured_b': {},
            'promotion': {
                'white_queen': (75, 375),
                'black_queen': (525, 25)
            }
        }
        
        parts = fen.split()
        if len(parts) < 1:
            raise ValueError("Invalid FEN string")
        
        piece_placement = parts[0]
        rows = piece_placement.split('/')
        
        x_offset = (self.width - 8) * self.square_size / 2
        y_offset = (self.height - 8) * self.square_size / 2
        
        current_pieces = {k: 0 for k in self.standard_piece_counts.keys()}
        
        piece_id = 0
        for row_idx, row in enumerate(rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    color = 'w' if char.isupper() else 'b'
                    piece_type = char.upper()
                    
                    x = x_offset + col_idx * self.square_size + self.square_size / 2
                    y = y_offset + (7 - row_idx) * self.square_size + self.square_size / 2
                    
                    self.add_piece(piece_id, x, y, piece_type, color)
                    self.piece_locations['active'][piece_id] = {
                        'type': piece_type,
                        'color': color,
                        'position': (x, y)
                    }
                    current_pieces[char] += 1
                    piece_id += 1
                    col_idx += 1

        start_y_w = 375
        start_y_b = 25
        spacing_y = 50
        col_1_count = 0
        col_2_count = 1
        col_12_count = 0
        col_11_count = 1
        captured_id = 0

        for piece_type, count in self.standard_piece_counts.items():
            current_count = current_pieces.get(piece_type, 0)
            missing = count - current_count
            if missing > 0:
                color = 'w' if piece_type.isupper() else 'b'
                self.captured_pieces[color].extend([piece_type] * missing)
                
                for _ in range(missing):
                    if color == 'w':
                        if col_1_count <= 7:
                            x = 25  
                            y = start_y_w - col_1_count * spacing_y
                            col_1_count += 1
                        else:
                            x = 75 
                            y = start_y_w - col_2_count * spacing_y 
                            col_2_count += 1
                    else: 
                        if col_12_count <= 7:
                            x = 575  
                            y = start_y_b + col_12_count * spacing_y
                            col_12_count += 1
                        else:
                            x = 525  
                            y = start_y_b + col_11_count * spacing_y
                            col_11_count += 1
                
                    location_key = f'captured_{color}_{captured_id}'
                    self.piece_locations[f'captured_{color}'][location_key] = {
                        'type': piece_type,
                        'color': color,
                        'position': (x, y)
                    }
                    captured_id += 1
        
        self.gy1_count = col_1_count
        self.gy2_count = col_2_count
        self.gy11_count = col_11_count
        self.gy12_count = col_12_count
    
    def render(self) -> None:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw grid
        for i in range(self.width + 1):
            ax.axvline(x=i * self.square_size, color='gray', linestyle='-', alpha=0.3)
        for j in range(self.height + 1):
            ax.axhline(y=j * self.square_size, color='gray', linestyle='-', alpha=0.3)
        
        for piece in self.pieces.values():
            facecolor = 'white' if piece.color == 'w' else 'black'
            edgecolor = 'black' if piece.color == 'w' else 'white'
            
            circle = Circle((piece.x, piece.y), piece.radius, 
                          facecolor=facecolor, edgecolor=edgecolor, alpha=0.7)
            ax.add_patch(circle)
            
            symbol = self.piece_symbols.get(piece.piece_type.lower() if piece.color == 'b' else piece.piece_type, '')
            text_color = 'black' if piece.color == 'w' else 'white'
            ax.text(piece.x, piece.y, symbol, 
                   ha='center', va='center', color=text_color, fontsize=20)
        
        for color in ['w', 'b']:
            for piece_info in self.piece_locations[f'captured_{color}'].values():
                x, y = piece_info['position']
                facecolor = 'white' if piece_info['color'] == 'w' else 'black'
                edgecolor = 'black' if piece_info['color'] == 'w' else 'white'
                
                circle = Circle((x, y), self.square_size / 3, 
                              facecolor=facecolor, edgecolor=edgecolor, alpha=0.7)
                ax.add_patch(circle)
                
                symbol = self.piece_symbols.get(
                    piece_info['type'].lower() if piece_info['color'] == 'b' else piece_info['type'], '')
                text_color = 'black' if piece_info['color'] == 'w' else 'white'
                ax.text(x, y, symbol, ha='center', va='center', color=text_color, fontsize=16)
        
        for queen_info, pos in self.piece_locations['promotion'].items():
            x, y = pos
            is_white = 'white' in queen_info
            facecolor = 'white' if is_white else 'black'
            edgecolor = 'black' if is_white else 'white'
            symbol = self.piece_symbols['Q' if is_white else 'q']
            text_color = 'black' if is_white else 'white'
            
            circle = Circle((x, y), self.square_size / 3, 
                          facecolor=facecolor, edgecolor=edgecolor, alpha=0.7)
            ax.add_patch(circle)
            ax.text(x, y, symbol, ha='center', va='center', color=text_color, fontsize=16)
        
        ax.set_xlim(0, self.board_width)
        ax.set_ylim(0, self.board_height)
        ax.set_aspect('equal')
        ax.set_title('Chess Board with Captured Pieces')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        
        plt.grid(True)
        plt.show()

    def get_all_piece_locations(self):
        return self.piece_locations

    def print_piece_locations(self):
        print("\nActive Pieces:")
        for piece_id, info in self.piece_locations['active'].items():
            print(f"Piece {piece_id}: {info['type']} ({info['color']}) at position {info['position']}")
        
        print("\nCaptured White Pieces:")
        for piece_id, info in self.piece_locations['captured_w'].items():
            print(f"{piece_id}: {info['type']} at position {info['position']}")
        
        print("\nCaptured Black Pieces:")
        for piece_id, info in self.piece_locations['captured_b'].items():
            print(f"{piece_id}: {info['type']} at position {info['position']}")
        
        print("\nPromotion Pieces:")
        for piece_name, position in self.piece_locations['promotion'].items():
            print(f"{piece_name} at position {position}")

    def path_to_graveyard(self, x: float, y: float, tolerance: float = 1.0):
        piece = self.get_piece_at_position(x, y, tolerance)

        G = nx.Graph()
        G.add_node((x,y))
        grid_points = []
        for i in range(self.width):
            for j in range(self.height):
                grid_x = 25 + i * 50
                grid_y = 25 + j * 50
                grid_points.append((grid_x, grid_y))
        
        for point in grid_points:
            point_x, point_y = point

            if self.get_piece_at_position(point_x, point_y, 0) is None:
                G.add_node(point)
        
        for point in list(G.nodes()):
            point_x, point_y = point
            diagonal_weight = 2
            
            straight_directions = [
                (point_x + 50, point_y, 1),  # right
                (point_x - 50, point_y, 1),  # left
                (point_x, point_y + 50, 1),  # up
                (point_x, point_y - 50, 1)   # down
            ]
            
            diagonal_directions = [
                (point_x + 50, point_y + 50, diagonal_weight),  # up-right
                (point_x + 50, point_y - 50, diagonal_weight),  # down-right
                (point_x - 50, point_y + 50, diagonal_weight),  # up-left
                (point_x - 50, point_y - 50, diagonal_weight)   # down-left
            ]
            
            for adjacent_x, adjacent_y, weight in straight_directions + diagonal_directions:
                if (adjacent_x, adjacent_y) in G.nodes():
                    G.add_edge(point, (adjacent_x, adjacent_y), weight=weight)
        
        closest_point = None
        min_distance = float('inf')
        
        for point in G.nodes():
            point_x, point_y = point
            distance = ((point_x - x) ** 2 + (point_y - y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        if closest_point is None or closest_point not in G.nodes():
            return [] 
            
        try:
            distances = nx.single_source_dijkstra_path_length(G, closest_point, weight='weight')
            paths = nx.single_source_dijkstra_path(G, closest_point, weight='weight')

            # GRAVEYAD LOCATION PART
            target_point = None
            
            if piece:
                if piece.color == "w":
                    primary_x, backup_x = 25, 75
                else:
                    primary_x, backup_x = 575, 525
                
                primary_targets = [(point, distances[point]) for point in distances.keys() 
                                  if point[0] == primary_x]
                
                if primary_targets:
                    target_point = min(primary_targets, key=lambda x: x[1])[0]
                else:
                    backup_targets = [(point, distances[point]) for point in distances.keys() 
                                     if point[0] == backup_x]
                    if backup_targets:
                        target_point = min(backup_targets, key=lambda x: x[1])[0]

                if target_point:
                    path_to_target = paths[target_point]
                    return path_to_target

            return distances, paths
        except nx.NetworkXNoPath:
            return {}

    def coord_from_uci(self, uci: str) -> Tuple[int, int]:
        x = 25 + (ord(uci[0]) - ord('a')) * 50 + 100
        y = 25 + (int(uci[1]) - 1) * 50
        return (x, y)

    def move_piece_left_xmm(self, piece_id: int, xmm: float):
        piece = self.pieces[piece_id]
        piece.x -= xmm

    def move_piece_right_xmm(self, piece_id: int, xmm: float):
        piece = self.pieces[piece_id]
        piece.x += xmm

    def move_piece_up_ymm(self, piece_id: int, ymm: float):
        piece = self.pieces[piece_id]
        piece.y += ymm

    def move_piece_down_ymm(self, piece_id: int, ymm: float):
        piece = self.pieces[piece_id]
        piece.y -= ymm

    def move_piece_diagonal_xymm(self, piece_id: int, xmm: float, ymm: float):
        step_x = 0.1
        step_y = 0.1

        while abs(xmm) > 0 or abs(ymm) > 0:
            piece = self.pieces[piece_id]
            piece.x += step_x
            piece.y += step_y
            if abs(xmm) > 0:
                xmm -= step_x
            if abs(ymm) > 0:
                ymm -= step_y

    def move_piece_diagonal(self, piece_id: int, move: str):
        from_x, from_y = self.coord_from_uci(move[:2])
        to_x, to_y = self.coord_from_uci(move[2:])
        
        dx = to_x - from_x
        dy = to_y - from_y
        
        if dx > 0 and dy > 0:
            direction = "northeast"  # Up-right
        elif dx > 0 and dy < 0:
            direction = "southeast"  # Down-right
        elif dx < 0 and dy > 0:
            direction = "northwest"  # Up-left
        elif dx < 0 and dy < 0:
            direction = "southwest"  # Down-left
             
        # Get the piece to move
        piece = self.pieces[piece_id]

        current_x = from_x
        current_y = from_y

        # need to progress the piece in the direction of the move
        while current_x != to_x and current_y != to_y:
            piece_left = self.get_piece_at_position(piece.x - 50, piece.y)
            piece_right = self.get_piece_at_position(piece.x + 50, piece.y)
            piece_up = self.get_piece_at_position(piece.x, piece.y + 50)
            piece_down = self.get_piece_at_position(piece.x, piece.y - 50)

            if direction == "northeast":
                if piece_right is None:
                    current_x += 50
                    current_y += 50
                    piece.x += 50
                    piece.y += 50
                elif piece_up is None:
                    current_x += 50
                    current_y += 50
                    piece.x += 50
                    piece.y += 50
                else:
                    piece_up.x -= 5
                    piece_up.y += 5
                    piece_right.x += 5
                    piece_right.y -= 5
                    #Move piece diagonally to piece.x + 50, piece.y + 50
                    self.move_piece_diagonal_xymm(piece_id, 50, 50)
                    #Reset the original piece positions
                    piece_up.x += 5
                    piece_up.y -= 5
                    piece_right.x -= 5
                    piece_right.y += 5
            
            elif direction == "southeast":
                if piece_right is None:
                    current_x += 50
                    current_y -= 50
                    piece.x += 50
                    piece.y -= 50
                elif piece_down is None:
                    current_x += 50
                    current_y -= 50
                    piece.x += 50
                    piece.y -= 50
                else:
                    piece_down.x += 5
                    piece_down.y -= 5
                    piece_right.x -= 5
                    piece_right.y += 5
                    #Move piece diagonally to piece.x + 50, piece.y - 50
                    self.move_piece_diagonal_xymm(piece_id, 50, -50)
                    #Reset the original piece positions
                    piece_down.x -= 5
                    piece_down.y += 5
                    piece_right.x += 5
                    piece_right.y -= 5

            elif direction == "northwest":
                if piece_left is None:
                    current_x -= 50
                    current_y += 50
                    piece.x -= 50
                    piece.y += 50
                elif piece_up is None:
                    current_x -= 50
                    current_y += 50
                    piece.x -= 50
                    piece.y += 50
                else:
                    piece_up.x -= 5
                    piece_up.y += 5
                    piece_left.x += 5
                    piece_left.y -= 5
                    #Move piece diagonally to piece.x - 50, piece.y + 50
                    self.move_piece_diagonal_xymm(piece_id, -50, 50)
                    #Reset the original piece positions
                    piece_up.x += 5
                    piece_up.y -= 5
                    piece_left.x -= 5
                    piece_left.y += 5
            
            elif direction == "southwest":
                if piece_left is None:
                    current_x -= 50
                    current_y -= 50
                    piece.x -= 50
                    piece.y -= 50
                elif piece_down is None:
                    current_x -= 50
                    current_y -= 50
                    piece.x -= 50
                    piece.y -= 50
                else:
                    piece_down.x -= 5
                    piece_down.y += 5
                    piece_left.x += 5
                    piece_left.y -= 5
                    #Move piece diagonally to piece.x - 50, piece.y - 50
                    self.move_piece_diagonal_xymm(piece_id, -50, -50)
                    #Reset the original piece positions
                    piece_down.x += 5
                    piece_down.y -= 5
                    piece_left.x -= 5
                    piece_left.y += 5
                    
        print(f"Moving piece {piece_id} ({piece.piece_type}) diagonally {direction} from ({from_x}, {from_y}) to ({to_x}, {to_y})")
        
        piece.move_to(to_x, to_y)

    def move_knight(self, piece_id: int, move: str):
        from_x, from_y = self.coord_from_uci(move[:2])
        to_x, to_y = self.coord_from_uci(move[2:])
        
    
    def move_right(self, piece_id: int, move: str):
        to_x, _= self.coord_from_uci(move[2:])
    
        piece = self.pieces[piece_id]
        while piece.x != to_x:
                self.move_piece_right_xmm(piece_id, 50)

    def move_left(self, piece_id: int, move: str):
        to_x, _= self.coord_from_uci(move[2:])

        piece = self.pieces[piece_id]
        while piece.x != to_x:
            self.move_piece_left_xmm(piece_id, 50)

    def move_up(self, piece_id: int, move: str):
        _, to_y = self.coord_from_uci(move[2:])

        piece = self.pieces[piece_id]
        while piece.y != to_y:
            self.move_piece_up_ymm(piece_id, 50)

    def move_down(self, piece_id: int, move: str):
        _, to_y = self.coord_from_uci(move[2:])

        piece = self.pieces[piece_id]
        while piece.y != to_y:
            self.move_piece_down_ymm(piece_id, 50)

    def get_path_from_move(self, move: chess.Move) -> List[Tuple[int, int]]:
        pass
        
        

board = Board()
random_fen = generate_random_fen(total_pieces=18)
print(random_fen)
board.place_from_fen('2n1R3/P2b2Q1/1Brpppn1/p2Pb3/k2NN1K1/P1p1p2P/Pp1pP1PP/1qR5 w - - 0 1')
#print(board.get_piece_at_position(75,125))

# #Get List of moves for piece id 11
# moves = board.pychess_board.legal_moves
# print(moves)


path = board.path_to_graveyard(125,225)
print(path)


# board.move_piece_diagonal(11, 'a3c5')
board.render()

