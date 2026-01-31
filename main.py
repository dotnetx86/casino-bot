import asyncio
import logging
import sys

from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command

from database import init_db
from handlers import (
    command_start_handler,
    help_command,
    balance_command,
    deposit_command,
    leaderboard_command,
    admin_setbalance_command,
    admin_broadcast_command,
    pre_checkout_handler,
    successful_payment_handler,
    IsAdmin
)
from games.roulette import roulette_command
from games.mines import mines_command, mines_callback
from games.towers import towers_command, towers_callback

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

dp.message.register(command_start_handler, CommandStart())
dp.message.register(help_command, Command("help"))
dp.message.register(balance_command, Command("balance"))
dp.message.register(deposit_command, Command("deposit"))
dp.message.register(leaderboard_command, Command("leaderboard"))
dp.message.register(roulette_command, Command("roulette"))
dp.message.register(mines_command, Command("mines"))
dp.message.register(towers_command, Command("towers"))
dp.message.register(admin_setbalance_command, Command("admin_setbalance"), IsAdmin())
dp.message.register(admin_broadcast_command, Command("admin_broadcast"), IsAdmin())

dp.pre_checkout_query.register(pre_checkout_handler)
dp.message.register(successful_payment_handler, lambda message: message.content_type == "successful_payment")

dp.callback_query.register(mines_callback, lambda c: c.data.startswith("mines_"))
dp.callback_query.register(towers_callback, lambda c: c.data.startswith("towers_"))


async def main() -> None:
    await init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())