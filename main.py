import os
import logging

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import Message
import asyncio

API_TOKEN = os.getenv("API_TOKEN")
MONGO_URI = os.getenv("MONGO_DB")

if not API_TOKEN:
    raise ValueError("No API token provided")
print(f"API_TOKEN: {API_TOKEN}")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

client = MongoClient(MONGO_URI)
db = client["test"]
user_collection = db["twofactorauths"]

class Form(StatesGroup):
    awaiting_token = State()
    awaiting_2fa = State()

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Hi! I'm a simple bot to demonstrate how to implement 2FA in your bot. "
        "To get started, please set your token using /token <your_token>."
    )

@router.message(Command("token"))
async def set_token(message: Message, state: FSMContext):
    command, *token = message.text.split()

    if token:
        token = token[0]
        data = user_collection.find_one({"token": token})
        
        if data:
            await message.reply(
                f"Token set successfully! Your code: <code>{data['code']}</code>",
                parse_mode=ParseMode.HTML,
            )
            await state.update_data(token=token, code=data['code'])
            await Form.awaiting_2fa.set()
        else:
            await message.reply("Invalid token provided.")
    else:
        await message.reply("Please provide a token.")

    await bot.delete_message(message.chat.id, message.message_id)

@router.message(Form.awaiting_2fa)
async def process_2fa(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if message.text == user_data['code']:
        await message.reply("2FA successful!")
        await state.clear()
    else:
        await message.reply("Invalid two-factor authentication code. Please try again.")

dp.include_router(router)

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
