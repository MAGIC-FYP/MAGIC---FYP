''' File for all Chess.com/LiChess related functions '''
import berserk
import re
import time
import requests
# Alex's personal API token
API_TOKEN = 'lip_x73cN37xXXVy7EkHCbDa'
BASE_URL = "https://lichess.org/api"
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

# Get the last game played by user
def archived_game(username):
    games = list(client.games.export_by_player(username, max=1, moves=True, pgn_in_json=True))
    
    if not games:
        print("No games found for this user.")
        return None, None, None
    game_pgn = games[0]['pgn'].split('\n\n')[1]
    # Use regex to remove move numbers and results
    moves = re.sub(r'\d+\.\s*', '', game_pgn)  # Remove "1. ", "2. ", etc.
    moves = re.sub(r'1-0|0-1|1/2-1/2|\*', '', moves).strip().split()  # Remove results & split into a list of moves

    # Extract player names and colors
    white_name = games[0]["players"]["white"]["user"]["name"]
    black_name = games[0]["players"]["black"]["user"]["name"]

    print(white_name)
    print(black_name)
    print(moves)

    return moves, white_name, black_name

# Using a game ID to find an archived game 
def extract_game_id(url):
    match = re.search(r'lichess\.org/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None

def extract_clean_moves(raw_moves):
    cleaned_moves = []
    for token in raw_moves:
        # Skip annotations, evals, clocks, and brackets
        if token in ['{', '}'] or token.startswith('[') or token.startswith('%') or re.match(r'\[%.*\]', token):
            continue
        # Skip dots for black moves (e.g. '..')
        if token == '..':
            continue
        cleaned_moves.append(token)
    return cleaned_moves

def get_game_by_id(url):
    game_id = extract_game_id(url)

    try:
        game_data = client.games.export(game_id, as_pgn=True)
        game_pgn = game_data.split('\n\n')[1]  # Get the moves part
        moves = re.sub(r'\d+\.\s*', '', game_pgn)
        moves = re.sub(r'1-0|0-1|1/2-1/2|\*', '', moves).strip().split()
        
        clean_moves = extract_clean_moves(moves)
        print("Moves:", clean_moves)
        return clean_moves
    
    except Exception as e:
        print(f"Failed to get game: {e}")
        return None

def online_game(username):
    # Find an ongoing game for the user
    print(f"Checking for live games for: {username}")
    games = list(client.games.export_by_player(username, ongoing=True))
    
    if not games:
        print("No live games found.")
        return
    
    game_id = games[0]['id']  # Get the first active game's ID
    print(f"Found live game: {game_id}")
    # Extract player names and colors
    white_name = games[0]["players"]["white"]["user"]["name"]
    black_name = games[0]["players"]["black"]["user"]["name"]
    print(f"White: {white_name} vs Black: {black_name}")

    
    last_moves = games[0].get("moves", "").split()
    last_move_count = len(last_moves)
    print(f"Current position has {last_move_count} moves already played")
    print("Watching for moves...")
      
    try:
        while True:
            # Get the current game state
            game_state = client.games.export(game_id)
            
            # Check if game ended
            if game_state.get("status") != "started":
                print(f"Game ended. Status: {game_state.get('status')}")
                break
                
            # Get current moves
            current_moves = game_state.get("moves", "").split()
            current_move_count = len(current_moves)
            
            # Check if new moves were made
            if current_move_count > last_move_count:
                # Extract only the new moves
                new_moves = current_moves[last_move_count:]
                
                for i, move in enumerate(new_moves):
                    move_number = (last_move_count + i + 1) // 2 + 1
                    player = "White" if (last_move_count + i) % 2 == 0 else "Black"
                    print(f"Move {move_number}: {player} played {move}")
                
                # Update our record of last seen moves
                last_move_count = current_move_count

    except KeyboardInterrupt:
        print("\nStopped watching game.")
    except Exception as e:
        print(f"Error occurred: {e}")


def get_active_game():
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{BASE_URL}/account/playing", headers=headers)
    data = response.json()
    print(data)

    if "nowPlaying" in data:
        for game in data["nowPlaying"]:
            if game.get("isMyTurn", False):  # Only pick games where it's your turn
                print('SUCCESS: Active Game Found')
                print(game)
                return game["gameId"]
                
    print("Whomp Whomp: No Active Game Where It’s Your Turn")
    return None


def send_move(game_id, move):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    url = f"{BASE_URL}/board/game/{game_id}/move/{move}"
    response = requests.post(url, headers=headers)
    return response.status_code, response.text

# game_id = get_active_game()
# if game_id:
#     move = input("Enter your move (e.g., e2e4): ")
#     status, result = send_move(game_id, move)
#     print(f"Move sent: {status}, Response: {result}")
# else:
#     print("No active game found.")


username = 'uniaccount'


archived_game(username)
print('NEW')
get_game_by_id('https://lichess.org/tbibfPRy')
# online_game('MNZS1927')
# archived_game('anatoliy324')



#####################################
######## OLD CHESS.COM TESTS ########
#####################################
######### No API access :( ##########
#####################################

# # import chessdotcom 
# from chessdotcom import get_player_game_archives
# import requests
# import chess.pgn
# from io import StringIO
# #headers = {'User-Agent': 'username: whitfieldalex, email: awhi0036@student.monash.edu'}
# def previous_game(username):
#     # Get the list of archived games
#     url = f"https://api.chess.com/pub/player/{username}/games/2024/05"
#     #url = f"https://api.chess.com/pub/game/136869707096"
#     response = requests.get(url, headers=headers)
#     print(response)
#     # Check if the request was successful
#     if response.status_code == 200:
#         data = response.json()
#         # print("Archives:", data)  # Debug the response
#         # Ensure 'archives' exists and is a list
#         if 'games' in data and len(data['games']) > 0:
#             # Get the most recent game URL
#             game_url = data['games'][-1]['url']  # Get the last game archive URL
#             print("Game URL:", game_url)  # Debug the game URL
            
#             # Now, fetch the game details from the game URL
#             game_response = requests.get(game_url, headers=headers)
#             print("First 500 characters of response:\n", game_response.text[:500])
#             print(game_response)
#             if game_response.status_code == 200:
#                 game_data = game_response.json()
#                 print("Game data:", game_data)
#             else:
#                 print(f"Error fetching game data: {game_response.status_code}")
#         else:
#             print("No archives found for this user.")
#     else:
#         print(f"Error fetching archives: {response.status_code}")

# def alt_prev_game(username):
#     # Get the list of archived games
#     url = f"https://api.chess.com/pub/player/{username}/games/2024/05"
#     response = requests.get(url, headers=headers)
#     #print(response)

#     if response.status_code == 200:
#         try:
#             data = response.json()
#         except requests.exceptions.JSONDecodeError:
#             print("Error: Response is not valid JSON")
#             #print("Response text:", response.text)
#             return

#         if 'games' in data and len(data['games']) > 0:
#             game_url = data['games'][-1]['url']
#             print("Game URL:", game_url)
#             game_id = game_url.split('/')[-1]  # Get last part of the URL
#             game_api_url = f"https://api.chess.com/pub/game/{game_id}"  # Correct API endpoint
#             print('BOOM', game_api_url)

#             game_response = requests.get(game_api_url, headers=headers)
#             #print("First 500 characters of response:\n", game_response.text[:500])
#             #print(game_response)

#             if game_response.status_code == 200:
#                 try:
#                     game_data = game_response.json()
#                     print("Game data:", game_data)
#                 except requests.exceptions.JSONDecodeError:
#                     print("Error: Game response is not valid JSON")
#                     print("Game Response text:", game_response.text)
#             else:
#                 print(f"Error fetching game data: {game_response.status_code}")
#         else:
#             print("No games found for this user.")
#     else:
#         print(f"Error fetching archives: {response.status_code}")

# username = "whitfieldalex" # My chess username
# alt_prev_game(username)
