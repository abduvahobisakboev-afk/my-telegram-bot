import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import speech_recognition as sr
from pydub import AudioSegment

# --- SOZLAMALAR ---
# Siz bergan eng yangi token
TOKEN = "8302977160:AAEJXME09z2ZdMkRQE7WDJN20bEoWkE5lCg" 
BTN_VIEW = "🗄 Saqlanganlarni ko'rish"
BTN_VOICE = "🎤 Ovozni matnga aylantirish"
BTN_HOME = "🏠 Bosh menyu"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- SERVER (RENDER PORTI UCHUN) ---
# "No open ports detected" xatosini yo'qotadi
async def handle(request): return web.Response(text="Bot is Live and Active!")
async def start_services():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()

# --- ASOSIY MENYU ---
def main_menu():
    kb = [
        [types.KeyboardButton(text=BTN_VIEW)],
        [types.KeyboardButton(text=BTN_VOICE)],
        [types.KeyboardButton(text=BTN_HOME)]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- START VA BOSH MENYU ---
@dp.message(F.text == BTN_HOME)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer_sticker("CAACAgIAAxkBAAELyRxl6R8X7TzS9Z7Q1Z_N8X7TzS9Z7A")
    await message.answer("Salom! Bot yangi token bilan muvaffaqiyatli ishga tushdi! 🚀🤖", reply_markup=main_menu())

# --- SAQLANGANLARNI KO'RISH ---
@dp.message(F.text == BTN_VIEW)
async def view_notes_handler(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid].get('notes'):
        await message.answer("Sizning barcha eslatmalaringiz: 👇")
        for i, n in enumerate(user_data[uid]['notes']):
            diff = datetime.now() - n['time']
            time_text = f"⏳ Saqlanganiga: {diff.days} kun, {diff.seconds // 3600} soat bo'ldi."
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{i}"))
            await message.answer(f"📌 **Matn:** {n['text']}\n\n{time_text}", reply_markup=builder.as_markup())
    else:
        await message.answer("Hozircha hech narsa saqlanmagan. ✨")

# --- OVOZNI MATNGA O'GIRISH ---
@dp.message(F.text == BTN_VOICE)
async def voice_start(message: types.Message):
    await message.answer("Menga ovozli xabar yuboring, men uni matnga o'girib beraman! 🎤🚀")

@dp.message(F.voice)
async def voice_proc(message: types.Message):
    wait = await message.answer("Ovoz tahlil qilinmoqda... 🚀")
    file = await bot.get_file(message.voice.file_id)
    voice_path = f"v_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, voice_path)
    try:
        audio = AudioSegment.from_file(voice_path).export("temp.wav", format="wav")
        r = sr.Recognizer()
        with sr.AudioFile("temp.wav") as source:
            text = r.recognize_google(r.record(source), language="uz-UZ")
        await wait.edit_text(f"🎤 **Siz aytgan matn:**\n\n`{text}`", parse_mode="Markdown")
    except:
        await wait.edit_text("Ovozni tushunib bo'lmadi. ❌")
    finally:
        for f in [voice_path, "temp.wav"]:
            if os.path.exists(f): os.remove(f)

# --- MATNNI SAQLASH ---
@dp.message(F.text)
async def text_handler(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = {'notes': [], 'temp': message.text}
    user_data[uid]['temp'] = message.text
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Saqlash ✅", callback_data="save_ok"),
                types.InlineKeyboardButton(text="Yo'q ❌", callback_data="save_no"))
    await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "save_ok")
async def save_cb(callback: types.CallbackQuery):
    uid = callback.from_user.id
    text = user_data[uid].get('temp', "")
    user_data[uid]['notes'].append({'text': text, 'time': datetime.now()})
    await callback.message.edit_text(f"Muvaffaqiyatli saqlandi! ✅")

async def main():
    # Eski webhookni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
