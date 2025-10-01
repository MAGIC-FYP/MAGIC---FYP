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

from .menu import SubMenu, MenuItem, BackMenuItem
from typing import Dict, Any, Callable, Optional
import chess


class ChessMenuBuilder:
    """
    Builder class for creating chess game configuration menus.
    """
    
    def __init__(self):
        """Initialize the chess menu builder."""
        self.game_config: Dict[str, Any] = {
            'game_mode': None,  # 'player_vs_robot' or 'robot_vs_robot'
            'player_colour': chess.WHITE,  # WHITE or BLACK
            'robot_level': 1,  # 1-20
            'robot1_level': 1,  # For robot vs robot
            'robot2_level': 1,  # For robot vs robot
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
        
        return root_menu
    
    def _build_player_vs_robot_menu(self) -> SubMenu:
        """Build the Player vs Robot submenu."""
        pvr_menu = SubMenu("Player vs Robot")
        
        # Player Colour submenu
        colour_menu = SubMenu("Player Colour")
        colour_menu.add(MenuItem("White", lambda: self._set_player_colour(chess.WHITE)))
        colour_menu.add(MenuItem("Black", lambda: self._set_player_colour(chess.BLACK)))
        colour_menu.add(BackMenuItem())
        pvr_menu.add(colour_menu)
        
        # Robot Level submenu
        level_menu = SubMenu("Robot Level")
        for level in range(1, 21):  # Levels 1-20
            level_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot_level(l)))
        level_menu.add(BackMenuItem())
        pvr_menu.add(level_menu)
        
        # Start Game
        pvr_menu.add(MenuItem("Start Game", lambda: self._start_player_vs_robot()))
        
        # Back to main menu
        pvr_menu.add(BackMenuItem())
        
        return pvr_menu
    
    def _build_robot_vs_robot_menu(self) -> SubMenu:
        """Build the Robot vs Robot submenu."""
        rvr_menu = SubMenu("Robot vs Robot")
        
        # Robot 1 Difficulty submenu
        robot1_menu = SubMenu("Robot 1 Level")
        for level in range(1, 21):  # Levels 1-20
            robot1_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot1_level(l)))
        robot1_menu.add(BackMenuItem())
        rvr_menu.add(robot1_menu)
        
        # Robot 2 Difficulty submenu
        robot2_menu = SubMenu("Robot 2 Level")
        for level in range(1, 21):  # Levels 1-20
            robot2_menu.add(MenuItem(f"Level {level}", lambda l=level: self._set_robot2_level(l)))
        robot2_menu.add(BackMenuItem())
        rvr_menu.add(robot2_menu)
        
        # Start Game
        rvr_menu.add(MenuItem("Start Game", lambda: self._start_robot_vs_robot()))
        
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
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current game configuration."""
        return self.game_config.copy()
