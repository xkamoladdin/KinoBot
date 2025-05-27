





import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7485385336:AAFAJyz8Yal28TU3bgv0Gn0sj-JBUmhLWUU'
GROUP_USERNAME = '@sanat_mebel'  # Masalan: '@sanat_mebel'
ADMIN_ID = 7331395623  # Admin Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Guruh tugmasi
join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Guruhga qo'shilish", url=f"https://t.me/{GROUP_USERNAME[1:]}")],
    [InlineKeyboardButton(text="Qo‘shildim ✅", callback_data="check_join")]
])

async def get_movie_list_text():
    try:
        with open("kinolar.json", "r") as f:
            kinolar = json.load(f)
    except:
        kinolar = {}

    if kinolar:
        text = "Salom!\n\n🎥 Mavjud kinolar ro'yxati:\n\n"
        for code, info in kinolar.items():
            text += f"🆔 Kod: {code} | 🎬 Kino: {info['name']}\n"
        text += "\nKod yozing:"
    else:
        text = "Salom!\n\n⛔ Hozircha hech qanday kino mavjud emas.\nKod yozing:"
    return text

# /start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, message.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            text = await get_movie_list_text()
            await message.answer(text)
        else:
            await message.answer("Botdan foydalanish uchun guruhga qo‘shiling:", reply_markup=join_keyboard)
    except:
        await message.answer("Botdan foydalanish uchun guruhga qo‘shiling:", reply_markup=join_keyboard)

# Guruhga qo‘shilganini tekshirish
@dp.callback_query_handler(lambda c: c.data == "check_join")
async def check_join(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            await callback_query.answer("Siz guruh a'zosisiz!", show_alert=True)
            text = await get_movie_list_text()
            await bot.send_message(user_id, text)
        else:
            await callback_query.answer("Hali guruhga qo‘shilmagansiz.", show_alert=True)
    except:
        await callback_query.answer("Xatolik yuz berdi yoki siz guruhda emassiz.", show_alert=True)

# /addmovie komandasi (admin uchun)
@dp.message_handler(commands=['addmovie'])
async def add_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Bu komandani faqat admin ishlata oladi.")
        return

    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("Kino videosiga javoban /addmovie 1-Titanic deb yozing.")
        return

    args = message.get_args()
    if '-' not in args:
        await message.reply("Iltimos, formatni to‘g‘ri kiriting: /addmovie 1-Titanic")
        return

    code, name = args.split('-', 1)
    code = code.strip()
    name = name.strip()
    file_id = message.reply_to_message.video.file_id

    try:
        with open("kinolar.json", "r") as f:
            kinolar = json.load(f)
    except:
        kinolar = {}

    kinolar[code] = {
        "name": name,
        "file_id": file_id
    }

    with open("kinolar.json", "w") as f:
        json.dump(kinolar, f, indent=4)

    await message.reply(f"✅ Kino saqlandi!\n📼 Nomi: {name}\n🆔 Kodi: {code}")

# Kod bo‘yicha kino qidirish
@dp.message_handler()
async def search_movie(message: types.Message):
    code = message.text.strip()

    try:
        with open("kinolar.json", "r") as f:
            kinolar = json.load(f)
    except:
        kinolar = {}

    if code in kinolar:
        movie = kinolar[code]
        await bot.send_video(
            message.chat.id,
            movie["file_id"],
            caption=f"🎬 Kino: {movie['name']}\n🎞 Kod: {code}"
        )
    else:
        await message.reply("Kechirasiz, bu kod bo‘yicha kino topilmadi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
