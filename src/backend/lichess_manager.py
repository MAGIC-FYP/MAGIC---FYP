'''
Lichess Board API manager for real-time online gameplay.
Uses streaming API for real-time game updates.
'''
import berserk
import chess
import time
import threading
from typing import Optional, Dict, Tuple


class LichessGameManager:
    """Manages Lichess Board API connections for online gameplay."""
    
    def __init__(self, api_token: str):
        """
        Initialize Lichess connection with Board API.
        
        Args:
            api_token: Personal Lichess API token
        """
        self.api_token = api_token
        self.session = berserk.TokenSession(api_token)
        self.client = berserk.Client(session=self.session)
        self.event_stream = None
        self.game_id = None
        self.opponent_name = None
        
    def get_authenticated_username(self) -> Optional[str]:
        """
        Return the username of the authenticated account associated with the API token.
        Falls back to the account id if username is unavailable.
        """
        try:
            account = self.client.account.get()
            return account.get('username') or account.get('id')
        except Exception as e:
            # Berserk library has compatibility issues with Python 3.11+
            # Try direct API call as fallback
            print(f"Warning: berserk client error ({e}), trying direct API call...")
            try:
                import requests
                response = requests.get(
                    'https://lichess.org/api/account',
                    headers={'Authorization': f'Bearer {self.api_token}'}
                )
                if response.status_code == 200:
                    data = response.json()
                    username = data.get('username') or data.get('id')
                    print(f"Retrieved username via direct API: {username}")
                    return username
            except Exception as e2:
                print(f"Fallback API call also failed: {e2}")
            return None
    
    def check_ongoing_games(self) -> list:
        """
        Check for any ongoing games on the account.
        
        Returns:
            List of ongoing game IDs
        """
        try:
            account_info = self.client.account.get()
            playing = account_info.get('playing')
            if playing:
                ongoing_games = [game['gameId'] for game in playing]
                return ongoing_games
            return []
        except Exception as e:
            print(f"Error checking ongoing games: {e}")
            return []
        
    def create_quickmatch(self, time_minutes: int = 10, increment_seconds: int = 0, 
                         rated: bool = False) -> Optional[str]:
        """
        Create a quickmatch seek and wait for opponent.
        
        This streams incoming events and creates a seek simultaneously.
        
        Args:
            time_minutes: Game time in minutes
            increment_seconds: Time increment per move in seconds
            rated: Whether the game is rated
            
        Returns:
            game_id when matched, None on error
        """
        print(f"Creating quickmatch: {time_minutes}+{increment_seconds} ({'Rated' if rated else 'Unrated'})")
        print("Searching for opponent...")
        
        # Start event stream to listen for game start
        event_stream = self.client.board.stream_incoming_events()
        
        # Track when seek is created
        seek_created = {'ready': False}
        
        # Create seek in separate thread to not block event stream
        seek_thread = threading.Thread(
            target=self._create_seek_blocking,
            args=(time_minutes, increment_seconds, rated, seek_created)
        )
        seek_thread.daemon = True
        seek_thread.start()
        
        # Wait for gameStart event
        try:
            for event in event_stream:
                print(f"DEBUG: Quickmatch event received: {event.get('type')}")
                
                if event['type'] == 'gameStart':
                    game_id = event['game']['id']
                    self.opponent_name = event['game']['opponent']['name']
                    print(f"DEBUG: gameStart detected, game_id: {game_id}")
                    
                    # Only accept this game if our seek was created
                    # This prevents picking up old/existing games
                    if seek_created['ready']:
                        self.game_id = game_id
                        print(f"Match found! Game ID: {game_id}")
                        return game_id
                    else:
                        print(f"DEBUG: Ignoring gameStart (seek not ready yet)")
                        
                elif event['type'] == 'challenge':
                    # Ignore challenges during quickmatch
                    print(f"DEBUG: Ignoring incoming challenge during quickmatch")
                    continue
        except Exception as e:
            print(f"Error during matchmaking: {e}")
            return None
    
    def _create_seek_blocking(self, time_minutes: int, increment_seconds: int, rated: bool, seek_created: dict):
        """
        Create a seek - this blocks until matched or canceled.
        Runs in separate thread.
        """
        try:
            # Mark that we're creating the seek
            seek_created['ready'] = True
            print("DEBUG: Seek creation started")
            
            # This will block until seek is matched
            self.client.board.seek(
                time=time_minutes,
                increment=increment_seconds,
                rated=rated
            )
            print("DEBUG: Seek matched!")
        except Exception as e:
            print(f"Seek error: {e}")
    
    def stream_game_state(self, game_id: str):
        """
        Stream game state for real-time updates.
        
        Args:
            game_id: Lichess game ID
            
        Returns:
            Iterator of game state events
        """
        return self.client.board.stream_game_state(game_id)
    
    def make_move(self, game_id: str, move: chess.Move) -> bool:
        """
        Make a move in the game.
        
        Args:
            game_id: Lichess game ID
            move: Chess move to make
            
        Returns:
            True if successful, False otherwise
        """
        try:
            move_uci = move.uci()
            self.client.board.make_move(game_id, move_uci)
            print(f"Move sent to Lichess: {move_uci}")
            return True
        except Exception as e:
            print(f"Error making move: {e}")
            return False
    
    def get_game_info(self, game_id: str) -> Optional[Dict]:
        """
        Get game information from the first stream event.
        
        Args:
            game_id: Lichess game ID
            
        Returns:
            Dictionary with game info or None
        """
        try:
            stream = self.stream_game_state(game_id)
            # First event is always gameFull
            first_event = next(stream)
            
            if first_event['type'] == 'gameFull':
                white_player = first_event.get('white', {})
                black_player = first_event.get('black', {})
                if white_player.get('name', white_player.get('id', 'White')) == self.get_authenticated_username():
                    opponent_name = black_player.get('name', black_player.get('id', 'Black'))
                else:
                    opponent_name = white_player.get('name', white_player.get('id', 'White'))
            
                return {
                    'game_id': game_id,
                    'white': white_player.get('name', white_player.get('id', 'White')),
                    'black': black_player.get('name', black_player.get('id', 'Black')),
                    'opponent_name': opponent_name,
                    'white_rating': white_player.get('rating', '?'),
                    'black_rating': black_player.get('rating', '?'),
                    'rated': first_event.get('rated', False),
                    'speed': first_event.get('speed', 'unknown'),
                    'initial_fen': first_event.get('initialFen', 'startpos'),
                    'moves': first_event['state'].get('moves', '').split() if first_event['state'].get('moves') else []
                }
        except Exception as e:
            print(f"Error getting game info: {e}")
            return None
    
    def resign_game(self, game_id: str):
        """Resign the current game."""
        try:
            self.client.board.resign_game(game_id)
            print("Game resigned")
        except Exception as e:
            print(f"Error resigning: {e}")
    
    def abort_game(self, game_id: str):
        """Abort the game (only possible in first moves)."""
        try:
            self.client.board.abort_game(game_id)
            print("Game aborted")
        except Exception as e:
            print(f"Error aborting: {e}")
    
    def challenge_user(self, username: str, time_minutes: int = 10, 
                      increment_seconds: int = 0, rated: bool = False) -> Optional[str]:
        """
        Challenge a specific user to a game.
        
        Args:
            username: Lichess username to challenge
            time_minutes: Game time in minutes
            increment_seconds: Time increment per move in seconds
            rated: Whether the game is rated
            
        Returns:
            game_id when challenge is accepted, None on error or decline
        """
        try:
            print(f"Challenging {username} to a game: {time_minutes}+{increment_seconds}")
            
            # Start event stream to listen for game start
            event_stream = self.client.board.stream_incoming_events()
            
            # Container to store challenge ID from the thread
            challenge_info = {'challenge_id': None}
            
            # Create challenge in separate thread
            challenge_thread = threading.Thread(
                target=self._create_challenge_blocking,
                args=(username, time_minutes, increment_seconds, rated, challenge_info)
            )
            challenge_thread.daemon = True
            challenge_thread.start()
            
            # Wait for challenge acceptance or timeout
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            for event in event_stream:
                #print(f"DEBUG: Challenge event received: {event.get('type')}")
                
                if time.time() - start_time > timeout:
                    print("Challenge timed out (no response)")
                    return None
                
                # Track when our challenge is created (we sent it, so destUser matches our target)
                if event['type'] == 'challenge':
                    challenge_data = event.get('challenge', {})
                    dest_user = challenge_data.get('destUser', {})
                    dest_username = dest_user.get('name') or dest_user.get('id')
                    
                    # Check if this challenge is to the user we're challenging
                    if dest_username and dest_username.lower() == username.lower():
                        challenge_info['challenge_id'] = challenge_data['id']
                        print(f"Challenge sent! Challenge ID: {challenge_info['challenge_id']}")
                        print(f"Waiting for {username} to accept...")
                
                if event['type'] == 'gameStart':
                    game_id = event['game']['id']
                    self.opponent_name = self.get_game_info(game_id)['opponent_name']
                    #print(f"DEBUG: gameStart detected, game_id: {game_id}")
                    
                    # Only accept this game if we have a challenge ID (meaning we sent a challenge recently)
                    # This prevents picking up old/existing games
                    if challenge_info['challenge_id'] is not None:
                        self.game_id = game_id
                        print(f"Challenge accepted! Game ID: {game_id}")
                        return game_id
                    
                elif event['type'] == 'challengeDeclined':
                    print(f"Challenge declined by {username}")
                    return None
                elif event['type'] == 'challengeCanceled':
                    print("Challenge was canceled")
                    return None
                    
        except Exception as e:
            print(f"Error challenging user: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_challenge_blocking(self, username: str, time_minutes: int, 
                                   increment_seconds: int, rated: bool, challenge_info: dict):
        """
        Create a challenge - runs in separate thread.
        """
        try:
            # Create the challenge using berserk
            result = self.client.challenges.create(
                username=username,
                rated=rated,
                clock_limit=time_minutes * 60,  # Convert to seconds
                clock_increment=increment_seconds,
                color='random'  # Let Lichess decide colors
            )
            #print(f"DEBUG: Challenge created: {result}")
        except Exception as e:
            # Berserk library has compatibility issues with Python 3.11+
            # Try direct API call as fallback
            print(f"Challenge creation error with berserk: {e}")
            print("Trying direct API call...")
            try:
                import requests
                response = requests.post(
                    f'https://lichess.org/api/challenge/{username}',
                    headers={'Authorization': f'Bearer {self.api_token}'},
                    json={
                        'rated': rated,
                        'clock.limit': time_minutes * 60,
                        'clock.increment': increment_seconds,
                        'color': 'random'
                    }
                )
                
                print(f"Direct API challenge failed: {response.status_code} - {response.text}")
            except Exception as e2:
                print(f"Fallback challenge creation also failed: {e2}")
