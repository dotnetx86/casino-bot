import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_user_balance, update_balance, increment_balance, cursor, conn

active_games = {}

async def mines_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("Usage: /mines <bet_amount> <mines_amount>\nExample: /mines 100 5")
        return
    
    try:
        bet = int(args[1])
        mines = int(args[2])
        
        if mines < 1 or mines > 24:
            await message.answer("Mines amount must be between 1 and 24.")
            return
    except ValueError:
        await message.answer("Invalid bet amount or mines amount. Please enter numbers.")
        return
    
    await start_new_mines_game(message, bet, mines)


async def start_new_mines_game(message: Message, bet: int, mines: int, user_id: int = None) -> None:
    if user_id is None:
        user_id = message.from_user.id
    
    result = get_user_balance(user_id)
    if not result or result[0] < bet:
        await message.answer("Insufficient balance.")
        return
    
    increment_balance(user_id, -bet)
    
    towers_board = [True] * mines + [False] * (25 - mines)
    random.shuffle(towers_board)

    game_state = {
        "user_id": user_id,
        "bet": bet,
        "mines": mines,
        "board": towers_board,
        "game_over": False,
        "winnings": bet,
        "revealed": set()
    }
    
    keyboard = create_mines_keyboard(game_state)
    game_msg = await message.answer(
        f"🗼 Mines Game Started!\nMines: {mines}\nBet: ⭐{bet}\nWinnings: ⭐{bet}\n\nClick tiles to reveal. Hit a mine = lose!",
        reply_markup=keyboard
    )
    
    game_key = f"{user_id}_{game_msg.message_id}"
    active_games[game_key] = game_state



async def mines_callback(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.message_id
    game_key = f"{user_id}_{msg_id}"
    
    if game_key not in active_games:
        await callback_query.answer("Game not found or expired.", show_alert=True)
        return
    
    game_state = active_games[game_key]
    data = callback_query.data
    
    if data == "mines_noop":
        await callback_query.answer()
        return
    
    action = data.split("_")[1]
    
    if action == "newgame":
        await callback_query.answer()
        del active_games[game_key]
        await start_new_mines_game(callback_query.message, game_state["bet"], game_state["mines"], user_id)
        return
    
    if game_state["game_over"]:
        await callback_query.answer("Game over! Start a new game.", show_alert=True)
        return
    
    if action == "cashout":
        winnings = game_state["winnings"]
        increment_balance(user_id, winnings)
        
        text = f"💰 Cashed out!\nWinnings: ⭐{winnings}\nBalance: ⭐{get_user_balance(user_id)[0]}"
        game_state["game_over"] = True
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Won ⭐{winnings}!")
        return
    
    try:
        tile = int(action)
    except ValueError:
        await callback_query.answer()
        return
    
    if game_state["game_over"]:
        await callback_query.answer()
        return
    
    if tile in game_state["revealed"]:
        await callback_query.answer("Tile already revealed!", show_alert=True)
        return
    
    hit_bomb = game_state["board"][tile]
    
    game_state["revealed"].add(tile)
    
    if hit_bomb:
        game_state["game_over"] = True
        
        text = f"💣 BOOM! You hit a bomb!\nLost: ⭐{game_state['bet']}\nBalance: ⭐{get_user_balance(user_id)[0]}"
        
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer("You hit a bomb!")
    else:
        multiplier = 1.0
        for i in range(len(game_state["revealed"])):
            multiplier *= (25 - i) / (25 - game_state["mines"] - i)
        multiplier *= (1 - 0.03 * game_state["mines"])
        
        winnings = int(game_state["bet"] * multiplier)
        game_state["winnings"] = winnings

        text = f"🗼 Mines Game\nMines: {game_state['mines']}\nBet: ⭐{game_state['bet']}\nMultiplier: {multiplier:.2f}x\nWinnings: ⭐{winnings}\n\nClick tiles to reveal. Hit a mine = lose!"
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Safe! Multiplier: {multiplier:.2f}x")

def create_mines_keyboard(game_state: dict) -> InlineKeyboardMarkup:
    keyboard = []
    board = game_state["board"]
    game_over = game_state["game_over"]
    
    for row in range(5):
        row_buttons = []
        for col in range(5):
            tile_idx = row * 5 + col
            if tile_idx in game_state["revealed"] or game_over:
                if board[tile_idx]:
                    button_text = "💣"
                else:
                    button_text = "✅"
            else:
                button_text = "⬜"
            
            if not game_over:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data=f"mines_{tile_idx}")
                )
            else:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data="mines_noop")
                )
            
        keyboard.append(row_buttons)
    
    action_row = []
    
    if game_state["game_over"]:
        action_row.append(
            InlineKeyboardButton(text="🔄 New Game", callback_data="mines_newgame")
        )
    else:
        action_row.append(
            InlineKeyboardButton(text="💰 Cash Out", callback_data="mines_cashout")
        )    
    
        
    keyboard.append(action_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
