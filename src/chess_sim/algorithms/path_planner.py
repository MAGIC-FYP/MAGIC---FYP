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

    def create_movement_graph(self, start_x: float, start_y: float, exclude_positions: List[Tuple[float, float]] = None, include_positions: List[Tuple[float, float]] = None) -> Tuple[nx.Graph, Tuple[float, float]]:
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
        
        # Add graveyard positions as potential nodes
        graveyard_positions = []
        for y in range(self.height):
            y_pos = self.half_square + y * self.square_size
            graveyard_positions.extend([
                (self.graveyard_left_col1, y_pos),
                (self.graveyard_left_col2, y_pos),
                (self.graveyard_right_col1, y_pos),
                (self.graveyard_right_col2, y_pos)
            ])
        grid_points.extend(graveyard_positions)
        
        # Handle dynamic position tracking
        if exclude_positions is None:
            exclude_positions = []
        if include_positions is None:
            include_positions = []
        
        # Debug: show graveyard positions if positions are being tracked
        if len(exclude_positions) > 0 or len(include_positions) > 0:
            print(f"Graveyard columns: gy1={self.graveyard_left_col1}, gy2={self.graveyard_left_col2}, gy12={self.graveyard_right_col1}, gy11={self.graveyard_right_col2}")
            print(f"Total graveyard positions added: {len(graveyard_positions)}")
        
        debug_info = {
            'total_grid_points': len(grid_points),
            'nodes_added': 0,
            'excluded_count': 0,
            'piece_blocked_count': 0,
            'included_override_count': 0
        }
        
        for point in grid_points:
            point_x, point_y = point
            
            # Check if position is excluded (newly occupied by previous moves)
            is_excluded = any(abs(point_x - ex_x) < 1 and abs(point_y - ex_y) < 1 for ex_x, ex_y in exclude_positions)
            
            # Check if position is explicitly included (newly freed by previous moves)
            is_included = any(abs(point_x - inc_x) <= 1.0 and abs(point_y - inc_y) <= 1.0 for inc_x, inc_y in include_positions)
            
            # Check for existing pieces at this position
            has_piece = self.get_piece_at_position(point_x, point_y, 0) is not None
            
            # Track debug info
            if is_excluded:
                debug_info['excluded_count'] += 1
            if has_piece and not is_included:
                debug_info['piece_blocked_count'] += 1
            if is_included:
                debug_info['included_override_count'] += 1
            
            # Include node if:
            # 1. Explicitly included (overrides everything else)
            # 2. OR (not excluded AND no piece there)
            should_include = is_included or (not is_excluded and not has_piece)
            
            # Special case: if included, override piece presence
            if is_included and has_piece:
                should_include = True
                
            if should_include:
                G.add_node(point)
                debug_info['nodes_added'] += 1
        
        # Print debug info occasionally
        if len(exclude_positions) > 5:  # Only show detailed debug for later moves
            print(f"Graph debug: {debug_info['nodes_added']}/{debug_info['total_grid_points']} nodes added")
            print(f"  Excluded: {debug_info['excluded_count']}, Piece blocked: {debug_info['piece_blocked_count']}, Include override: {debug_info['included_override_count']}")
            print(f"  Include positions: {include_positions[:3]}..." if len(include_positions) > 3 else f"  Include positions: {include_positions}")
            print(f"  Exclude positions: {exclude_positions[:3]}..." if len(exclude_positions) > 3 else f"  Exclude positions: {exclude_positions}")
        
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

    def path_to_graveyard(self, x: float, y: float, tolerance: float = 1.0, exclude_positions: List[Tuple[float, float]] = None, include_positions: List[Tuple[float, float]] = None):
        piece = self.get_piece_at_position(x, y, tolerance)
        if not piece:
            return []

        G, closest_point = self.create_movement_graph(x, y, exclude_positions, include_positions)
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

    def path_to_target(self, x: float, y: float, target_x: float, target_y: float, exclude_positions: List[Tuple[float, float]] = None, include_positions: List[Tuple[float, float]] = None) -> List[Tuple[float, float]]:
        G, closest_point = self.create_movement_graph(x, y, exclude_positions, include_positions)
        self.visualize_graph(G, (x,y))  # Comment out for cleaner output
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

    def get_l_edge_type(self, x1: float, y1: float, x2: float, y2: float) -> str:
        """
        Identify which of the 8 L-edge types is being used.
        Args:
            x1, y1: Starting point (in mm)
            x2, y2: Ending point (in mm)
        Returns:
            String identifier for the L-edge type
        """
        dx = x2 - x1  # Signed difference
        dy = y2 - y1  # Signed difference
        
        # Map to the 8 L-edge types
        if abs(dx) == 2 * self.square_size and abs(dy) == self.square_size:
            if dx > 0 and dy > 0:
                return "R2U1"  # Right 2, Up 1
            elif dx > 0 and dy < 0:
                return "R2D1"  # Right 2, Down 1
            elif dx < 0 and dy > 0:
                return "L2U1"  # Left 2, Up 1
            elif dx < 0 and dy < 0:
                return "L2D1"  # Left 2, Down 1
        elif abs(dx) == self.square_size and abs(dy) == 2 * self.square_size:
            if dx > 0 and dy > 0:
                return "R1U2"  # Right 1, Up 2
            elif dx > 0 and dy < 0:
                return "R1D2"  # Right 1, Down 2
            elif dx < 0 and dy > 0:
                return "L1U2"  # Left 1, Up 2
            elif dx < 0 and dy < 0:
                return "L1D2"  # Left 1, Down 2
        
        return "UNKNOWN"   

    def process_l_edges(self, path: List[Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
        """
        Process a path and split it at L-edges, inserting placeholder paths.
        Args:
            path: A single path as a list of coordinate tuples
        Returns:
            List of path segments with placeholders around L-edges
        """
        if not path or len(path) < 2:
            return [path]
        
        result = []
        current_segment = [path[0]]
        
        for i in range(len(path) - 1):
            # Convert from cm to mm for comparison
            x1, y1 = path[i][0] * 10, path[i][1] * 10
            x2, y2 = path[i+1][0] * 10, path[i+1][1] * 10
            
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            # Check if this is an L-shaped edge
            is_l_edge = (dx == 2 * self.square_size and dy == self.square_size) or \
                        (dx == self.square_size and dy == 2 * self.square_size)
            
            if is_l_edge:
                # Add the segment before the L-edge (if it has more than just the starting point)
                l_edge_type = self.get_l_edge_type(x1, y1, x2, y2)

                x_delta = 7.5
                y_delta = 7.5

                pos_dict = {
                    "R2U1": [(x1 + self.square_size, y1 + self.square_size),(x1 + self.square_size, y1)],
                    "R2D1": [(x1 + self.square_size, y1 - self.square_size),(x1 + self.square_size, y1)],
                    "L2U1": [(x1 - self.square_size, y1 + self.square_size),(x1 - self.square_size, y1)],
                    "L2D1": [(x1 - self.square_size, y1 - self.square_size),(x1 - self.square_size, y1)],
                    "R1U2": [(x1 + self.square_size, y1 + self.square_size),(x1, y1 + self.square_size)],
                    "R1D2": [(x1 + self.square_size, y1 - self.square_size),(x1, y1 - self.square_size)],
                    "L1U2": [(x1 - self.square_size, y1 + self.square_size),(x1, y1 + self.square_size)],
                    "L1D2": [(x1 - self.square_size, y1 - self.square_size),(x1, y1 - self.square_size)]
                }

                delta_dict = {
                    "R2U1": [(x1 + self.square_size - x_delta , y1 + self.square_size + y_delta),(x1 + self.square_size + x_delta, y1 - y_delta)],
                    "R2D1": [(x1 + self.square_size + x_delta , y1 - self.square_size + y_delta),(x1 + self.square_size - x_delta, y1 + y_delta)],
                    "L2U1": [(x1 - self.square_size + x_delta, y1 + self.square_size + y_delta),(x1 - self.square_size - x_delta, y1 - y_delta)],
                    "L2D1": [(x1 - self.square_size + x_delta, y1 - self.square_size - y_delta),(x1 - self.square_size - x_delta, y1 + y_delta)],
                    "R1U2": [(x1 + self.square_size + x_delta, y1 + self.square_size - y_delta),(x1 - x_delta, y1 + self.square_size + y_delta)],
                    "R1D2": [(x1 + self.square_size + x_delta, y1 - self.square_size + y_delta),(x1 - x_delta, y1 - self.square_size - y_delta)],
                    "L1U2": [(x1 - self.square_size - x_delta, y1 + self.square_size - y_delta),(x1 + x_delta, y1 + self.square_size + y_delta)],
                    "L1D2": [(x1 - self.square_size - x_delta, y1 - self.square_size + y_delta),(x1 + x_delta, y1 - self.square_size - y_delta)]
                }

                piece1 = (pos_dict[l_edge_type][0][0]/10, pos_dict[l_edge_type][0][1]/10) 
                piece2 = (pos_dict[l_edge_type][1][0]/10, pos_dict[l_edge_type][1][1]/10)

                piece1_new = (delta_dict[l_edge_type][0][0]/10, delta_dict[l_edge_type][0][1]/10)
                piece2_new = (delta_dict[l_edge_type][1][0]/10, delta_dict[l_edge_type][1][1]/10)

                if len(current_segment) > 1:
                    result.append(current_segment[:-1])  # Don't include the L-edge starting point
                
                # Insert: [new_path1], [new_path2], [L-edge segment], [new_path3], [new_path4]
                result.extend([
                    [piece1, piece1_new],  # Make Space
                    [piece2, piece2_new],  # Make Space
                    [path[i], path[i+1]],  # Just the L-edge itself
                    [piece1_new, piece1],  # Undo 
                    [piece2_new, piece2]   # Undo
                ])
                
                # Start new segment from the point after the L-edge
                current_segment = [path[i+1]]
            else:
                # Regular edge, continue building current segment
                current_segment.append(path[i+1])
        
        # Add the final segment if it has content beyond just the starting point
        if len(current_segment) > 1:
            result.append(current_segment)
        elif not result:
            # If no L-edges were found, return the original path
            result.append(path)
        
        return result

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
        
        # Process each path for L-edges
        processed_paths = []
        for single_path in path:
            processed_paths.extend(self.process_l_edges(single_path))
        
        return processed_paths

        #return path
    
    def get_full_path_simpli(self, move: str) -> List[Tuple[float, float]]:
        path = self.get_full_path(move)
        #print(f"original path: {path}")
        path = self.simplify_path(path)
        #print(f"path: {path}")
        return path

    def get_original_positions(self) -> dict:
        """
        Get the original starting positions for all pieces in standard chess setup.
        Returns a dictionary mapping piece types and colors to their original positions.
        """
        original_positions = {}
        
        # Calculate board offsets
        x_offset = self.chess_start_x
        y_offset = self.chess_start_y
        
        # White pieces (bottom ranks)
        # White pawns on rank 2
        for file_idx in range(8):
            x = x_offset + file_idx * self.square_size + self.half_square
            y = y_offset + 1 * self.square_size + self.half_square  # Rank 2
            original_positions[f'w_pawn_{file_idx}'] = (x, y)
        
        # White pieces on rank 1
        piece_order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for file_idx, piece_type in enumerate(piece_order):
            x = x_offset + file_idx * self.square_size + self.half_square
            y = y_offset + 0 * self.square_size + self.half_square  # Rank 1
            
            # Handle multiple pieces of same type
            if piece_type in ['R', 'N', 'B']:
                count = sum(1 for i in range(file_idx) if piece_order[i] == piece_type)
                original_positions[f'w_{piece_type.lower()}_{count}'] = (x, y)
            else:
                original_positions[f'w_{piece_type.lower()}'] = (x, y)
        
        # Black pieces (top ranks)
        # Black pawns on rank 7
        for file_idx in range(8):
            x = x_offset + file_idx * self.square_size + self.half_square
            y = y_offset + 6 * self.square_size + self.half_square  # Rank 7
            original_positions[f'b_pawn_{file_idx}'] = (x, y)
        
        # Black pieces on rank 8
        for file_idx, piece_type in enumerate(piece_order):
            x = x_offset + file_idx * self.square_size + self.half_square
            y = y_offset + 7 * self.square_size + self.half_square  # Rank 8
            
            # Handle multiple pieces of same type
            if piece_type in ['R', 'N', 'B']:
                count = sum(1 for i in range(file_idx) if piece_order[i] == piece_type)
                original_positions[f'b_{piece_type.lower()}_{count}'] = (x, y)
            else:
                original_positions[f'b_{piece_type.lower()}'] = (x, y)
        
        return original_positions

    def reset_to_original_positions(self, fen: str) -> List[List[Tuple[float, float]]]:
        """
        Calculate paths to move all pieces from the given FEN position to their original starting positions.
        
        Args:
            fen: The current FEN position to reset from
            
        Returns:
            List of paths for each piece that needs to move to reach original position
        """
        # First, set up the board with the given FEN
        self.place_from_fen(fen)
        
        # Get original positions
        original_positions = self.get_original_positions()
        
        # Get all paths needed to reset the board
        reset_paths = []
        piece_assignments = {}
        
        # Create a mapping of current pieces to their target original positions
        current_pieces = []
        for piece_id, piece_info in self.piece_locations['active'].items():
            current_pieces.append({
                'id': piece_id,
                'type': piece_info['type'],
                'color': piece_info['color'],
                'current_pos': piece_info['position']
            })
        
        # Also include pieces in graveyard that need to return to the board
        for color in ['w', 'b']:
            for piece_key, piece_info in self.piece_locations[f'captured_{color}'].items():
                current_pieces.append({
                    'id': piece_key,
                    'type': piece_info['type'],
                    'color': piece_info['color'],
                    'current_pos': piece_info['position'],
                    'from_graveyard': True
                })
        
        # Sort pieces to prioritize on-board repositioning first, then graveyard clearing
        def sort_priority(piece):
            if not piece.get('from_graveyard', False):
                return 0  # On-board pieces move FIRST to free up space
            
            pos = piece['current_pos']
            # Backup graveyard columns (gy2 and gy11) get second priority
            if abs(pos[0] - self.graveyard_left_col2) < 1:  # Left backup column (gy2)
                return 1
            elif abs(pos[0] - self.graveyard_right_col2) < 1:  # Right backup column (gy11)
                return 1
            else:
                return 2  # Primary graveyard columns (gy1 and gy12) move last
        
        current_pieces.sort(key=sort_priority)
        
        # Track positions that become occupied as pieces move
        newly_occupied_positions = []
        # Track positions that become free as pieces leave graveyard
        newly_free_positions = []
        
        # Assign each piece to its original position
        used_positions = set()
        
        for piece in current_pieces:
            piece_type = piece['type'].lower()
            color = piece['color']
            
            # Find an appropriate original position for this piece
            target_key = None
            
            if piece_type == 'p':
                # Find an unused pawn position
                for i in range(8):
                    key = f'{color}_pawn_{i}'
                    if key in original_positions and key not in used_positions:
                        target_key = key
                        break
            elif piece_type in ['r', 'n', 'b']:
                # Find an unused position for this piece type
                for i in range(2):
                    key = f'{color}_{piece_type}_{i}'
                    if key in original_positions and key not in used_positions:
                        target_key = key
                        break
            else:
                # Unique pieces (King, Queen)
                key = f'{color}_{piece_type}'
                if key in original_positions and key not in used_positions:
                    target_key = key
            
            if target_key:
                target_pos = original_positions[target_key]
                current_pos = piece['current_pos']
                
                # Calculate path with current state of newly occupied and freed positions
                path = self.path_to_target(current_pos[0], current_pos[1], target_pos[0], target_pos[1], newly_occupied_positions, newly_free_positions)
                
                if path:
                    reset_paths.append({
                        'piece_id': piece['id'],
                        'piece_type': piece['type'],
                        'piece_color': piece['color'],
                        'from_pos': current_pos,
                        'to_pos': target_pos,
                        'path': path,
                        'from_graveyard': piece.get('from_graveyard', False)
                    })
                    
                    # Update tracking lists
                    # The target position becomes occupied
                    newly_occupied_positions.append(target_pos)
                    
                    # The source position becomes free (whether from graveyard or board)
                    newly_free_positions.append(current_pos)
                
                used_positions.add(target_key)
                piece_assignments[piece['id']] = target_key
        
        return reset_paths

    def get_graveyard_column_info(self, x_pos: float) -> str:
        """Helper method to identify which graveyard column a position belongs to"""
        if abs(x_pos - self.graveyard_left_col1) < 1:
            return "gy1 (left primary)"
        elif abs(x_pos - self.graveyard_left_col2) < 1:
            return "gy2 (left backup)"
        elif abs(x_pos - self.graveyard_right_col1) < 1:
            return "gy12 (right primary)"
        elif abs(x_pos - self.graveyard_right_col2) < 1:
            return "gy11 (right backup)"
        else:
            return "on board"


if __name__ == "__main__":
    board = Board()    
    print(f"Resetting board from FEN: {fen}")
    print("Current position has:")
    print("- Black king on g8")
    print("- White pawn on g3") 
    print("- White king on f1")
    print("- All other pieces in graveyard")
    print()
    
    # Calculate paths to reset to original positions
    reset_paths = board.reset_to_original_positions(fen)
    
    print(f"Found {len(reset_paths)} pieces that need to move to original positions:")
    print("Movement sequence optimized: on-board repositioning → gy2 & gy11 → board → gy1 & gy12 → board")
    print()
    
    # Group by movement phase
    phase_1 = []  # on-board pieces
    phase_2 = []  # gy2 and gy11 pieces
    phase_3 = []  # gy1 and gy12 pieces
    
    for i, move_info in enumerate(reset_paths):
        from_pos = move_info['from_pos']
        to_pos = move_info['to_pos']
        graveyard_info = board.get_graveyard_column_info(from_pos[0])
        
        # Add information about graph node changes
        move_info['move_number'] = i + 1
        if move_info.get('from_graveyard', False):
            move_info['graph_change'] = f"Frees {graveyard_info} node ({from_pos[0]:.1f}, {from_pos[1]:.1f}), occupies board position ({to_pos[0]:.1f}, {to_pos[1]:.1f})"
        else:
            move_info['graph_change'] = f"Frees board position ({from_pos[0]:.1f}, {from_pos[1]:.1f}), occupies new board position ({to_pos[0]:.1f}, {to_pos[1]:.1f})"
        
        if "on board" in graveyard_info:
            phase_1.append((move_info, graveyard_info))
        elif "backup" in graveyard_info:
            phase_2.append((move_info, graveyard_info))
        else:  # primary graveyard
            phase_3.append((move_info, graveyard_info))
    
    phases = [
        ("PHASE 1: Reposition pieces already on board", phase_1),
        ("PHASE 2: Clear backup graveyards (gy2 & gy11)", phase_2), 
        ("PHASE 3: Clear primary graveyards (gy1 & gy12)", phase_3)
    ]
    
    move_counter = 1
    for phase_name, phase_moves in phases:
        if phase_moves:
            print(f"=== {phase_name} ===")
            for move_info, graveyard_info in phase_moves:
                piece_name = f"{move_info['piece_color'].upper()} {move_info['piece_type'].upper()}"
                from_pos = move_info['from_pos']
                to_pos = move_info['to_pos']
                path_length = len(move_info['path'])
                
                print(f"{move_counter}. {piece_name} from {graveyard_info}")
                print(f"   From: ({from_pos[0]:.1f}, {from_pos[1]:.1f}) -> To: ({to_pos[0]:.1f}, {to_pos[1]:.1f})")
                print(f"   Graph update: {move_info['graph_change']}")
                print(f"   Path length: {path_length} waypoints")
                print(f"   Path (cm): {[(round(x, 1), round(y, 1)) for x, y in move_info['path']]}")
                print()
                move_counter += 1
            print()
    
    # Render the current board state
    board.render()

