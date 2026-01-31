import asyncio
from dataclasses import dataclass
import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_balance, update_balance, increment_balance, cursor, conn

config = {
    "red_coefficient": 2,
    "black_coefficient": 2,
    "yellow_coefficient": 14,
    "red_probability": 0.45,
    "black_probability": 0.45,
    "yellow_probability": 0.1
}

async def roulette_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("Usage: /roulette <bet_amount> <color>\nColors: red (🟥), black (⬛), yellow (🟨)\nExample: /roulette 100 red")
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
    
    increment_balance(message.from_user.id, -bet)
    
    pattern = ["🟥", "⬛", "🟨"]
    spin = random.choices(pattern, k=24, weights=[config["red_probability"], config["black_probability"], config["yellow_probability"]])
    
    spin[16] = bet_color
    
    line = "".join(spin[:9]) + "\n➖➖➖➖🔺➖➖➖➖"
    spinning_msg = await message.answer(line)
    result_symbol = spin[19]
    
    for i in range(1, 16):
        newline = "".join(spin[i:i+9]) + "\n➖➖➖➖🔺➖➖➖➖"
        if line != newline:
            await spinning_msg.edit_text(newline)
            line = newline
        await asyncio.sleep(0.05 + i * 0.025)
    await asyncio.sleep(0.5)
    
    winnings = 0
    if result_symbol == bet_color:
        if bet_color == "🟥":
            winnings = bet * config["red_coefficient"]
        elif bet_color == "⬛":
            winnings = bet * config["black_coefficient"]
        elif bet_color == "🟨":
            winnings = bet * config["yellow_coefficient"]
        increment_balance(message.from_user.id, winnings)
        result_text = f"🎉 You won ⭐{winnings}!\nBalance: ⭐{get_user_balance(message.from_user.id)[0]}"
    else:
        result_text = f"😞 You lost ⭐{bet}.\nBalance: ⭐{get_user_balance(message.from_user.id)[0]}"
    
    play_again_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🎮 Play Again", switch_inline_query_current_chat=f"/roulette {bet} {color_input}")
        ]]
    )
    
    await spinning_msg.edit_text(f"{line}\n\n{result_text}", reply_markup=play_again_keyboard)
