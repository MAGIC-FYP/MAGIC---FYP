"""
Chess game menu structure builder.

Creates a hierarchical menu for chess game configuration:
- Player vs Robot
  - Player Colour
  - Robot Level
  - Start Game
- Robot vs Robot
  - Robot 1 Difficulty
  - Robot 2 Difficulty
  - Start Game
"""

from typing import Dict, Any, Callable, Optional
import chess

# Use try/except to support both relative and absolute imports
try:
    from .menu import SubMenu, MenuItem, BackMenuItem
except ImportError:
    from menu import SubMenu, MenuItem, BackMenuItem


class ChessMenuBuilder:
    """
    Builder class for creating chess game configuration menus.
    """
    
    def __init__(self):
        """Initialize the chess menu builder."""
        self.game_config: Dict[str, Any] = {
            'game_mode': None,  # 'player_vs_robot', 'robot_vs_robot', 'online_quickmatch', or 'online_friend_challenge'
            'player_colour': chess.WHITE,  # WHITE or BLACK
            'robot_level': 1,  # 1-20
            'robot1_level': 1,  # For robot vs robot
            'robot2_level': 1,  # For robot vs robot
            'lichess_time': 10,  # Time in minutes for online games
            'lichess_increment': 0,  # Increment in seconds for online games
            'lichess_rated': False,  # Whether online game is rated
            'friend_username': None,  # Username to challenge
        }
        self.start_game_callback: Optional[Callable] = None
    
    def set_start_game_callback(self, callback: Callable):
        """
        Set the callback function to be called when "Start Game" is selected.
        
        Args:
            callback: Function to call with game_config as argument
        """
        self.start_game_callback = callback
        return self
    
    def build(self) -> SubMenu:
        """
        Build and return the complete menu structure.
        
        Returns:
            Root SubMenu containing the entire menu hierarchy
        """
        # Create root menu
        root_menu = SubMenu("Main Menu")
        
        # Create Player vs Robot submenu
        pvr_menu = self._build_player_vs_robot_menu()
        root_menu.add(pvr_menu)
        
        # Create Robot vs Robot submenu
        rvr_menu = self._build_robot_vs_robot_menu()
        root_menu.add(rvr_menu)
        
        # Create Online Play submenu
        online_menu = self._build_online_play_menu()
        root_menu.add(online_menu)
        
        # Create Archived Games submenu
        archived_menu = self._build_archived_games_menu()
        root_menu.add(archived_menu)
        
        return root_menu
    
    def _build_player_vs_robot_menu(self) -> SubMenu:
        """Build the Player vs Robot submenu."""
        pvr_menu = SubMenu("Plyr v Bot")

        # Start Game (no auto_back - stays on current menu or exits)
        pvr_menu.add(MenuItem("Start Game", lambda: self._start_player_vs_robot()))
        
        # Player Colour submenu
        colour_menu = SubMenu("Plyr Col")
        colour_menu.add(MenuItem("White", lambda: self._set_player_colour(chess.WHITE), auto_back=True))
        colour_menu.add(MenuItem("Black", lambda: self._set_player_colour(chess.BLACK), auto_back=True))
        colour_menu.add(BackMenuItem())
        pvr_menu.add(colour_menu)
        
        # Robot Level submenu
        level_menu = SubMenu("Bot Lvl")
        for level in range(1, 21):  # Levels 1-20
            level_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot_level(l), auto_back=True))
        level_menu.add(BackMenuItem())
        pvr_menu.add(level_menu)
        
        # Back to main menu
        pvr_menu.add(BackMenuItem())
        
        return pvr_menu
    
    def _build_robot_vs_robot_menu(self) -> SubMenu:
        """Build the Robot vs Robot submenu."""
        rvr_menu = SubMenu("Bot v Bot")

        # Start Game (no auto_back - stays on current menu or exits)
        rvr_menu.add(MenuItem("Start Game", lambda: self._start_robot_vs_robot()))
        
        # Robot 1 Difficulty submenu
        robot1_menu = SubMenu("Bot 1 Level")
        for level in range(1, 21):  # Levels 1-20
            robot1_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot1_level(l), auto_back=True))
        robot1_menu.add(BackMenuItem())
        rvr_menu.add(robot1_menu)
        
        # Robot 2 Difficulty submenu
        robot2_menu = SubMenu("Bot 2 Level")
        for level in range(1, 21):  # Levels 1-20
            robot2_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot2_level(l), auto_back=True))
        robot2_menu.add(BackMenuItem())
        rvr_menu.add(robot2_menu)
    
        # Back to main menu
        rvr_menu.add(BackMenuItem())
        
        return rvr_menu
    
    def _set_player_colour(self, colour: chess.Color):
        """Set the player's colour."""
        self.game_config['player_colour'] = colour
        colour_name = "White" if colour == chess.WHITE else "Black"
        print(f"Player colour set to: {colour_name}")
    
    def _set_robot_level(self, level: int):
        """Set the robot difficulty level for Player vs Robot."""
        self.game_config['robot_level'] = level
        print(f"Robot level set to: {level}")
    
    def _set_robot1_level(self, level: int):
        """Set Robot 1 difficulty level for Robot vs Robot."""
        self.game_config['robot1_level'] = level
        print(f"Robot 1 level set to: {level}")
    
    def _set_robot2_level(self, level: int):
        """Set Robot 2 difficulty level for Robot vs Robot."""
        self.game_config['robot2_level'] = level
        print(f"Robot 2 level set to: {level}")
    
    def _start_player_vs_robot(self):
        """Start a Player vs Robot game."""
        self.game_config['game_mode'] = 'player_vs_robot'
        print("\n" + "="*50)
        print("Starting Player vs Robot game...")
        print(f"Player colour: {'White' if self.game_config['player_colour'] == chess.WHITE else 'Black'}")
        print(f"Robot level: {self.game_config['robot_level']}")
        print("="*50 + "\n")
        
        if self.start_game_callback:
            self.start_game_callback(self.game_config)
    
    def _start_robot_vs_robot(self):
        """Start a Robot vs Robot game."""
        self.game_config['game_mode'] = 'robot_vs_robot'
        print("\n" + "="*50)
        print("Starting Robot vs Robot game...")
        print(f"Robot 1 level: {self.game_config['robot1_level']}")
        print(f"Robot 2 level: {self.game_config['robot2_level']}")
        print("="*50 + "\n")
        
        if self.start_game_callback:
            self.start_game_callback(self.game_config)
    
    def _build_online_play_menu(self) -> SubMenu:
        """Build the Online Play (Lichess) submenu."""
        online_menu = SubMenu("Play Online")
        
        # Time control submenu
        time_menu = SubMenu("Time Control")
        time_options = [(1, 0, "Bullet 1+0"), (3, 0, "Blitz 3+0"), (5, 0, "Blitz 5+0"),
                       (10, 0, "Rapid 10+0"), (15, 10, "Rapid 15+10")]
        for minutes, increment, label in time_options:
            time_menu.add(MenuItem(label, lambda m=minutes, i=increment: self._set_time_control(m, i), auto_back=True))
        time_menu.add(BackMenuItem())
        online_menu.add(time_menu)
        
        # Rated/Unrated toggle
        rated_menu = SubMenu("Game Type")
        rated_menu.add(MenuItem("Casual", lambda: self._set_rated(False), auto_back=True))
        rated_menu.add(MenuItem("Rated", lambda: self._set_rated(True), auto_back=True))
        rated_menu.add(BackMenuItem())
        online_menu.add(rated_menu)
        
        # Start quickmatch
        online_menu.add(MenuItem("Start Quickmatch", lambda: self._start_quickmatch()))
        
        # Challenge friend option
        online_menu.add(MenuItem("Challenge Friend", lambda: self._challenge_friend()))
        
        # Back to main menu
        online_menu.add(BackMenuItem())
        
        return online_menu
    
    def _set_time_control(self, minutes: int, increment: int):
        """Set time control for online games."""
        self.game_config['lichess_time'] = minutes
        self.game_config['lichess_increment'] = increment
        print(f"Time control set to: {minutes}+{increment}")
    
    def _set_rated(self, rated: bool):
        """Set whether online game is rated."""
        self.game_config['lichess_rated'] = rated
        print(f"Game type set to: {'Rated' if rated else 'Casual'}")
    
    def _start_quickmatch(self):
        """Start a Lichess quickmatch."""
        self.game_config['game_mode'] = 'online_quickmatch'
        print("\n" + "="*50)
        print("Starting Lichess Quickmatch...")
        print(f"Time control: {self.game_config['lichess_time']}+{self.game_config['lichess_increment']}")
        print(f"Game type: {'Rated' if self.game_config['lichess_rated'] else 'Casual'}")
        print("="*50 + "\n")
        
        if self.start_game_callback:
            self.start_game_callback(self.game_config)
    
    def _challenge_friend(self):
        """Challenge a friend to a game - hardcoded to 'tawildoer'."""
        # Hardcoded friend username
        friend_username = 'tawildoer'
        
        self.game_config['friend_username'] = friend_username
        self.game_config['game_mode'] = 'online_friend_challenge'
        
        print("\n" + "="*50)
        print(f"Challenging {friend_username}...")
        print(f"Time control: {self.game_config['lichess_time']}+{self.game_config['lichess_increment']}")
        print(f"Game type: {'Rated' if self.game_config['lichess_rated'] else 'Casual'}")
        print("="*50 + "\n")
        
        if self.start_game_callback:
            self.start_game_callback(self.game_config)
    
    def _build_archived_games_menu(self) -> SubMenu:
        """Build the Archived Games submenu."""
        archived_menu = SubMenu("Archived Games")
        
        # Import PGN reader to get available games
        try:
            import sys
            from pathlib import Path
            # Add chess_sim to path
            chess_sim_path = Path(__file__).parent.parent / "chess_sim"
            if str(chess_sim_path) not in sys.path:
                sys.path.insert(0, str(chess_sim_path))
            
            from pgn_reader import PGNReader
            pgn_reader = PGNReader()
            pgn_files = pgn_reader.get_pgn_files()
            
            if pgn_files:
                # Create menu items for each PGN file
                for filename in pgn_files:
                    summary = pgn_reader.get_game_summary(filename)
                    if summary:
                        # Truncate summary if too long for LCD display
                        display_name = summary[:16] if len(summary) > 16 else summary
                        archived_menu.add(MenuItem(display_name, lambda f=filename: self._start_archived_game(f)))
                    else:
                        # Fallback to filename if summary fails
                        display_name = filename.replace('.pgn', '')[:16]
                        archived_menu.add(MenuItem(display_name, lambda f=filename: self._start_archived_game(f)))
                
                # Add back option
                archived_menu.add(BackMenuItem())
            else:
                # No PGN files found
                archived_menu.add(MenuItem("No games found", lambda: None, auto_back=True))
                archived_menu.add(BackMenuItem())
                
        except ImportError as e:
            print(f"Error importing PGN reader: {e}")
            archived_menu.add(MenuItem("Error loading games", lambda: None, auto_back=True))
            archived_menu.add(BackMenuItem())
        
        return archived_menu
    
    def _start_archived_game(self, filename: str):
        """Start an archived game replay."""
        self.game_config['game_mode'] = 'archived_game'
        self.game_config['archived_filename'] = filename
        
        print("\n" + "="*50)
        print(f"Starting archived game: {filename}")
        print("="*50 + "\n")
        
        if self.start_game_callback:
            self.start_game_callback(self.game_config)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current game configuration."""
        return self.game_config.copy()
