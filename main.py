import json
import os
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
GROUP_USERNAME = os.getenv("GROUP_USERNAME")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Ro‘yxatdan o‘tgan foydalanuvchilar
registered_users = set()
temp_movies = {}

# Kino fayli
try:
    with open("kinolar.json", "r") as f:
        kinolar = json.load(f)
except:
    kinolar = {}

# FSM
class AddMovieState(StatesGroup):
    waiting_for_code = State()

# Join tugmasi
join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("Guruhga qo'shilish", url=f"https://t.me/{GROUP_USERNAME[1:]}")],
    [InlineKeyboardButton("Qo'shildim ✅", callback_data="check_join")]
])

# Faqat private chatga ruxsat
@dp.message_handler(lambda msg: msg.chat.type != 'private')
async def no_group(msg: types.Message):
    await msg.reply("❗ Men faqat shaxsiy chatda ishlayman.")

# Reklama filtr
REKLAMA_SOZLAR = ["http", "https", ".ru", "vpn", "@", "t.me", "instagram", "youtube"]

@dp.message_handler(lambda msg: any(bad in msg.text.lower() for bad in REKLAMA_SOZLAR))
async def reklama_block(msg: types.Message):
    await msg.delete()
    await msg.answer("❌ Reklama yuborish taqiqlangan.")

# /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, message.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            registered_users.add(message.from_user.id)
            await message.reply("Salom! Kino kodini yuboring.")
        else:
            await message.answer("Botdan foydalanish uchun guruhga qo'shiling.", reply_markup=join_keyboard)
    except:
        await message.answer("Botdan foydalanish uchun guruhga qo'shiling.", reply_markup=join_keyboard)

# Guruhga qo‘shilganligini tekshirish
@dp.callback_query_handler(lambda c: c.data == "check_join")
async def check_join(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            registered_users.add(user_id)
            await callback_query.answer("Siz guruh a'zosisiz!", show_alert=True)
            await bot.send_message(user_id, "Botga xush kelibsiz! Kino kodini yozing.")
        else:
            await callback_query.answer("Hali guruhga qo‘shilmadingiz.", show_alert=True)
    except:
        await callback_query.answer("Xatolik yoki guruhga a’zo emassiz.", show_alert=True)

# /addmovie (admin)
@dp.message_handler(commands=['addmovie'])
async def add_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Faqat admin qo‘shishi mumkin.")
        return

    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("Kino videosiga javoban /addmovie kino_nomi deb yozing.")
        return

    kino_nomi = message.get_args().strip().lower()
    if not kino_nomi:
        await message.reply("Kino nomini kiriting: /addmovie kino_nomi")
        return

    file_id = message.reply_to_message.video.file_id
    temp_movies[message.from_user.id] = {
        "file_id": file_id,
        "name": kino_nomi
    }

    await message.reply("Endi kino kodini kiriting (masalan: #K123):")
    await AddMovieState.waiting_for_code.set()

# Kodni qabul qilish
@dp.message_handler(state=AddMovieState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in temp_movies:
        await message.reply("Xatolik. /addmovie bilan qayta urinib ko‘ring.")
        await state.finish()
        return

    code = message.text.strip()
    movie = temp_movies.pop(user_id)
    kino_nomi = movie["name"]

    kinolar[kino_nomi] = {
        "file_id": movie["file_id"],
        "code": code
    }

    with open("kinolar.json", "w") as f:
        json.dump(kinolar, f, indent=4)

    await message.reply(f"✅ '{kino_nomi}' saqlandi!")
    await state.finish()

# Kino yuborish
@dp.message_handler()
async def send_movie(message: types.Message):
    if message.from_user.id not in registered_users:
        await message.reply("❗ Botdan foydalanish uchun avval /start buyrug‘ini yuboring.")
        return

    code = message.text.strip()
    for kino_nomi, data in kinolar.items():
        if isinstance(data, dict) and data.get("code") == code:
            caption = f"🎬 Kino nomi: {kino_nomi.title()}\n🎞 Kod: {code}"
            await bot.send_video(message.chat.id, data["file_id"], caption=caption)
            return

    await message.reply("❗ Bunday kod bilan kino topilmadi.")

# Start
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
