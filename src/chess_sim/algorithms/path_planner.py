import numpy as np
import chess
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from typing import List, Tuple
#from fen import generate_random_fen
import networkx as nx
import yaml
import os

def load_config():
    """Load configuration from config.yml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

class Piece:
    def __init__(self, piece_id: int, x: float, y: float, piece_type: str = 'P', color: str = 'w', diameter: float = None):
        self.id = piece_id
        self.x = x
        self.y = y
        self.piece_type = piece_type
        self.color = color
        self.diameter = diameter
        self.radius = diameter / 2
        self.original_position = (x, y)
    
    def __repr__(self):
        return f"Piece(id={self.id}, x={self.x:.1f}, y={self.y:.1f})"

class Board:
    def __init__(self, width: int = 12, height: int = 8, square_size: float = None):
        # Load configuration
        self.config = load_config()
        path_config = self.config['models']['path_finding']
        
        self.pychess_board = None
        self.width = width
        self.height = height
        self.square_size = square_size if square_size is not None else path_config['square_size']
        self.piece_diameter = path_config['piece_diameter']
        self.express_channel_size = path_config['express_channel_size']
        self.board_width = width * self.square_size
        self.board_height = height * self.square_size
        
        # Calculate derived values from config
        self.half_square = self.square_size / 2
        self.piece_radius = self.piece_diameter / 2
        
        # Calculate graveyard and board positions
        self.chess_start_x = (self.width - 8) * self.square_size / 2
        self.chess_start_y = (self.height - 8) * self.square_size / 2
        
        # Graveyard positions (2 columns on each side)
        self.graveyard_left_col1 = self.half_square  # 25mm when square_size=50
        self.graveyard_left_col2 = self.square_size + self.half_square  # 75mm when square_size=50
        self.graveyard_right_col1 = self.board_width - self.half_square  # 575mm when square_size=50, width=12
        self.graveyard_right_col2 = self.board_width - self.square_size - self.half_square  # 525mm when square_size=50, width=12
        
        # Express channels (top and bottom)
        self.express_bottom_y = -self.express_channel_size
        self.express_top_y = self.board_height + self.express_channel_size
        
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
                'white_queen': (self.graveyard_left_col2, self.board_height - self.half_square),
                'black_queen': (self.graveyard_right_col2, self.half_square)
            }
        }
    
    def add_piece(self, piece_id: int, x: float, y: float, piece_type: str = 'P', color: str = 'w') -> Piece:
        piece = Piece(piece_id, x, y, piece_type, color, self.piece_diameter)
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
        
        for queen_info, pos in self.piece_locations['promotion'].items():
            if abs(pos[0] - x) <= tolerance and abs(pos[1] - y) <= tolerance:
                is_white = 'white' in queen_info
                return {
                    'type': 'Q',
                    'color': 'w' if is_white else 'b',
                    'position': pos
                }
                
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
                'white_queen': (self.graveyard_left_col1, self.board_height - self.half_square),
                'black_queen': (self.graveyard_right_col1, self.half_square)
            }
        }
        
        parts = fen.split()
        if len(parts) < 1:
            raise ValueError("Invalid FEN string")
        
        piece_placement = parts[0]
        rows = piece_placement.split('/')
        
        x_offset = self.chess_start_x
        y_offset = self.chess_start_y
        
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
                    
                    x = x_offset + col_idx * self.square_size + self.half_square
                    y = y_offset + (7 - row_idx) * self.square_size + self.half_square
                    
                    self.add_piece(piece_id, x, y, piece_type, color)
                    self.piece_locations['active'][piece_id] = {
                        'type': piece_type,
                        'color': color,
                        'position': (x, y)
                    }
                    current_pieces[char] += 1
                    piece_id += 1
                    col_idx += 1

        start_y_w = self.board_height - self.half_square
        start_y_b = self.half_square
        spacing_y = self.square_size
        col_1_count = 1
        col_2_count = 0
        col_12_count = 1
        col_11_count = 0
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
                            x = self.graveyard_left_col1  
                            y = start_y_w - col_1_count * spacing_y
                            col_1_count += 1
                        else:
                            x = self.graveyard_left_col2 
                            y = start_y_b + col_2_count * spacing_y 
                            col_2_count += 1
                    else: 
                        if col_12_count <= 7:
                            x = self.graveyard_right_col1  
                            y = start_y_b + col_12_count * spacing_y
                            col_12_count += 1
                        else:
                            x = self.graveyard_right_col2  
                            y = start_y_w - col_11_count * spacing_y
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

        for i in range(self.width + 1):
            ax.axvline(x=i * self.square_size, color='gray', linestyle='-', alpha=0.3)
        for j in range(self.height + 1):
            ax.axhline(y=j * self.square_size, color='gray', linestyle='-', alpha=0.3)
        
        for piece in self.pieces.values():
            facecolor = 'white' if piece.color == 'w' else 'black'
            edgecolor = 'black' if piece.color == 'w' else 'white'
            
            circle = Circle((piece.x, piece.y), self.piece_radius, 
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
                
                circle = Circle((x, y), self.piece_radius, 
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
            
            circle = Circle((x, y), self.piece_radius, 
                          facecolor=facecolor, edgecolor=edgecolor, alpha=0.7)
            ax.add_patch(circle)
            ax.text(x, y, symbol, ha='center', va='center', color=text_color, fontsize=16)
        
        ax.set_xlim(0, self.board_width)
        ax.set_ylim(0, self.board_height)
        ax.set_aspect('equal')
        ax.set_title('Chess Board with Captured Pieces')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        
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

    def create_movement_graph(self, start_x: float, start_y: float) -> Tuple[nx.Graph, Tuple[float, float]]:
        G = nx.Graph()
        G.add_node((start_x, start_y))
        grid_points = []
        
        for i in range(self.width):
            for j in range(self.height):
                grid_x = self.half_square + i * self.square_size
                grid_y = self.half_square + j * self.square_size
                grid_points.append((grid_x, grid_y))

        # Express Travel Channels
        for i in range(self.width):
            grid_points.append((self.half_square + i * self.square_size, self.express_bottom_y))
            grid_points.append((self.half_square + i * self.square_size, self.express_top_y))
        
        for point in grid_points:
            point_x, point_y = point
            if self.get_piece_at_position(point_x, point_y, 0) is None:
                G.add_node(point)
        
        for point in list(G.nodes()):
            point_x, point_y = point
            diagonal_weight = 4
            L_shape_weight = 10
            
            straight_directions = [
                (point_x + self.square_size, point_y, 1),  # right
                (point_x - self.square_size, point_y, 1),  # left
                (point_x, point_y + self.square_size, 1),  # up
                (point_x, point_y - self.square_size, 1)   # down
            ]
            
            diagonal_directions = [
                (point_x + self.square_size, point_y + self.square_size, diagonal_weight),  # up-right
                (point_x + self.square_size, point_y - self.square_size, diagonal_weight),  # down-right
                (point_x - self.square_size, point_y + self.square_size, diagonal_weight),  # up-left
                (point_x - self.square_size, point_y - self.square_size, diagonal_weight)   # down-left
            ]

            L_shape_directions = [  
                (point_x + 2*self.square_size, point_y + self.square_size, L_shape_weight),
                (point_x + 2*self.square_size, point_y - self.square_size, L_shape_weight),
                (point_x - 2*self.square_size, point_y + self.square_size, L_shape_weight),
                (point_x - 2*self.square_size, point_y - self.square_size, L_shape_weight),
                (point_x + self.square_size, point_y + 2*self.square_size, L_shape_weight),
                (point_x + self.square_size, point_y - 2*self.square_size, L_shape_weight),
                (point_x - self.square_size, point_y + 2*self.square_size, L_shape_weight),
                (point_x - self.square_size, point_y - 2*self.square_size, L_shape_weight),
            ]
            
            for adjacent_x, adjacent_y, weight in straight_directions + diagonal_directions + L_shape_directions:
                if (adjacent_x, adjacent_y) in G.nodes():
                    G.add_edge(point, (adjacent_x, adjacent_y), weight=weight)

            if point_y == self.half_square:
                G.add_edge(point, (point_x, self.express_bottom_y), weight=1)
            if point_y == self.board_height - self.half_square:
                G.add_edge(point, (point_x, self.express_top_y), weight=1)
        
        closest_point = None
        min_distance = float('inf')
        
        for point in G.nodes():
            point_x, point_y = point
            distance = ((point_x - start_x) ** 2 + (point_y - start_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        return G, closest_point

    def path_to_graveyard(self, x: float, y: float, tolerance: float = 1.0):
        piece = self.get_piece_at_position(x, y, tolerance)
        if not piece:
            return []

        G, closest_point = self.create_movement_graph(x, y)
        if closest_point is None or closest_point not in G.nodes():
            return []
            
        try:
            distances = nx.single_source_dijkstra_path_length(G, closest_point, weight='weight')
            paths = nx.single_source_dijkstra_path(G, closest_point, weight='weight')

            # Find target point in graveyard
            target_point = None
            
            if piece:
                if piece.color == "w":
                    # White pieces go to left side graveyard, highest possible position
                    primary_targets = [(point, distances[point]) for point in distances.keys() 
                                      if point[0] == self.graveyard_left_col1 and point[1] >= self.half_square and point[1] <= self.board_height - self.half_square]  # Regular graveyard
                    backup_targets = [(point, distances[point]) for point in distances.keys() 
                                     if point[0] == self.graveyard_left_col2 and point[1] >= self.half_square and point[1] <= self.board_height - self.half_square]   # Backup graveyard
                else:
                    # Black pieces go to right side graveyard, lowest possible position
                    primary_targets = [(point, distances[point]) for point in distances.keys() 
                                      if point[0] == self.graveyard_right_col1 and point[1] >= self.half_square and point[1] <= self.board_height - self.half_square]  # Regular graveyard
                    backup_targets = [(point, distances[point]) for point in distances.keys() 
                                     if point[0] == self.graveyard_right_col2 and point[1] >= self.half_square and point[1] <= self.board_height - self.half_square]  # Backup graveyard
                
                if primary_targets:
                    # For white pieces, get highest y-coordinate; for black, get lowest
                    target_point = max(primary_targets, key=lambda x: x[0][1])[0] if piece.color == "w" else min(primary_targets, key=lambda x: x[0][1])[0]
                elif backup_targets:
                    # Same logic for backup targets
                    target_point = min(backup_targets, key=lambda x: x[0][1])[0] if piece.color == "w" else max(backup_targets, key=lambda x: x[0][1])[0]
                else:
                    return []  # No valid graveyard location found

                if target_point:
                    path_to_target_mm = paths[target_point]
                    return [(point[0] / 10, point[1] / 10) for point in path_to_target_mm]
            
            return None, distances, paths
        except nx.NetworkXNoPath:
            return {}
    
    def visualize_graph(self, G: nx.Graph, start_point: Tuple[float, float] = None):
        plt.figure(figsize=(12, 8))
        
        pos = {node: node for node in G.nodes()}  # Use actual coordinates as positions
        nx.draw_networkx_edges(G, pos, alpha=0.5, width=1)
        
        node_colors = []
        for node in G.nodes():
            if start_point and node == start_point:
                node_colors.append('red')  # Highlight start point
            elif node[1] == self.express_bottom_y or node[1] == self.express_top_y:
                node_colors.append('green')  # Express travel channel points
            else:
                node_colors.append('blue')  # Regular grid points
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=100)
        
        labels = {node: f"({node[0]}, {node[1]})" for node in G.nodes() if node[1] == self.express_bottom_y or node[1] == self.express_top_y}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Movement Graph Visualization")
        plt.axis('equal')
        plt.show()

    def path_to_target(self, x: float, y: float, target_x: float, target_y: float) -> List[Tuple[float, float]]:
        G, closest_point = self.create_movement_graph(x, y)
        #self.visualize_graph(G, (x,y))
        if closest_point is None or closest_point not in G.nodes():
            return []
        
        distances = nx.single_source_dijkstra_path_length(G, closest_point, weight='weight')
        paths = nx.single_source_dijkstra_path(G, closest_point, weight='weight')

        target_point = (target_x, target_y)
        if target_point in distances:
            path_mm = paths[target_point]
            return [(point[0] / 10, point[1] / 10) for point in path_mm]
        return []

    def coord_from_uci(self, uci: str) -> Tuple[int, int]:
        x = self.half_square + (ord(uci[0]) - ord('a')) * self.square_size + (2*self.square_size)
        y = self.half_square + (int(uci[1]) - 1) * self.square_size 
        return (x, y)

    def process_path(self, path: List[Tuple[float, float]]):
        pass

    def simplify_path(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Simplify a path by merging parallel segments that are one after the other into a single long span.
        Args:
            path: List of path segments.
        Returns:
            Simplified path with merged parallel segments.
        """

        num_changes = 0
        path = path[0]
        simplified_path = [path[0]]
        while True:
            for i in range(1, len(path)-1):
                # Check if the current segment is parallel to the next one
                if (path[i][0] - path[i-1][0]) * (path[i+1][1] - path[i][1]) == (path[i][1] - path[i-1][1]) * (path[i+1][0] - path[i][0]):
                    # If parallel, merge the segments by removing the current point
                    simplified_path.append(path[i+1])
                    #print(f"merged {path[i-1]}, {path[i]} and {path[i+1]}")
                    num_changes += 1
                else:
                    # If not parallel, add the current point to the simplified path
                    simplified_path.append(path[i])
            # Add the last point of the original path to the simplified path
            if path[-1] != simplified_path[-1]:
                simplified_path.append(path[-1])
    
            if num_changes == 0:
                return [simplified_path]
            else:
                num_changes = 0
                path = simplified_path
                simplified_path = [path[0]]
        

    def get_full_path(self, move: str) -> List[Tuple[float, float]]:
        """
        This is the main function that builds the path for a move, handling regular moves, captures, and promotions.
        Args:
            move: UCI format move string (e.g., 'e2e4' for regular move, 'c7c8q' for promotion)
        Returns:
            List of path segments for pieces to be moved [[path_to_graveyard], [intermediate_moves],...., [path_to_target]]
        """
        # Handle promotion moves
        promotion = None
        if len(move) == 5:  # Promotion move (e.g., c7c8q)
            promotion = move[4].upper()
            move = move[:4]  # Remove promotion piece from move string
        
        from_x, from_y = self.coord_from_uci(move[:2])
        to_x, to_y = self.coord_from_uci(move[2:])

        # Handle promotion moves
        if promotion:
            # Send pawn to graveyard
            pawn = self.get_piece_at_position(from_x, from_y)
            path1 = self.path_to_graveyard(from_x, from_y)
            self.pieces[pawn.id].x = path1[-1][0]
            self.pieces[pawn.id].y = path1[-1][1]
            self.piece_locations['active'][pawn.id]['position'] = (path1[-1][0], path1[-1][1])

            # Move the promoted queen to the target position based on promotion colour
            if pawn.color == 'w':
                queen = self.get_piece_at_position(self.graveyard_left_col2, self.board_height - self.half_square)
                path2 = self.path_to_target(self.graveyard_left_col2, self.board_height - self.half_square, to_x, to_y)
                self.pieces[queen.id].x = to_x
                self.pieces[queen.id].y = to_y
                self.piece_locations['promotion']['white_queen'] = (to_x, to_y)
                self.piece_locations['active'][queen.id]['position'] = (to_x, to_y)
            else:
                queen = self.get_piece_at_position(self.graveyard_right_col2, self.half_square)
                path2 = self.path_to_target(self.graveyard_right_col2, self.half_square, to_x, to_y)
                self.pieces[queen.id].x = to_x
                self.pieces[queen.id].y = to_y
                self.piece_locations['promotion']['black_queen'] = (to_x, to_y)
                self.piece_locations['active'][queen.id]['position'] = (to_x, to_y)
        
            return [path1, path2]
        
        # Handle en passant moves
        if self.pychess_board.is_en_passant(chess.Move.from_uci(move)):
            pawn = self.get_piece_at_position(from_x, from_y)
            path1 = self.path_to_target(from_x, from_y, to_x, to_y)
            self.pieces[pawn.id].x = to_x
            self.pieces[pawn.id].y = to_y
            self.piece_locations['active'][pawn.id]['position'] = (to_x, to_y)

            captured_pawn = self.get_piece_at_position(to_x, from_y)
            path2 = self.path_to_graveyard(to_x, from_y)
            self.pieces[captured_pawn.id].x = path2[-1][0]
            self.pieces[captured_pawn.id].y = path2[-1][1]
            self.piece_locations['active'][captured_pawn.id]['position'] = (path2[-1][0], path2[-1][1])

            return [path1, path2]

        # Handle castling moves
        if self.pychess_board.is_castling(chess.Move.from_uci(move)):
            # Check if queen side or king side castling
            if move[2] == 'c':
                # Queen side castling 
                king_piece = self.get_piece_at_position(from_x, from_y)
                # Queen side rook position (a-file)
                queenside_rook_x = self.chess_start_x + self.half_square
                rook_piece = self.get_piece_at_position(queenside_rook_x, from_y)

                # King moves from e1 to c1 or e8 to c8
                path_1 = self.path_to_target(from_x, from_y, to_x, to_y) # King path
                self.pieces[king_piece.id].x = to_x
                self.pieces[king_piece.id].y = to_y
                self.piece_locations['active'][king_piece.id]['position'] = (to_x, to_y)

                # Rook moves from a1 to d1 or a8 to d8
                path_2 = self.path_to_target(queenside_rook_x, from_y, to_x + self.square_size, to_y) # Rook path
                self.pieces[rook_piece.id].x = to_x + self.square_size
                self.pieces[rook_piece.id].y = to_y
                self.piece_locations['active'][rook_piece.id]['position'] = (to_x + self.square_size, to_y)

                return [path_1, path_2]

            else:
                # King side castling
                king_piece = self.get_piece_at_position(from_x, from_y)
                # King side rook position (h-file)
                kingside_rook_x = self.chess_start_x + 7 * self.square_size + self.half_square
                rook_piece = self.get_piece_at_position(kingside_rook_x, from_y)

                # King moves from e1 to g1 or e8 to g8
                path_1 = self.path_to_target(from_x, from_y, to_x, to_y) # King path
                self.pieces[king_piece.id].x = to_x
                self.pieces[king_piece.id].y = to_y
                self.piece_locations['active'][king_piece.id]['position'] = (to_x, to_y)

                # Rook moves from h1 to f1 or h8 to f8
                path_2 = self.path_to_target(kingside_rook_x, from_y, to_x - self.square_size, to_y) # Rook path
                self.pieces[rook_piece.id].x = to_x - self.square_size
                self.pieces[rook_piece.id].y = to_y
                self.piece_locations['active'][rook_piece.id]['position'] = (to_x - self.square_size, to_y)

                return [path_1, path_2]

        # Check if there's a piece at the destination (i.e. is capture move?)
        captured_piece = self.get_piece_at_position(to_x, to_y)
        path = []

        if captured_piece:
            ##print("here")
            graveyard_path = self.path_to_graveyard(to_x, to_y)
            if graveyard_path:
                path.append(graveyard_path)
                #Update the piece location in the board to the last point in the graveyard path
                self.pieces[captured_piece.id].x = graveyard_path[-1][0]
                self.pieces[captured_piece.id].y = graveyard_path[-1][1]
                self.piece_locations['active'][captured_piece.id]['position'] = (graveyard_path[-1][0], graveyard_path[-1][1])
        
        
        path.append(self.path_to_target(from_x, from_y, to_x, to_y))
        return path
    
    def get_full_path_simpli(self, move: str) -> List[Tuple[float, float]]:
        path = self.get_full_path(move)
        #print(f"original path: {path}")
        path = self.simplify_path(path)
        #print(f"path: {path}")
        return path
        


if __name__ == "__main__":
    board = Board()
    board.place_from_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    print(board.pychess_board.is_castling(chess.Move.from_uci('e1c1')))
    #path = board.get_full_path('e1c1')
    #print(path)
    board.render()

