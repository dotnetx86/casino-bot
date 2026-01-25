import asyncio
from dataclasses import dataclass
import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_balance, update_balance, cursor, conn

@dataclass
class rouletteSettings:
    min_bet: int = 10
    max_bet: int = 1000
    red_probability: float = 0.45
    black_probability: float = 0.45
    yellow_probability: float = 0.1
    red_coefficient: float = 2.0
    black_coefficient: float = 2.0
    yellow_coefficient: float = 9.0

async def roulette_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("Usage: /roulette <bet_amount> <color>\nColors: red (🟥), black (⬛), yellow (🟨)")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("Invalid bet amount. Please enter a number.")
        return
    
    color_input = args[2].lower()
    color_map = {
        "red": "🟥",
        "black": "⬛",
        "yellow": "🟨"
    }
    
    if color_input not in color_map:
        await message.answer("Invalid color. Use: red, black, or yellow")
        return
    
    bet_color = color_map[color_input]
    
    result = get_user_balance(message.from_user.id)
    if not result or result[0] < bet:
        await message.answer("Insufficient balance.")
        return
    
    pattern = ["🟥", "⬛", "🟨"]
    spin = random.choices(pattern, k=24, weights=[rouletteSettings.red_probability, rouletteSettings.black_probability, rouletteSettings.yellow_probability])
    
    spin[16] = bet_color
    
    spinning_msg = await message.answer(f"{"".join(spin[:9])}\n➖➖➖➖🔺➖➖➖➖")
    result_symbol = spin[19]
    
    line = ""
    for i in range(1, 16):
        newline = "".join(spin[i:i+9]) + "\n➖➖➖➖🔺➖➖➖➖"
        if line != newline:
            await spinning_msg.edit_text(newline)
            line = newline
        await asyncio.sleep(0.05 + i * 0.025)
    await asyncio.sleep(0.5)
    
    if result_symbol == bet_color:
        match result_symbol:
            case "🟥":
                winnings = bet * rouletteSettings.red_coefficient
                new_balance = result[0] - bet + winnings
                result_text = f"🎉 You won! +{winnings}\nNew balance: {new_balance}"
            case "⬛":
                winnings = bet * rouletteSettings.black_coefficient
                new_balance = result[0] - bet + winnings
                result_text = f"🎉 You won! +{winnings}\nNew balance: {new_balance}"
            case "🟨":
                winnings = bet * rouletteSettings.yellow_coefficient
                new_balance = result[0] - bet + winnings
                result_text = f"🎉 You won! +{winnings}\nNew balance: {new_balance}"
            case _:
                new_balance = result[0] - bet
                result_text = f"💔 You lost! -{bet}\nNew balance: {new_balance}"
    else:
        new_balance = result[0] - bet
        result_text = f"💔 You lost! -{bet}\nNew balance: {new_balance}"
    
    play_again_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🎮 Play Again", switch_inline_query_current_chat=f"/roulette {bet} {color_input}")
        ]]
    )
    
    await spinning_msg.edit_text(f"{line}\n\n{result_text}", reply_markup=play_again_keyboard)
    
    update_balance(message.from_user.id, new_balance)
