"""
PGN (Portable Game Notation) file reader and parser.

This module provides functionality to read and parse PGN files,
extracting game moves and metadata for replay on the chess board.
"""

import chess
import chess.pgn
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config import load_config
import time as time_sleep
import re

config = load_config()

class PGNReader:
    """
    Reads and parses PGN files for chess game replay.
    """
    
    def __init__(self, pgn_directory: str = None):
        """
        Initialize the PGN reader.
        
        Args:
            pgn_directory: Directory containing PGN files (defaults to 'PGN Files' in src)
        """
        if pgn_directory is None:
            # Default to PGN Files directory in src (one level up from chess_sim)
            src_dir = Path(__file__).parent.parent
            self.pgn_directory = src_dir / "PGN Files"
        else:
            self.pgn_directory = Path(pgn_directory)
        
        if not self.pgn_directory.exists():
            self.pgn_directory.mkdir(parents=True, exist_ok=True)
    
    def get_pgn_files(self) -> List[str]:
        """
        Get list of PGN files in the directory.
        
        Returns:
            List of PGN filenames (without path)
        """
        if not self.pgn_directory.exists():
            return []
        
        pgn_files = []
        for file_path in self.pgn_directory.glob("*.pgn"):
            pgn_files.append(file_path.name)
        
        return sorted(pgn_files)
    
    def read_pgn_file(self, filename: str) -> Optional[Dict]:
        """
        Read and parse a PGN file.
        
        Args:
            filename: Name of the PGN file to read
            
        Returns:
            Dictionary containing game data, or None if file not found/invalid
        """
        file_path = self.pgn_directory / filename
        
        if not file_path.exists():
            print(f"PGN file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                game = chess.pgn.read_game(file)
                
                if game is None:
                    print(f"No valid game found in {filename}")
                    return None
                
                # Extract game metadata
                game_data = {
                    'filename': filename,
                    'event': game.headers.get('Event', 'Unknown Event'),
                    'site': game.headers.get('Site', 'Unknown Site'),
                    'date': game.headers.get('Date', 'Unknown Date'),
                    'round': game.headers.get('Round', 'Unknown Round'),
                    'white': game.headers.get('White', 'Unknown'),
                    'black': game.headers.get('Black', 'Unknown'),
                    'result': game.headers.get('Result', '*'),
                    'eco': game.headers.get('ECO', ''),
                    'white_elo': game.headers.get('WhiteElo', ''),
                    'black_elo': game.headers.get('BlackElo', ''),
                    'moves': [],
                    'move_count': 0
                }
                
                # Extract moves
                board = chess.Board()
                move_count = 0
                
                for move in game.mainline_moves():
                    move_data = {
                        'move_number': move_count + 1,
                        'move': move,
                        'from_square': move.from_square,
                        'to_square': move.to_square,
                        'uci': move.uci(),
                        'san': board.san(move),
                        'fen_before': board.fen(),
                        'is_capture': board.is_capture(move),
                        'is_castling': board.is_castling(move),
                        'is_en_passant': board.is_en_passant(move),
                        'is_promotion': move.promotion is not None
                    }
                    
                    game_data['moves'].append(move_data)
                    board.push(move)
                    move_count += 1
                
                game_data['move_count'] = move_count
                game_data['final_fen'] = board.fen()
                
                return game_data
                
        except Exception as e:
            print(f"Error reading PGN file {filename}: {e}")
            return None
    
    def get_game_summary(self, filename: str) -> Optional[str]:
        """
        Get a brief summary of a PGN file for display in menu.
        
        Args:
            filename: Name of the PGN file
            
        Returns:
            Formatted summary string, or None if file not found
        """
        game_data = self.read_pgn_file(filename)
        
        if game_data is None:
            return None
        
        # Create a compact summary for LCD display
        white_name = game_data['white'][:8] if len(game_data['white']) > 8 else game_data['white']
        black_name = game_data['black'][:8] if len(game_data['black']) > 8 else game_data['black']
        
        summary = f"{white_name} vs {black_name}"
        
        # Add date if available
        if game_data['date'] != 'Unknown Date':
            try:
                # Extract year from date
                year_match = re.search(r'(\d{4})', game_data['date'])
                if year_match:
                    summary += f" ({year_match.group(1)})"
            except:
                pass
        
        # Add result
        result_map = {
            '1-0': 'W',
            '0-1': 'B', 
            '1/2-1/2': 'D',
            '*': '?'
        }
        result = result_map.get(game_data['result'], '?')
        summary += f" [{result}]"
        
        return summary
    
    def validate_pgn_file(self, filename: str) -> bool:
        """
        Validate that a PGN file is readable and contains a valid game.
        
        Args:
            filename: Name of the PGN file to validate
            
        Returns:
            True if file is valid, False otherwise
        """
        game_data = self.read_pgn_file(filename)
        return game_data is not None and len(game_data['moves']) > 0


class PGNExecutor:
    """
    Executes PGN games on the chess board.
    """
    
    def __init__(self, board, controller, gantry, path_planner_board, lcd_manager=None):
        """
        Initialize the PGN executor.
        
        Args:
            board: Chess board instance
            controller: Controller instance for piece movement
            gantry: Gantry control instance
            path_planner_board: Path planner instance
            lcd_manager: LCD manager for interrupt handling
        """
        self.board = board
        self.controller = controller
        self.current_game = None
        self.current_move_index = 0
        self.is_executing = False
        self.gantry = gantry
        self.path_planner_board = path_planner_board
        self.path_const = (3.5/5)
        self.lcd_manager = lcd_manager
        
    
    def load_game(self, game_data: Dict) -> bool:
        """
        Load a game for execution.
        
        Args:
            game_data: Game data from PGNReader
            
        Returns:
            True if game loaded successfully, False otherwise
        """
        if not game_data or not game_data['moves']:
            return False
        
        self.current_game = game_data
        self.current_move_index = 0
        return True
    
    def execute_game(self, delay_between_moves: float = 2.0) -> bool:
        """
        Execute the loaded game on the chess board.
        
        Args:
            delay_between_moves: Delay in seconds between moves
            
        Returns:
            True if execution completed successfully, False otherwise
        """
        quick_speed = config['gantry']['quick_speed']
        slow_speed = config['gantry']['slow_speed']

        if not self.current_game:
            print("No game loaded for execution")
            return False
        
        print(f"\nExecuting game: {self.current_game['white']} vs {self.current_game['black']}")
        print(f"Total moves: {self.current_game['move_count']}")
        print("=" * 50)
        
        # Center all pieces first
        print("Centering pieces...")
        #self.board.gantry.center_pieces()
        
        # Reset board to starting position
        #self.board.board.reset()
        
        self.is_executing = True
        
        try:
            for i, move_data in enumerate(self.current_game['moves']):
                # Check for interrupt
                if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                    print("\nArchived game interrupted by user")
                    self.lcd_manager.acknowledge_interrupt()
                    self.lcd_manager.clear_game_interrupt()
                    return False
                
                if not self.is_executing:
                    break
                
                print(f"\nMove {move_data['uci']}: {move_data['san']}")
                self.path_planner_board.place_from_fen(self.board.board.fen())
                self.path = self.path_planner_board.get_full_path_simpli(move_data['uci'])
                # Make the move on the board
                if self.board.make_move(move_data['move']):
                    #print(self.board.board)
                    move = move_data['uci']
                    
                    print(f"Path: {self.path}")
                    for path in self.path:
                        # Check for interrupt before each path segment
                        if self.lcd_manager and self.lcd_manager.is_game_interrupt_requested():
                            print("\nArchived game interrupted during gantry movement")
                            self.lcd_manager.acknowledge_interrupt()
                            self.lcd_manager.clear_game_interrupt()
                            self.gantry.electromagnet(False)  # Release piece
                            return False
                        
                        move_result = self.gantry.move(path[0][0]*self.path_const, path[0][1]*self.path_const, quick_speed)
                        if move_result == False:
                            print("Gantry movement interrupted")
                            self.lcd_manager.acknowledge_interrupt()
                            self.lcd_manager.clear_game_interrupt()
                            self.gantry.electromagnet(False)
                            return False
                        
                        self.gantry.electromagnet(True)
                        time_sleep.sleep(0.3)

                        for point in path[:-1]:
                            move_result = self.gantry.move(point[0]*self.path_const, point[1]*self.path_const, slow_speed)
                            if move_result == False:
                                print("Gantry movement interrupted")
                                self.lcd_manager.acknowledge_interrupt()
                                self.lcd_manager.clear_game_interrupt()
                                self.gantry.electromagnet(False)
                                return False
                            
                        move_result = self.gantry.move(path[len(path)-1][0]*self.path_const, path[len(path)-1][1]*self.path_const, slow_speed, drag_compensation=True)
                        if move_result == False:
                            print("Gantry movement interrupted")
                            self.lcd_manager.acknowledge_interrupt()
                            self.lcd_manager.clear_game_interrupt()
                            self.gantry.electromagnet(False)
                            return False
                        
                        self.gantry.electromagnet(False)
                        time_sleep.sleep(0.1)
                        self.gantry.electromagnet(True)
                        time_sleep.sleep(0.3)
                        self.gantry.electromagnet(False)
                        time_sleep.sleep(0.1)
                    
                    print(f"Executed: {move_data['uci']}")
                    
                    
                    # Switch player for next move
                    self.board.switch_player()
                    
                    # Wait before next move
                    import time
                    time.sleep(delay_between_moves)
                else:
                    print(f"Failed to execute move: {move_data['san']}")
                    return False
            
            print("\n" + "=" * 50)
            print("Game execution completed!")
            print(f"Final result: {self.current_game['result']}")
            
            return True
            
        except KeyboardInterrupt:
            print("\nGame execution interrupted by user")
            return False
        except Exception as e:
            print(f"Error during game execution: {e}")
            return False
        finally:
            self.is_executing = False
    
    def stop_execution(self):
        """Stop the current game execution."""
        self.is_executing = False
    
    def get_execution_progress(self) -> Tuple[int, int]:
        """
        Get current execution progress.
        
        Returns:
            Tuple of (current_move, total_moves)
        """
        if not self.current_game:
            return (0, 0)
        
        return (self.current_move_index, self.current_game['move_count'])
    
    def is_currently_executing(self) -> bool:
        """Check if a game is currently being executed."""
        return self.is_executing
