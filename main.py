import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- SOZLAMALAR ---
TOKEN = "7880913847:AAFe7u0G0-rS-7A6u9642W-P3_L-9jE_eG8"
BTN_VIEW = "🗄 Saqlanganlarni ko'rish"
BTN_CLEAR = "🗑 Hammasini o'chirish"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- WEB SERVER (Cron-job uchun) ---
async def handle(request): return web.Response(text="Bot Live!")
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# --- INSTAGRAM YUKLOVCHI ---
def download_video(url):
    ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return 'video.mp4'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text=BTN_VIEW)], [types.KeyboardButton(text=BTN_CLEAR)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Salom! Matn yuborsangiz, tasdiqlaganingizdan keyin saqlayman. ✨", reply_markup=keyboard)

# --- SAQLASHNI TASDIQLASH (Inline Button) ---
@dp.message(F.text)
async def ask_to_save(message: types.Message):
    if message.text in [BTN_VIEW, BTN_CLEAR]: return
    
    if "instagram.com" in message.text:
        wait_msg = await message.answer("Video yuklanmoqda... ⏳")
        try:
            path = await asyncio.to_thread(download_video, message.text)
            await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
            os.remove(path)
            await wait_msg.delete()
        except Exception:
            await wait_msg.edit_text("Xatolik: Yuklab bo'lmadi. ❌")
    else:
        # Saqlashni so'rash
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Ha, saqlansin ✅", callback_data=f"save_{message.text[:20]}"))
        builder.row(types.InlineKeyboardButton(text="Yo'q, kerakmas ❌", callback_data="cancel_save"))
        
        # Vaqtincha xotirada ushlab turish
        uid = message.from_user.id
        if uid not in user_data: user_data[uid] = {'notes': [], 'temp_note': ""}
        user_data[uid]['temp_note'] = message.text
        
        await message.answer(f"'{message.text}' - Ushbu matnni saqlaymi?", reply_markup=builder.as_markup())

# --- TUGMA BOSILGANDA ---
@dp.callback_query(F.data.startswith("save_"))
async def confirm_save(callback: types.CallbackQuery):
    uid = callback.from_user.id
    note = user_data[uid].get('temp_note', "")
    if note:
        user_data[uid]['notes'].append({'text': note, 'time': datetime.now()})
        await callback.message.edit_text(f"'{note}' xotiraga saqlandi! ✅")
    user_data[uid]['temp_note'] = ""

@dp.callback_query(F.data == "cancel_save")
async def cancel_save(callback: types.CallbackQuery):
    await callback.message.edit_text("Saqlash bekor qilindi. ✨")

# --- KO'RISH ---
@dp.message(F.text == BTN_VIEW)
async def show_notes(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid]['notes']:
        res = "Sizning eslatmalaringiz:\n\n"
        for n in user_data[uid]['notes']:
            diff = datetime.now() - n['time']
            res += f"• {n['text']} ({diff.days} kun bo'ldi) ⏳\n"
        await message.answer(res)
    else:
        await message.answer("Ma'lumot topilmadi. ✨")

# --- O'CHIRISH ---
@dp.message(F.text == BTN_CLEAR)
async def clear_notes(message: types.Message):
    uid = message.from_user.id
    if uid in user_data: user_data[uid]['notes'] = []
    await message.answer("Barcha eslatmalar o'chirildi! 🗑")

async def main():
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
