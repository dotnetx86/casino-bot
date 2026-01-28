from aiogram.types import Message
from aiogram.filters import CommandStart, Command, Filter
from database import add_user, get_user_balance, get_leaderboard, update_balance
from database import cursor
from os import getenv


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        admin_ids = getenv("ADMIN_IDS", "").split(",")
        admin_ids = [int(aid.strip()) for aid in admin_ids if aid.strip()]
        return message.from_user.id in admin_ids


async def command_start_handler(message: Message) -> None:
    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(f"Hello, *{message.from_user.full_name}*!", parse_mode="Markdown")


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


async def admin_setbalance_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) != 3:
        await message.answer("Usage: /admin_setbalance <user_id> <balance>")
        return
    
    try:
        user_id = int(args[1])
        balance = float(args[2])
        
        if user_id == -1:
            user_id = message.from_user.id
        
        update_balance(user_id, balance)
        await message.answer(f"✅ Set balance for user {user_id} to ₪{balance}")
    except ValueError:
        await message.answer("❌ Invalid user_id or balance. Please provide valid numbers.")


async def admin_broadcast_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("Usage: /admin_broadcast <message>")
        return
    
    broadcast_message = args[1]
    
    try:
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        
        if not users:
            await message.answer("❌ No users found to broadcast to.")
            return
        
        bot = message.bot
        
        success_count = 0
        for user in users:
            try:
                await bot.send_message(user[0], f"📢 {broadcast_message}")
                success_count += 1
            except Exception:
                pass
        
        await message.answer(f"✅ Broadcast sent to {success_count}/{len(users)} users")
    except Exception as e:
        await message.answer(f"❌ Error during broadcast: {str(e)}")