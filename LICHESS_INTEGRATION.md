# Lichess Online Play Integration

This document describes how to play online chess games against real opponents on Lichess.

## Features

✅ **Quickmatch Mode** - Play against random opponents with various time controls  
✅ **Real-time Streaming** - Uses Lichess Board API for instant move updates  
✅ **Multiple Time Controls** - Bullet (1+0), Blitz (3+0, 5+0), Rapid (10+0, 15+10)  
✅ **Rated/Casual Games** - Choose whether to play for rating points  

## Setup

### 1. Get Lichess API Token

1. Go to https://lichess.org/account/oauth/token
2. Log in to your Lichess account
3. Create a new personal API token with these scopes:
   - ✅ **Board: Play games with the Board API** (required)
   - ✅ Read preferences
4. Copy the generated token (starts with `lip_`)

### 2. Configure API Token (IMPORTANT - Security)

**Create your `.env` file:**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and replace with your actual token
# LICHESS_API_TOKEN=lip_your_actual_token_here
```

Or create `.env` manually in the project root:
```bash
LICHESS_API_TOKEN=lip_your_token_here
```

✅ The `.env` file is already in `.gitignore` so it won't be committed  
✅ The code automatically loads the token from `.env` using `python-dotenv`

### 3. Install Dependencies

```bash
pip install berserk python-dotenv
```

## Usage

### Via Menu System

1. Run the chess program:
   ```bash
   python src/chess_sim/main.py
   ```

2. Navigate to **"Play Online"** in the main menu

3. Configure your game:
   - **Time Control**: Select time format (1+0, 3+0, 5+0, 10+0, 15+10)
   - **Game Type**: Choose Casual or Rated
   - **Start Quickmatch**: Begin searching for opponent

4. When prompted, enter your Lichess username

5. Play the game! 
   - Your moves: Enter in UCI format (e.g., `e2e4`)
   - Opponent moves: Received automatically via streaming

### Via Direct Function Call

```python
from src.chess_sim.main import start_game

game_config = {
    'game_mode': 'online_quickmatch',
    'lichess_time': 10,         # minutes
    'lichess_increment': 0,      # seconds
    'lichess_rated': False       # True for rated
}

start_game(game_config)
```

## How It Works

### Architecture

1. **LichessGameManager** (`src/backend/lichess_manager.py`)
   - Creates game seeks using Board API
   - Streams incoming events to detect game start
   - Manages game state streaming
   - Sends moves to Lichess

2. **LichessPlayer** (`src/chess_sim/models/player.py`)
   - Represents the remote opponent
   - Receives moves via Board API stream
   - Implements BasePlayer interface

3. **Board API Streaming** (Not Polling!)
   - Uses `client.board.stream_incoming_events()` to detect game starts
   - Uses `client.board.stream_game_state(game_id)` for real-time updates
   - Sends moves with `client.board.make_move(game_id, move)`

### API Flow

```
1. Create Seek (quickmatch)
   └─> client.board.seek(time, increment, rated)
   
2. Stream Events (parallel)
   └─> client.board.stream_incoming_events()
       └─> Receive "gameStart" event → Get game_id
   
3. Stream Game State
   └─> client.board.stream_game_state(game_id)
       ├─> "gameFull" (first event) → Game info
       └─> "gameState" (updates) → New moves
   
4. Make Moves
   └─> client.board.make_move(game_id, move_uci)
```

## Comparison: Old vs New Implementation

### ❌ Old Implementation (Incorrect)
```python
# Uses Games API (for archived games only)
game_state = client.games.export(game_id)  # Polling, not streaming

# Checks game every N seconds
while True:
    time.sleep(2)  # Inefficient polling
    game_state = client.games.export(game_id)
```

### ✅ New Implementation (Correct)
```python
# Uses Board API (for real-time play)
game_stream = client.board.stream_game_state(game_id)  # Streaming!

# Real-time events
for event in game_stream:
    if event['type'] == 'gameState':
        # Instant move notification
```

## Troubleshooting

### "No active game found"
- Make sure you have Board API scope enabled in your token
- Check that your token is correctly configured

### "Failed to create quickmatch"
- Verify internet connection
- Check Lichess API status: https://lichess.org/api
- Ensure your account isn't restricted

### "Failed to send move"
- Game may have ended
- Move might be illegal
- Check network connection

### Stream timeouts
- Lichess sends keepalive every 7 seconds
- If stream stops, reconnect

## Rate Limits

- **Board API**: 8 seeks per second
- **Move making**: 20 moves per second per game
- Generally not a concern for human play

## Limitations

- Must have an active internet connection
- Requires valid Lichess account
- Board API only (not Bot API)
- Engine assistance is forbidden per Lichess fair play policy

## API Documentation

- **Lichess API**: https://lichess.org/api
- **Berserk Library**: https://github.com/lichess-org/berserk
- **Board API Section**: https://lichess.org/api#tag/Board

## Future Enhancements

Potential additions (not implemented):
- Accept/decline challenges
- View ongoing games and join
- Tournament play
- Time control customization in menu
- Auto-detect username from API
- Reconnection handling
- Chat functionality

---

**Questions?** Check the Lichess API documentation or the berserk library issues.
