import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = '7599546479:AAGL_ipn2mqQaRTKjWRaJ7Y2Ic16Juv9VUs'
GROUP_USERNAME = '@sanat_mebel'  # Masalan: '@sanat_mebel'
ADMIN_ID = 7331395623  # Admin Telegram ID

# FSM (holatlar)
class AddMovieState(StatesGroup):
    waiting_for_code = State()

# Bot va storage
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Kinolarni yuklab olish
try:
    with open("kinolar.json", "r") as f:
        kinolar = json.load(f)
except:
    kinolar = {}

# Guruh tugmalari
join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Guruhga qo'shilish", url=f"https://t.me/{GROUP_USERNAME[1:]}")],
    [InlineKeyboardButton(text="Qo'shilganman ✅", callback_data="check_join")]
])

# /start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, message.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            await message.reply("Salom! Kino kodini yozing, men sizga uni yuboraman.")
        else:
            await message.answer(
                "Salom! Botdan foydalanish uchun avvalo guruhimizga qo'shiling.",
                reply_markup=join_keyboard
            )
    except Exception:
        await message.answer(
            "Salom! Botdan foydalanish uchun avvalo guruhimizga qo'shiling.",
            reply_markup=join_keyboard
        )

# Guruhga qo'shilganlikni tekshirish
@dp.callback_query_handler(lambda c: c.data == "check_join")
async def process_check_join(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            await callback_query.answer("Siz guruh a'zosisiz!", show_alert=True)
            await bot.send_message(user_id, "Botga xush kelibsiz! Endi kino nomini yozing.")
        else:
            await callback_query.answer("Siz hali guruhga qo'shilmagansiz.", show_alert=True)
    except Exception:
        await callback_query.answer("Xatolik yuz berdi yoki siz guruh a'zosi emassiz.", show_alert=True)

# Vaqtinchalik saqlovchi dict
temp_movies = {}

# /addmovie komandasi
@dp.message_handler(commands=['addmovie'])
async def add_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Faqat admin qo'shishi mumkin.")
        return

    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("Iltimos, kino videosiga javoban /addmovie kino_nomi deb yozing.")
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

# Kino kodini qabul qilish
@dp.message_handler(state=AddMovieState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in temp_movies:
        await message.reply("Xatolik. Iltimos, /addmovie komandasi bilan qaytadan boshlang.")
        await state.finish()
        return

    code = message.text.strip()
    movie = temp_movies.pop(user_id)
    kino_nomi = movie["name"]

    # Saqlash
    kinolar[kino_nomi] = {
        "file_id": movie["file_id"],
        "code": code
    }

    with open("kinolar.json", "w") as f:
        json.dump(kinolar, f, indent=4)

    await message.reply(f"✅ '{kino_nomi}' nomli kino kodi bilan saqlandi!")
    await state.finish()

# Kino yuborish
@dp.message_handler()
async def send_movie_by_code(message: types.Message):
    code = message.text.strip()

    # Kod bo'yicha kinoni izlash
    for kino_nomi, kino_data in kinolar.items():
        if isinstance(kino_data, dict) and kino_data.get("code") == code:
            caption = f"🎬 Kino nomi: {kino_nomi.title()}\n🎞 Kino kodi: {code}"
            await bot.send_video(message.chat.id, kino_data["file_id"], caption=caption)
            return

    # Agar topilmasa
    await message.reply("Kechirasiz, bu kod bo‘yicha kino topilmadi.")

# Botni ishga tushirish
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
