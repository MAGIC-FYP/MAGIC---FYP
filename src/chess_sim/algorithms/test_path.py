from path_planner import Board
from fen import generate_random_fen
import os

NUM_TESTS = 5000

def test_path_finding():
    if not os.path.exists('test_results'):
        os.makedirs('test_results')
    
    with open('test_results/failed_paths.txt', 'w') as f:
        FAIL_COUNT = 0
        for test_num in range(NUM_TESTS):
            print(f"Testing FEN {test_num + 1}/{NUM_TESTS}")
            
            random_fen = generate_random_fen(total_pieces=32)
            
            board = Board()
            board.place_from_fen(random_fen)
            
            failed_positions = []
            for x in range(125, 476, 50): 
                for y in range(25, 376, 50): 
                    piece = board.get_piece_at_position(x, y)
                    if piece is not None: 
                        path = board.path_to_graveyard(x, y)
                        if path[0] is None:
                            failed_positions.append((x, y))
                            FAIL_COUNT += 1
            
            if failed_positions:
                f.write(f" Fail {FAIL_COUNT} FEN: {random_fen}\n")
                f.write("Failed positions:\n")
                for x, y in failed_positions:
                    f.write(f"  Position: ({x}, {y})\n")
                f.write("\n" + "-"*80 + "\n\n")

if __name__ == "__main__":
    test_path_finding() 