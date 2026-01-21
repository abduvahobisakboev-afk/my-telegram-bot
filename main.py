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

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- ERTALABKI ESLATMA ---
async def daily_reminder():
    for uid, data in user_data.items():
        if data.get('notes'):
            report = "Ertalabki hisobot! ☀️\n\n"
            for i, n in enumerate(data['notes']):
                diff = (datetime.now() - n['time']).days
                report += f"{i+1}. {n['text']} ({diff} kun bo'ldi) ⏳\n"
            try:
                await bot.send_message(uid, report)
            except: pass

# --- WEB SERVER VA SCHEDULER ---
async def handle(request): return web.Response(text="Bot Live!")
async def start_services():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
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
    kb = [[types.KeyboardButton(text=BTN_VIEW)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Salom! Matn yuboring yoki Instagram link tashlang. ✨", reply_markup=keyboard)

# --- MATN VA LINKLAR ---
@dp.message(F.text)
async def handle_msg(message: types.Message):
    if message.text == BTN_VIEW: return
    
    if "instagram.com" in message.text:
        wait_msg = await message.answer("Video yuklanmoqda... ⏳")
        try:
            path = await asyncio.to_thread(download_video, message.text)
            await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
            os.remove(path); await wait_msg.delete()
        except: await wait_msg.edit_text("Xatolik! ❌")
    else:
        uid = message.from_user.id
        if uid not in user_data: user_data[uid] = {'notes': [], 'temp': ""}
        user_data[uid]['temp'] = message.text
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Ha, saqlansin ✅", callback_data="confirm_save"))
        builder.row(types.InlineKeyboardButton(text="Yo'q ❌", callback_data="cancel_save"))
        await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

# --- CALLBACKLAR (SAQLASH VA BITTALAB O'CHIRISH) ---
@dp.callback_query(F.data == "confirm_save")
async def save_now(callback: types.CallbackQuery):
    uid = callback.from_user.id
    note = user_data[uid].get('temp', "")
    if note:
        user_data[uid]['notes'].append({'text': note, 'time': datetime.now()})
        await callback.message.edit_text(f"'{note}' saqlandi! ✅")
    user_data[uid]['temp'] = ""

@dp.callback_query(F.data.startswith("del_"))
async def delete_item(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    uid = callback.from_user.id
    if uid in user_data and len(user_data[uid]['notes']) > index:
        removed = user_data[uid]['notes'].pop(index)
        await callback.answer(f"'{removed['text']}' o'chirildi")
        # Ro'yxatni yangilab ko'rsatish
        await show_notes_list(callback.message, uid)

@dp.callback_query(F.data == "cancel_save")
async def cancel_now(callback: types.CallbackQuery):
    await callback.message.edit_text("Bekor qilindi. ❌")

# --- KO'RISH FUNKSIYASI ---
async def show_notes_list(message, uid):
    if uid in user_data and user_data[uid]['notes']:
        await message.answer("Sizning eslatmalaringiz:")
        for i, n in enumerate(user_data[uid]['notes']):
            diff = (datetime.now() - n['time']).days
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{i}"))
            await message.answer(f"• {n['text']} ({diff} kun bo'ldi)", reply_markup=builder.as_markup())
    else:
        await message.answer("Hozircha eslatmalar yo'q. ✨")

@dp.message(F.text == BTN_VIEW)
async def view_notes(message: types.Message):
    await show_notes_list(message, message.from_user.id)

async def main():
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
