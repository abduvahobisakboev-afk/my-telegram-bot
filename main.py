import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment

# --- SOZLAMALAR ---
TOKEN = "8302977160:AAFdsxTWdSFjiG-ppp-xJaxGbqE-89EhUzY" 
BTN_VIEW = "🗄 Saqlanganlarni ko'rish"
BTN_VOICE = "🎤 Ovozni matnga aylantirish"
BTN_HOME = "🏠 Bosh menyu"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- SERVER ---
async def handle(request): return web.Response(text="Bot is running stable!")
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
    # Stiker yuborish
    await message.answer_sticker("CAACAgIAAxkBAAELyRxl6R8X7TzS9Z7Q1Z_N8X7TzS9Z7A")
    # Siz aytgan matn
    await message.answer("Salom! Bot tayyor. Hamma xizmatlarimiz tayyor! ✨🤖", reply_markup=main_menu())

# --- SAQLANGANLARNI KO'RISH (ANIQ VAQT BILAN) ---
@dp.message(F.text == BTN_VIEW)
async def view_notes_handler(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid].get('notes'):
        await message.answer("Sizning barcha eslatmalaringiz: 👇")
        for i, n in enumerate(user_data[uid]['notes']):
            diff = datetime.now() - n['time']
            time_text = f"⏳ Siz bu xabarni saqlaganingizga:\n➡️ {diff.days} kun, {diff.seconds // 3600} soat va {(diff.seconds // 60) % 60} minut bo'ldi."
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🗑 Hammasini o'chirish", callback_data=f"delall_{i}"))
            
            await message.answer(f"📌 **Xabar:** {n['text']}\n\n{time_text}", reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer("Hozircha hech narsa saqlanmagan. ✨")

# --- OVOZLI XABARNI MATNGA AYLANTIRISH (TEZKOR) ---
@dp.message(F.text == BTN_VOICE)
async def voice_start(message: types.Message):
    await message.answer("Menga ovozli xabar yuboring, men uni darhol matnga o'girib beraman! 🎤🚀")

@dp.message(F.voice)
async def voice_proc(message: types.Message):
    wait = await message.answer("Ovoz tahlil qilinmoqda (tezkor)... 🚀")
    file = await bot.get_file(message.voice.file_id)
    voice_path = f"v_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, voice_path)
    
    try:
        audio = AudioSegment.from_file(voice_path)
        audio.export("temp.wav", format="wav")
        recognizer = sr.Recognizer()
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
        await wait.edit_text(f"🎤 **Siz aytgan matn:**\n\n`{text}`", parse_mode="Markdown")
    except:
        await wait.edit_text("Kechirasiz, ovozni tushunib bo'lmadi. ❌")
    finally:
        if os.path.exists(voice_path): os.remove(voice_path)
        if os.path.exists("temp.wav"): os.remove("temp.wav")

# --- MATNNI SAQLASH (DUBLIKATSIZ) ---
@dp.message(F.text)
async def text_handler(message: types.Message):
    if "instagram.com" in message.text:
        return # Instagram yuklash kodi

    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = {'notes': [], 'temp': ""}
    user_data[uid]['temp'] = message.text
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Saqlansin ✅", callback_data="save_ok"),
                types.InlineKeyboardButton(text="Yo'q ❌", callback_data="save_no"))
    await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

# --- CALLBACK TUGMALAR ---
@dp.callback_query(F.data == "save_ok")
async def save_cb(callback: types.CallbackQuery):
    uid = callback.from_user.id
    text = user_data[uid].get('temp', "")
    if text and not any(n['text'] == text for n in user_data[uid]['notes']):
        user_data[uid]['notes'].append({'text': text, 'time': datetime.now()})
        await callback.message.edit_text(f"'{text}' muvaffaqiyatli saqlandi! ✅")
    else:
        await callback.message.edit_text("Bu xabar allaqachon ro'yxatda bor! ⚠️")

@dp.callback_query(F.data.startswith("delall_"))
async def delete_all_cb(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    uid = callback.from_user.id
    if uid in user_data and len(user_data[uid]['notes']) > idx:
        target_text = user_data[uid]['notes'][idx]['text']
        user_data[uid]['notes'] = [n for n in user_data[uid]['notes'] if n['text'] != target_text]
        await callback.message.delete()
        await callback.answer("O'chirildi! ✅")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
