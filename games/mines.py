import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_user_balance, update_balance, cursor, conn

active_games = {}


async def mines_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("Usage: /mines <bet_amount>\nExample: /mines 100")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("Invalid bet amount. Please enter a number.")
        return
    
    await start_new_mines_game(message, bet)


async def start_new_mines_game(message: Message, bet: int, user_id: int = None) -> None:
    if user_id is None:
        user_id = message.from_user.id
    
    result = get_user_balance(user_id)
    if not result or result[0] < bet:
        await message.answer("Insufficient balance.")
        return
    
    initial_balance = result[0]
    
    mines_board = [random.random() < 0.25 for _ in range(9)]
    revealed = [False] * 9
    winnings = bet
    game_state = {
        "user_id": user_id,
        "bet": bet,
        "initial_balance": initial_balance,
        "board": mines_board,
        "revealed": revealed,
        "winnings": winnings,
        "game_over": False,
        "won": False
    }
    
    keyboard = create_mines_keyboard(game_state)
    game_msg = await message.answer(
        f"💣 Mines Game Started!\nBet: {bet}\nWinnings: {winnings}\n\nClick tiles to reveal. Hit a mine = lose!",
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
    
    if action == "cashout":
        balance = game_state["initial_balance"]
        new_balance = balance + game_state["winnings"]
        update_balance(user_id, new_balance)
        
        text = f"💰 Cashed out!\nWinnings: +{game_state['winnings']}\nNew balance: {new_balance}"
        game_state["game_over"] = True
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Won {game_state['winnings']}!")
        return
    
    if action == "newgame":
        await callback_query.answer()
        del active_games[game_key]
        await start_new_mines_game(callback_query.message, game_state["bet"], user_id)
        return
    
    try:
        tile = int(action)
    except ValueError:
        await callback_query.answer()
        return
    
    if game_state["game_over"]:
        await callback_query.answer()
        return
    
    if game_state["revealed"][tile]:
        await callback_query.answer("Already revealed!", show_alert=False)
        return
    
    game_state["revealed"][tile] = True
    
    if game_state["board"][tile]:
        game_state["game_over"] = True
        text = f"💣 BOOM! You hit a mine!\nLost: -{game_state['bet']}\n"
        
        new_balance = game_state["initial_balance"] - game_state["bet"]
        update_balance(user_id, new_balance)
        
        text += f"New balance: {new_balance}"
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer("You hit a mine!")
    else:
        safe_tiles = sum(1 for i, revealed in enumerate(game_state["revealed"]) if revealed and not game_state["board"][i])
        game_state["winnings"] = game_state["bet"] * (1 + safe_tiles * 0.5)
        
        text = f"💣 Mines Game\nBet: {game_state['bet']}\nWinnings: {game_state['winnings']:.0f}\nSafe tiles: {safe_tiles}\n\nClick tiles to reveal. Hit a mine = lose!"
        keyboard = create_mines_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Safe! Winnings: {game_state['winnings']:.0f}")


def create_mines_keyboard(game_state: dict) -> InlineKeyboardMarkup:
    keyboard = []
    board = game_state["board"]
    revealed = game_state["revealed"]
    game_over = game_state["game_over"]
    
    for row in range(3):
        row_buttons = []
        for col in range(3):
            tile_idx = row * 3 + col
            
            if revealed[tile_idx]:
                if board[tile_idx]:
                    button_text = "💣"
                else:
                    button_text = "✅"
            else:
                button_text = "⬜"
            
            if not game_over and not revealed[tile_idx]:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data=f"mines_{tile_idx}")
                )
            else:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data="mines_noop")
                )
        
        keyboard.append(row_buttons)
    
    action_row = [
        InlineKeyboardButton(text="💰 Cash Out", callback_data="mines_cashout"),
        InlineKeyboardButton(text="🔄 New Game", callback_data="mines_newgame")
    ]
    keyboard.append(action_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
