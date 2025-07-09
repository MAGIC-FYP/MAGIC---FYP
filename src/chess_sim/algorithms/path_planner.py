import numpy as np
import chess
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from typing import List, Tuple
#from fen import generate_random_fen
import networkx as nx

class Piece:
    def __init__(self, piece_id: int, x: float, y: float, piece_type: str = 'P', color: str = 'w', diameter: float = 35.0):
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
                'white_queen': (25, 375),
                'black_queen': (575, 25)
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
                            x = 25  
                            y = start_y_w - col_1_count * spacing_y
                            col_1_count += 1
                        else:
                            x = 75 
                            y = start_y_b + col_2_count * spacing_y 
                            col_2_count += 1
                    else: 
                        if col_12_count <= 7:
                            x = 575  
                            y = start_y_b + col_12_count * spacing_y
                            col_12_count += 1
                        else:
                            x = 525  
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
                
                circle = Circle((x, y), 17.5, 
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
            
            circle = Circle((x, y), 17.5, 
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

    def create_movement_graph(self, start_x: float, start_y: float) -> Tuple[nx.Graph, Tuple[float, float]]:
        G = nx.Graph()
        G.add_node((start_x, start_y))
        grid_points = []
        
        for i in range(self.width):
            for j in range(self.height):
                grid_x = 25 + i * 50
                grid_y = 25 + j * 50
                grid_points.append((grid_x, grid_y))

        # Express Travel Channels
        for i in range(self.width):
            grid_points.append((25 + i * 50, -12.5))
            grid_points.append((25 + i * 50, 412.5))
        
        for point in grid_points:
            point_x, point_y = point
            if self.get_piece_at_position(point_x, point_y, 0) is None:
                G.add_node(point)
        
        for point in list(G.nodes()):
            point_x, point_y = point
            diagonal_weight = 4
            L_shape_weight = 10
            
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

            L_shape_directions = [  
                (point_x + 100, point_y+50, L_shape_weight),
                (point_x + 100, point_y-50, L_shape_weight),
                (point_x - 100, point_y+50, L_shape_weight),
                (point_x - 100, point_y-50, L_shape_weight),
                (point_x + 50, point_y+100, L_shape_weight),
                (point_x + 50, point_y-100, L_shape_weight),
                (point_x - 50, point_y+100, L_shape_weight),
                (point_x - 50, point_y-100, L_shape_weight),
            ]
            
            for adjacent_x, adjacent_y, weight in straight_directions + diagonal_directions + L_shape_directions:
                if (adjacent_x, adjacent_y) in G.nodes():
                    G.add_edge(point, (adjacent_x, adjacent_y), weight=weight)

            if point_y == 25:
                G.add_edge(point, (point_x, -12.5), weight=1)
            if point_y == 375:
                G.add_edge(point, (point_x, 412.5), weight=1)
        
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
                                      if point[0] == 25 and point[1] >= 25 and point[1] <= 375]  # Regular graveyard
                    backup_targets = [(point, distances[point]) for point in distances.keys() 
                                     if point[0] == 75 and point[1] >= 25 and point[1] <= 375]   # Backup graveyard
                else:
                    # Black pieces go to right side graveyard, lowest possible position
                    primary_targets = [(point, distances[point]) for point in distances.keys() 
                                      if point[0] == 575 and point[1] >= 25 and point[1] <= 375]  # Regular graveyard
                    backup_targets = [(point, distances[point]) for point in distances.keys() 
                                     if point[0] == 525 and point[1] >= 25 and point[1] <= 375]  # Backup graveyard
                
                if primary_targets:
                    # For white pieces, get highest y-coordinate; for black, get lowest
                    target_point = max(primary_targets, key=lambda x: x[0][1])[0] if piece.color == "w" else min(primary_targets, key=lambda x: x[0][1])[0]
                elif backup_targets:
                    # Same logic for backup targets
                    target_point = max(backup_targets, key=lambda x: x[0][1])[0] if piece.color == "w" else min(backup_targets, key=lambda x: x[0][1])[0]
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
            elif node[1] == -12.5 or node[1] == 412.5:
                node_colors.append('green')  # Express travel channel points
            else:
                node_colors.append('blue')  # Regular grid points
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=100)
        
        labels = {node: f"({node[0]}, {node[1]})" for node in G.nodes() if node[1] == -12.5 or node[1] == 412.5}
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
        x = 25 + (ord(uci[0]) - ord('a')) * 50 + 100
        y = 25 + (int(uci[1]) - 1) * 50
        return (x, y)

    def process_path(self, path: List[Tuple[float, float]]):
        pass

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
                queen = self.get_piece_at_position(75, 375)
                path2 = self.path_to_target(75, 375, to_x, to_y)
                self.pieces[queen.id].x = to_x
                self.pieces[queen.id].y = to_y
                self.piece_locations['promotion']['white_queen'] = (to_x, to_y)
                self.piece_locations['active'][queen.id]['position'] = (to_x, to_y)
            else:
                queen = self.get_piece_at_position(525, 25)
                path2 = self.path_to_target(75, 375, to_x, to_y)
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
                rook_piece = self.get_piece_at_position(125, from_y)

                # King moves from e1 to c1 or e8 to c8
                path_1 = self.path_to_target(from_x, from_y, to_x, to_y) # King path
                self.pieces[king_piece.id].x = to_x
                self.pieces[king_piece.id].y = to_y
                self.piece_locations['active'][king_piece.id]['position'] = (to_x, to_y)

                # Rook moves from d1 to a1 or d8 to a8
                path_2 = self.path_to_target(125 , from_y, to_x + 50, to_y) # Rook path
                self.pieces[rook_piece.id].x = to_x
                self.pieces[rook_piece.id].y = to_y
                self.piece_locations['active'][rook_piece.id]['position'] = (to_x, to_y)

                return [path_1, path_2]

            else:
                # King side castling
                king_piece = self.get_piece_at_position(from_x, from_y)
                rook_piece = self.get_piece_at_position(475, from_y)

                # King moves from e1 to g1 or e8 to g8
                path_1 = self.path_to_target(from_x, from_y, to_x, to_y) # King path
                self.pieces[king_piece.id].x = to_x
                self.pieces[king_piece.id].y = to_y
                self.piece_locations['active'][king_piece.id]['position'] = (to_x, to_y)

                # Rook moves from f1 to h1 or f8 to h8
                path_2 = self.path_to_target(475, from_y, to_x - 50, to_y) # Rook path
                self.pieces[rook_piece.id].x = to_x
                self.pieces[rook_piece.id].y = to_y
                self.piece_locations['active'][rook_piece.id]['position'] = (to_x, to_y)

                return [path_1, path_2]

        # Check if there's a piece at the destination (i.e. is capture move?)
        captured_piece = self.get_piece_at_position(to_x, to_y)
        path = []

        if captured_piece:
            print("here")
            graveyard_path = self.path_to_graveyard(to_x, to_y)
            if graveyard_path:
                path.append(graveyard_path)
                #Update the piece location in the board to the last point in the graveyard path
                self.pieces[captured_piece.id].x = graveyard_path[-1][0]
                self.pieces[captured_piece.id].y = graveyard_path[-1][1]
                self.piece_locations['active'][captured_piece.id]['position'] = (graveyard_path[-1][0], graveyard_path[-1][1])
        
        
        path.append(self.path_to_target(from_x, from_y, to_x, to_y))

        return path
        


if __name__ == "__main__":
    board = Board()
    board.place_from_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    print(board.pychess_board.is_castling(chess.Move.from_uci('e1c1')))
    #path = board.get_full_path('e1c1')
    #print(path)
    board.render()

