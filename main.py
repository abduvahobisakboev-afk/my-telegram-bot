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

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- SERVER (RENDER UCHUN) ---
async def handle(request): return web.Response(text="Bot is Live and Full Version!")
async def start_services():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# --- INSTAGRAM YUKLOVCHI FUNKSIYASI ---
def download_video(url):
    ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
    return 'video.mp4'

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text=BTN_VIEW)],
        [types.KeyboardButton(text=BTN_VOICE)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "Salom! Botga xush kelibsiz. ✨\n\nMen Instagram videolarini yuklayman, matnlarni vaqtini hisoblab saqlayman va ovozli xabarlaringizni matnga aylantirib beraman!",
        reply_markup=keyboard
    )

# --- 1-VAZIFA: SAQLANGANLARNI VAQT BILAN KO'RSATISH ---
@dp.message(F.text == BTN_VIEW)
async def view_notes_handler(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid].get('notes'):
        await message.answer("Sizning eslatmalaringiz: 👇")
        for i, n in enumerate(user_data[uid]['notes']):
            diff = datetime.now() - n['time']
            days, hours, minutes = diff.days, diff.seconds // 3600, (diff.seconds // 60) % 60
            
            time_text = f"⏳ Saqlaganingizga: {days} kun, {hours} soat va {minutes} minut bo'ldi."
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{i}"))
            
            await message.answer(f"📌 **Matn:** {n['text']}\n\n{time_text}", reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer("Hozircha hech narsa saqlanmagan. ✨")

# --- 2-VAZIFA: OVOZNI MATNGA AYLANTIRISH ---
@dp.message(F.text == BTN_VOICE)
async def voice_btn_handler(message: types.Message):
    await message.answer("Menga ovozli xabar yuboring, men uni matnga o'giraman! 🎤")

@dp.message(F.voice)
async def voice_processing(message: types.Message):
    wait = await message.answer("Ovoz tahlil qilinmoqda... ⏳")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    voice_path = "voice.ogg"
    await bot.download_file(file.file_path, voice_path)
    
    try:
        audio = AudioSegment.from_file(voice_path)
        audio.export("temp.wav", format="wav")
        recognizer = sr.Recognizer()
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
        
        user_data[message.from_user.id] = user_data.get(message.from_user.id, {'notes': [], 'temp': ""})
        user_data[message.from_user.id]['temp'] = text
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Saqlansin ✅", callback_data="confirm_save"))
        builder.row(types.InlineKeyboardButton(text="Yo'q ❌", callback_data="cancel_save"))
        await wait.edit_text(f"🎤 **Ovoz matni:**\n\n`{text}`\n\nSaqlaymi?", reply_markup=builder.as_markup(), parse_mode="Markdown")
    except:
        await wait.edit_text("Ovozni matnga aylantirib bo'lmadi. Aniqroq gapirib ko'ring. ❌")
    finally:
        if os.path.exists(voice_path): os.remove(voice_path)
        if os.path.exists("temp.wav"): os.remove("temp.wav")

# --- 3-VAZIFA: INSTAGRAM VA ODDY MATNNI SAQLASH ---
@dp.message(F.text)
async def main_handler(message: types.Message):
    if "instagram.com" in message.text:
        wait = await message.answer("Video yuklanmoqda... ⏳")
        try:
            path = await asyncio.to_thread(download_video, message.text)
            await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
            os.remove(path); await wait.delete()
        except: await wait.edit_text("Xatolik! Linkni tekshiring. ❌")
        return

    # Oddiy matnni saqlash
    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = {'notes': [], 'temp': ""}
    user_data[uid]['temp'] = message.text
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Ha ✅", callback_data="confirm_save"), 
                types.InlineKeyboardButton(text="Yo'q ❌", callback_data="cancel_save"))
    await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

# --- CALLBACK TUGMALAR ---
@dp.callback_query(F.data == "confirm_save")
async def save_confirm(callback: types.CallbackQuery):
    uid = callback.from_user.id
    note = user_data[uid].get('temp', "")
    user_data[uid]['notes'].append({'text': note, 'time': datetime.now()})
    await callback.message.edit_text(f"Muvaffaqiyatli saqlandi! ✅")

@dp.callback_query(F.data == "cancel_save")
async def save_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("Bekor qilindi. ❌")

@dp.callback_query(F.data.startswith("del_"))
async def delete_note(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    user_data[callback.from_user.id]['notes'].pop(index)
    await callback.message.delete()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
