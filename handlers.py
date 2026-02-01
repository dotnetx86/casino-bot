from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment
from aiogram.filters import CommandStart, Command, Filter
from database import add_user, get_user_balance, get_leaderboard, update_balance, increment_balance
from database import cursor
from os import getenv
import requests

class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        admin_ids = getenv("ADMIN_IDS", "").split(",")
        admin_ids = [int(aid.strip()) for aid in admin_ids if aid.strip()]
        return message.from_user.id in admin_ids


async def command_start_handler(message: Message) -> None:
    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    balance = get_user_balance(message.from_user.id)
    
    welcome_text = f"""
🎰 **Welcome to Israel.game, {message.from_user.full_name}!** 🎰

Your current balance: **⭐{balance[0]}**

Get started by playing games or depositing more funds!

✡️ /random_text - Receive a random Torah text
💰 /deposit <amount> - Add Telegram Stars to your balance
🎮 /help - View all available commands and games
🏆 /leaderboard - Check top players

Good luck and have fun! 🍀
"""
    await message.answer(welcome_text, parse_mode="Markdown")


async def help_command(message: Message) -> None:
    help_text = """
🎰 **Israel.game Commands**

*User Commands:*
/start - Welcome message and balance check
/random_text - Get a random Torah text
/balance - Check your current balance
/deposit <amount> - Deposit Telegram Stars to your balance
/withdraw <amount> - Withdraw Stars from your balance
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

async def random_text_command(message: Message) -> None:
    response = requests.get("https://www.sefaria.org/api/texts/random?titles=Mishnah%20Peah")
    
    await message.answer(f"Random Torah text:\n<blockquote>{response.json()['text']}</blockquote>", parse_mode="html")

async def balance_command(message: Message) -> None:
    result = get_user_balance(message.from_user.id)
    if result:
        await message.answer(f"Your balance: ⭐{result[0]}")
    else:
        await message.answer("Balance not found.")


async def deposit_command(message: Message) -> None:
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Usage: /deposit <amount_in_stars>\nExample: /deposit 100")
        return
    
    try:
        amount = int(args[1])
        if amount <= 0:
            await message.answer("Amount must be positive.")
            return
    except ValueError:
        await message.answer("Invalid amount. Please provide a number.")
        return
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Deposit to Casino Bot",
        description=f"Deposit {amount} Telegram Stars to your balance.",
        payload=f"deposit_{message.from_user.id}_{amount}",
        currency="XTR",
        prices=[{"label": f"{amount} Stars", "amount": amount}],
        start_parameter="deposit"
    )


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def successful_payment_handler(message: Message) -> None:
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    if payload.startswith("deposit_"):
        _, user_id_str, amount_str = payload.split("_")
        user_id = int(user_id_str)
        amount = int(amount_str)
        
        increment_balance(user_id, amount)
        
        await message.answer(f"✅ Deposit successful! Added ⭐{amount} to your balance.")

async def withdraw_command(message: Message) -> None:
    await message.answer("Coming soon.")

async def leaderboard_command(message: Message) -> None:
    rows = get_leaderboard(10)
    if rows:
        text = "Leaderboard:\n" + "\n".join(f"{row[0]}: ⭐{row[1]}" for row in rows)
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
        await message.answer(f"✅ Set balance for user {user_id} to ⭐{balance}")
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