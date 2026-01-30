import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_user_balance, update_balance, increment_balance, cursor, conn

active_games = {}

DIFFICULTIES = {
    "easy": {"columns": 3, "bombs": 1, "multiplier_per_floor": 1.4},
    "medium": {"columns": 2, "bombs": 1, "multiplier_per_floor": 1.9},
    "hard": {"columns": 3, "bombs": 2, "multiplier_per_floor": 2.8}
}


async def towers_command(message: Message) -> None:
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("Usage: /towers <bet_amount> [difficulty]\nDifficulty: easy (3 cols, 1 bomb), medium (2 cols, 1 bomb), hard (3 cols, 2 bombs)\nExample: /towers 100 easy")
        return
    
    try:
        bet = int(args[1])
    except ValueError:
        await message.answer("Invalid bet amount. Please enter a number.")
        return
    
    difficulty = args[2].lower() if len(args) > 2 else "easy"
    if difficulty not in DIFFICULTIES:
        await message.answer(f"Invalid difficulty. Choose: {', '.join(DIFFICULTIES.keys())}")
        return
    
    await start_new_towers_game(message, bet, difficulty)


async def start_new_towers_game(message: Message, bet: int, difficulty: str, user_id: int = None) -> None:
    if user_id is None:
        user_id = message.from_user.id
    
    result = get_user_balance(user_id)
    if not result or result[0] < bet:
        await message.answer("Insufficient balance.")
        return
    
    increment_balance(user_id, -bet)

    config = DIFFICULTIES[difficulty]
    
    towers_board = []
    for row_idx in range(5):
        row = [True] * config["bombs"] + [False] * (config["columns"] - config["bombs"])
        random.shuffle(row)
        towers_board.extend(row)

    winnings = bet
    game_state = {
        "user_id": user_id,
        "bet": bet,
        "difficulty": difficulty,
        "board": towers_board,
        "floor": 4,
        "multiplier": 1.0,
        "won": False,
        "columns": config["columns"],
        "multiplier_per_floor": config["multiplier_per_floor"],
        "game_over": False
    }
    
    keyboard = create_towers_keyboard(game_state)
    game_msg = await message.answer(
        f"🗼 Towers Game Started!\nDifficulty: {difficulty.upper()}\nBet: {bet}\nWinnings: {winnings}\n\nClick tiles to reveal. Hit a bomb = lose!",
        reply_markup=keyboard
    )
    
    game_key = f"{user_id}_{game_msg.message_id}"
    active_games[game_key] = game_state



async def towers_callback(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.message_id
    game_key = f"{user_id}_{msg_id}"
    
    if game_key not in active_games:
        await callback_query.answer("Game not found or expired.", show_alert=True)
        return
    
    game_state = active_games[game_key]
    data = callback_query.data
    
    if data == "towers_noop":
        await callback_query.answer()
        return
    
    action = data.split("_")[1]
    
    if action == "newgame":
        await callback_query.answer()
        del active_games[game_key]
        await start_new_towers_game(callback_query.message, game_state["bet"], game_state["difficulty"], user_id)
        return
    
    if game_state["game_over"]:
        await callback_query.answer("Game over! Start a new game.", show_alert=True)
        return
    
    if action == "cashout":        
        winnings = int(game_state["bet"] * game_state["multiplier"])
        increment_balance(user_id, winnings)
        
        text = f"💰 Cashed out!\nWinnings: +{winnings}"
        game_state["game_over"] = True
        keyboard = create_towers_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Won {winnings}!")
        return
    
    try:
        tile = int(action)
    except ValueError:
        await callback_query.answer()
        return
    
    if game_state["game_over"]:
        await callback_query.answer()
        return
    
    
    columns = game_state["columns"]
    row_idx = tile // columns
    
    if row_idx != game_state["floor"]:
        await callback_query.answer("You can only reveal the current floor!", show_alert=True)
        return
    
    hit_bomb = game_state["board"][tile]
    
    if hit_bomb:
        game_state["game_over"] = True
        
        text = f"💣 BOOM! You hit a bomb!\nLost: -{game_state['bet']}\n"
        
        keyboard = create_towers_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer("You hit a bomb!")
    else:
        game_state["multiplier"] *= game_state["multiplier_per_floor"]
        winnings = int(game_state["bet"] * game_state["multiplier"])

        text = f"🗼 Towers Game\nDifficulty: {game_state['difficulty'].upper()}\nBet: {game_state['bet']}\nMultiplier: {game_state['multiplier']:.1f}x\nWinnings: {winnings}\n\nClick tiles to reveal. Hit a bomb = lose!"
        game_state["floor"] -= 1
        keyboard = create_towers_keyboard(game_state)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer(f"Safe! Multiplier: {game_state['multiplier']:.1f}x")


def create_towers_keyboard(game_state: dict) -> InlineKeyboardMarkup:
    keyboard = []
    board = game_state["board"]
    game_over = game_state["game_over"]
    columns = game_state["columns"]
    floor = game_state["floor"]
    num_tiles = len(board)
    rows = num_tiles // columns
    
    for row in range(rows):
        row_buttons = []
        for col in range(columns):
            tile_idx = row * columns + col
            
            if floor < row or game_over:
                if board[tile_idx]:
                    button_text = "💣"
                else:
                    button_text = "✅"
            else:
                button_text = "⬜"
            
            if not game_over: # and floor <= row:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data=f"towers_{tile_idx}")
                )
            else:
                row_buttons.append(
                    InlineKeyboardButton(text=button_text, callback_data="towers_noop")
                )
        
        keyboard.append(row_buttons)
    
    action_row = []
    
    if game_state["game_over"]:
        action_row.append(
            InlineKeyboardButton(text="🔄 New Game", callback_data="towers_newgame")
        )
    else:
        action_row.append(
            InlineKeyboardButton(text="💰 Cash Out", callback_data="towers_cashout")
        )    
    
        
    keyboard.append(action_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
