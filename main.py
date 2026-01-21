import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SOZLAMALAR ---
TOKEN = "8302977160:AAHme7pxM3bpGLr0kCqe_hLT1bAZ1Va5FMk"
BTN_VIEW = "🗄 Saqlanganlarni ko'rish"
BTN_CLEAR = "🗑 Hammasini o'chirish"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- ERTALABKI ESLATMA FUNKSIYASI ---
async def daily_reminder():
    for uid, data in user_data.items():
        if data['notes']:
            report = "Ertalabki hisobot! ☀️\n\n"
            for n in data['notes']:
                diff = (datetime.now() - n['time']).days
                report += f"• {n['text']} (saqlanganiga {diff} kun bo'ldi) ⏳\n"
            try:
                await bot.send_message(uid, report)
            except:
                pass

# --- WEB SERVER VA SCHEDULER ---
async def handle(request): return web.Response(text="Bot Live!")
async def start_services():
    # Web serverni ishga tushirish
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    
    # Har kuni soat 08:00 da eslatishni sozlash
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(daily_reminder, 'cron', hour=8, minute=0)
    scheduler.start()

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
    await message.answer("Salom! Instagram link yuboring (darhol yuklayman) yoki matn yozing. ✨", reply_markup=keyboard)

@dp.message(F.text)
async def handle_msg(message: types.Message):
    if message.text in [BTN_VIEW, BTN_CLEAR]: return
    
    if "instagram.com" in message.text:
        wait_msg = await message.answer("Video yuklanmoqda... ⏳")
        try:
            path = await asyncio.to_thread(download_video, message.text)
            await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
            os.remove(path); await wait_msg.delete()
        except Exception: await wait_msg.edit_text("Xatolik! ❌")
    else:
        uid = message.from_user.id
        if uid not in user_data: user_data[uid] = {'notes': [], 'temp': ""}
        user_data[uid]['temp'] = message.text
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Ha, saqlansin ✅", callback_data="confirm_save"))
        builder.row(types.InlineKeyboardButton(text="Yo'q ❌", callback_data="cancel_save"))
        await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "confirm_save")
async def save_now(callback: types.CallbackQuery):
    uid = callback.from_user.id
    note = user_data[uid].get('temp', "")
    if note:
        user_data[uid]['notes'].append({'text': note, 'time': datetime.now()})
        await callback.message.edit_text(f"'{note}' saqlandi! ✅")
    user_data[uid]['temp'] = ""

@dp.callback_query(F.data == "cancel_save")
async def cancel_now(callback: types.CallbackQuery):
    await callback.message.edit_text("Bekor qilindi. ❌")

@dp.message(F.text == BTN_VIEW)
async def view(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid]['notes']:
        res = "Eslatmalaringiz:\n\n"
        for n in user_data[uid]['notes']:
            d = (datetime.now() - n['time']).days
            res += f"• {n['text']} ({d} kun bo'ldi) ⏳\n"
        await message.answer(res)
    else: await message.answer("Bo'sh! ✨")

@dp.message(F.text == BTN_CLEAR)
async def clear(message: types.Message):
    if message.from_user.id in user_data: user_data[message.from_user.id]['notes'] = []
    await message.answer("O'chirildi! 🗑")

async def main():
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
