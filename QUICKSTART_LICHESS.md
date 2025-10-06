# Quick Start: Lichess Online Play

## 1. Get Your API Token
1. Go to https://lichess.org/account/oauth/token
2. Create token with scope: **"Board: Play games with the Board API"**
3. Copy the token (starts with `lip_`)

## 2. Setup Environment
```bash
# Copy the template
cp .env.example .env

# Edit .env and paste your token
nano .env  # or use any text editor
```

Your `.env` should look like:
```
LICHESS_API_TOKEN=lip_your_actual_token_here
```

## 3. Install Dependencies
```bash
pip install berserk python-dotenv
```

## 4. Run & Play
```bash
python src/chess_sim/main.py
```

Navigate: **Main Menu → Play Online → Start Quickmatch**

## Time Controls Available
- 1+0 (Bullet)
- 3+0 (Blitz)
- 5+0 (Blitz)
- 10+0 (Rapid)
- 15+10 (Rapid)

## How to Play
1. Select time control
2. Choose Casual or Rated
3. Start Quickmatch (waits for opponent)
4. Enter your Lichess username when prompted
5. Play! Enter moves in UCI format (e.g., `e2e4`)

---

For detailed documentation, see `LICHESS_INTEGRATION.md`
