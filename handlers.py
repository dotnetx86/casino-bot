from aiogram import html
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from database import add_user, get_user_balance, get_leaderboard
from database import cursor


async def command_start_handler(message: Message) -> None:
    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(f"Hello, *{message.from_user.full_name}*!", parse_mode="MarkdownV2")


async def help_command(message: Message) -> None:
    help_text = """
🎰 **Casino Bot Commands**

*User Commands:*
/start - Initialize your account
/profile - View your profile information
/balance - Check your current balance
/leaderboard - View top 10 players

*Games:*
/towers <bet> [difficulty] - Play Towers game
  Difficulties: easy (3 cols, 1 bomb), medium (2 cols, 1 bomb), hard (3 cols, 2 bombs)
  Example: /towers 100 easy

/mines <bet> [grid_size] - Play Mines game
  Grid sizes: 5, 10, 15 (default: 10)
  Example: /mines 100 10

/roulette <bet> - Play Roulette game
  Example: /roulette 100

*Game Mechanics:*
🗼 Towers: Open tiles from bottom to top. Complete each row to unlock the next.
💣 Mines: Find safe spots and avoid mines. Each safe spot increases your winnings.
🎡 Roulette: Bet on a number (0-36) and spin the wheel.

Good luck! 🍀
"""
    await message.answer(help_text, parse_mode="Markdown")


async def profile_command(message: Message) -> None:
    cursor.execute("SELECT username, balance FROM users WHERE id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if user:
        await message.answer(f"Profile: {user[0]}, Balance: {user[1]}")
    else:
        await message.answer("Profile not found.")


async def balance_command(message: Message) -> None:
    result = get_user_balance(message.from_user.id)
    if result:
        await message.answer(f"Your balance: ₪{result[0]}")
    else:
        await message.answer("Balance not found.")


async def leaderboard_command(message: Message) -> None:
    rows = get_leaderboard(10)
    if rows:
        text = "Leaderboard:\n" + "\n".join(f"{row[0]}: {row[1]}" for row in rows)
        await message.answer(text)
    else:
        await message.answer("No users found.")
