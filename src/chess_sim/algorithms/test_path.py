from path_planner import Board
from fen import generate_random_fen
import os

NUM_TESTS = 5000

def has_l_edge(path, square_size=50):
    """Check if a path contains an L-shaped edge (knight-like move)."""
    if not path or len(path) < 2:
        return False
    
    for i in range(len(path) - 1):
        # Convert from cm to mm for comparison
        x1, y1 = path[i][0] * 10, path[i][1] * 10
        x2, y2 = path[i+1][0] * 10, path[i+1][1] * 10
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # L-shaped edges: (2*square_size, square_size) or (square_size, 2*square_size)
        is_l_edge = (dx == 2 * square_size and dy == square_size) or \
                    (dx == square_size and dy == 2 * square_size)
        
        if is_l_edge:
            return True
    
    return False

def has_diagonal_edge(path, square_size=50):
    """Check if a path contains a diagonal edge."""
    if not path or len(path) < 2:
        return False
    
    for i in range(len(path) - 1):
        # Convert from cm to mm for comparison
        x1, y1 = path[i][0] * 10, path[i][1] * 10
        x2, y2 = path[i+1][0] * 10, path[i+1][1] * 10
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # Diagonal edges: (square_size, square_size)
        is_diagonal = (dx == square_size and dy == square_size)
        
        if is_diagonal:
            return True
    
    return False

def test_path_finding():
    if not os.path.exists('test_results'):
        os.makedirs('test_results')
    
    with open('test_results/failed_paths.txt', 'w') as f_fail, \
         open('test_results/l_edge_paths.txt', 'w') as f_l, \
         open('test_results/diagonal_edge_paths.txt', 'w') as f_diag:
        FAIL_COUNT = 0
        L_EDGE_COUNT = 0
        DIAGONAL_EDGE_COUNT = 0
        
        for test_num in range(NUM_TESTS):
            print(f"Testing FEN {test_num + 1}/{NUM_TESTS}")
            
            random_fen = generate_random_fen(total_pieces=32)
            
            board = Board()
            board.place_from_fen(random_fen)
            
            failed_positions = []
            l_edge_positions = []
            diagonal_edge_positions = []
            
            for x in range(125, 476, 50): 
                for y in range(25, 376, 50): 
                    piece = board.get_piece_at_position(x, y)
                    if piece is not None: 
                        path = board.path_to_graveyard(x, y)
                        if path[0] is None:
                            failed_positions.append((x, y))
                            FAIL_COUNT += 1
                        else:
                            if has_l_edge(path):
                                l_edge_positions.append((x, y, path))
                                L_EDGE_COUNT += 1
                            if has_diagonal_edge(path):
                                diagonal_edge_positions.append((x, y, path))
                                DIAGONAL_EDGE_COUNT += 1
            
            if failed_positions:
                f_fail.write(f"Fail {FAIL_COUNT} FEN: {random_fen}\n")
                f_fail.write("Failed positions:\n")
                for x, y in failed_positions:
                    f_fail.write(f"  Position: ({x}, {y})\n")
                f_fail.write("\n" + "-"*80 + "\n\n")
            
            if l_edge_positions:
                f_l.write(f"L-Edge found (count: {L_EDGE_COUNT}) FEN: {random_fen}\n")
                f_l.write("Positions with L-shaped edges:\n")
                for x, y, path in l_edge_positions:
                    f_l.write(f"  Position: ({x}, {y})\n")
                    f_l.write(f"  Path: {path}\n")
                f_l.write("\n" + "-"*80 + "\n\n")
            
            if diagonal_edge_positions:
                f_diag.write(f"Diagonal-Edge found (count: {DIAGONAL_EDGE_COUNT}) FEN: {random_fen}\n")
                f_diag.write("Positions with diagonal edges:\n")
                for x, y, path in diagonal_edge_positions:
                    f_diag.write(f"  Position: ({x}, {y})\n")
                    f_diag.write(f"  Path: {path}\n")
                f_diag.write("\n" + "-"*80 + "\n\n")
        
        print(f"\nTest completed: {FAIL_COUNT} failures, {L_EDGE_COUNT} paths with L-edges, {DIAGONAL_EDGE_COUNT} paths with diagonal edges")

if __name__ == "__main__":
    test_path_finding() 