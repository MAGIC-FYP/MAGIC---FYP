''' File for all Chess.com related functions '''
import chessdotcom 
from chessdotcom import get_player_game_archives
import requests
import chess.pgn
from io import StringIO

headers = {'User-Agent': 'username: whitfieldalex, email: awhi0036@student.monash.edu'}


def previous_game(username):
    # Get the list of archived games
    url = f"https://api.chess.com/pub/player/{username}/games/2024/05"
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # print("Archives:", data)  # Debug the response
        # Ensure 'archives' exists and is a list
        if 'games' in data and len(data['games']) > 0:
            # Get the most recent game URL
            game_url = data['games'][-1]['url']  # Get the last game archive URL
            print("Game URL:", game_url)  # Debug the game URL
            
            # Now, fetch the game details from the game URL
            game_response = requests.get(game_url, headers=headers)
            print("First 500 characters of response:\n", game_response.text[:500])
            print(game_response)
            if game_response.status_code == 200:
                game_data = game_response.json()
                print("Game data:", game_data)
            else:
                print(f"Error fetching game data: {game_response.status_code}")
        else:
            print("No archives found for this user.")
    else:
        print(f"Error fetching archives: {response.status_code}")

username = "whitfieldalex" # My chess username
previous_game(username)
