import asyncio
import logging
import sqlite3
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

# Global database connection
conn = None
cursor = None

async def init_db():
    global conn, cursor
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 1000.0
    )''')
    conn.commit()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (message.from_user.id, message.from_user.username))
    conn.commit()
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer("This is a help message.")

@dp.message(Command("profile"))
async def profile_command(message: Message) -> None:
    cursor.execute("SELECT username, balance FROM users WHERE id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if user:
        await message.answer(f"Profile: {user[0]}, Balance: {user[1]}")
    else:
        await message.answer("Profile not found.")

@dp.message(Command("balance"))
async def balance_command(message: Message) -> None:
    cursor.execute("SELECT balance FROM users WHERE id = ?", (message.from_user.id,))
    result = cursor.fetchone()
    if result:
        await message.answer(f"Your balance: {result[0]}")
    else:
        await message.answer("Balance not found.")

@dp.message(Command("leaderboard"))
async def leaderboard_command(message: Message) -> None:
    cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    rows = cursor.fetchall()
    if rows:
        text = "Leaderboard:\n" + "\n".join(f"{row[0]}: {row[1]}" for row in rows)
        await message.answer(text)
    else:
        await message.answer("No users found.")

@dp.message(Command("roulette"))
async def roulette_command(message: Message) -> None:
    # Placeholder for roulette game logic
    # For simplicity, just deduct a bet and add winnings randomly
    import random
    bet = 100  # Assume fixed bet for now
    cursor.execute("SELECT balance FROM users WHERE id = ?", (message.from_user.id,))
    result = cursor.fetchone()
    if result and result[0] >= bet:
        outcome = random.choice(['win', 'lose'])
        if outcome == 'win':
            winnings = bet * 2
            new_balance = result[0] - bet + winnings
            await message.answer(f"You won! New balance: {new_balance}")
        else:
            new_balance = result[0] - bet
            await message.answer(f"You lost! New balance: {new_balance}")
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, message.from_user.id))
        conn.commit()
    else:
        await message.answer("Insufficient balance or profile not found.")

@dp.message(Command("mines"))
async def mines_command(message: Message) -> None:
    # Placeholder for mines game logic
    # Simple version: random win/lose
    import random
    bet = 50
    cursor.execute("SELECT balance FROM users WHERE id = ?", (message.from_user.id,))
    result = cursor.fetchone()
    if result and result[0] >= bet:
        if random.random() > 0.5:
            new_balance = result[0] + bet
            await message.answer(f"You won! New balance: {new_balance}")
        else:
            new_balance = result[0] - bet
            await message.answer(f"You lost! New balance: {new_balance}")
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, message.from_user.id))
        conn.commit()
    else:
        await message.answer("Insufficient balance or profile not found.")

@dp.message(Command("towers"))
async def towers_command(message: Message) -> None:
    # Placeholder for towers game logic
    # Simple version: random win/lose
    import random
    bet = 75
    cursor.execute("SELECT balance FROM users WHERE id = ?", (message.from_user.id,))
    result = cursor.fetchone()
    if result and result[0] >= bet:
        if random.random() > 0.4:
            new_balance = result[0] + bet * 1.5
            await message.answer(f"You won! New balance: {new_balance}")
        else:
            new_balance = result[0] - bet
            await message.answer(f"You lost! New balance: {new_balance}")
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, message.from_user.id))
        conn.commit()
    else:
        await message.answer("Insufficient balance or profile not found.")

@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    init_db()
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())