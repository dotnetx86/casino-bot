# Casino Bot

A Telegram bot built with Python that lets users play casino games, manage virtual currency, and compete on leaderboards.

## Features

- 🎮 Three mini-games: Roulette, Mines, and Towers
- 💰 Virtual currency system with deposit/withdraw via Telegram Stars
- 📊 Leaderboard tracking
- 👨‍💼 Admin commands for user management and broadcasts
- 🗄️ SQLite database with async operations

## Requirements

- Python 3.8+
- Telegram Bot Token
- SQLite3 (included with Python)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dotnetx86/casino-bot
cd casino-bot
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r reqirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root directory:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here
```

**How to get your BOT_TOKEN:**
1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot` command
3. Copy the token provided

**How to get your ADMIN_ID:**
1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID

### 5. Run the bot

```bash
python main.py
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and get started with the bot |
| `/help` | Show available commands |
| `/balance` | Check your current balance |
| `/deposit` | Add Telegram Stars to your balance |
| `/withdraw` | Withdraw balance as Telegram Stars |
| `/leaderboard` | View top players by balance |
| `/roulette` | Play roulette game |
| `/mines` | Play mines game |
| `/towers` | Play towers game |
| `/admin_setbalance <user_id> <amount>` | [Admin] Set user balance |
| `/admin_broadcast <message>` | [Admin] Send message to all users |

## Project Structure

```
casino-bot/
├── main.py              # Bot entry point
├── database.py          # Database operations
├── handlers.py          # Command and message handlers
├── games/
│   ├── roulette.py     # Roulette game logic
│   ├── mines.py        # Mines game logic
│   └── towers.py       # Towers game logic
├── reqirements.txt     # Python dependencies
├── .env                # Environment variables (create this)
└── README.md           # This file
```

## Development

The bot uses:
- **aiogram 3.x** - Telegram Bot API framework
- **sqlite3** - Database
- **python-dotenv** - Environment variable management
- **asyncio** - Asynchronous operations

## License

See [LICENSE](LICENSE) for details.
