import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- YANGI TOKENINGIZ JOYLANGAN ---
TOKEN = "8302977160:AAFdsxTWdSFjiG-ppp-xJaxGbqE-89EhUzY" 
BTN_VIEW = "🗄 Saqlanganlarni ko'rish"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- ERTALABKI HISOBOT (08:00) ---
async def daily_reminder():
    for uid, data in user_data.items():
        if data.get('notes'):
            report = "Ertalabki hisobot! ☀️\n\n"
            for i, n in enumerate(data['notes']):
                diff = datetime.now() - n['time']
                report += f"{i+1}. {n['text']} ({diff.days} kun bo'ldi) ⏳\n"
            try:
                await bot.send_message(uid, report)
            except: pass

# --- SERVER VA SCHEDULER (RENDERDA KOMPYUTERSIZ ISHLASHI UCHUN) ---
async def handle(request): return web.Response(text="Bot is Live and Stable!")

async def start_services():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    
    # O'zbekiston vaqti bilan hisobot rejalashtiruvchisi
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(daily_reminder, 'cron', hour=8, minute=0)
    scheduler.start()

# --- INSTAGRAM YUKLOVCHI ---
def download_video(url):
    ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
    return 'video.mp4'

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text=BTN_VIEW)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=False)
    await message.answer(
        "Salom! Matn yuboring yoki Instagram link tashlang. ✨\n\nMen sizga ma'lumotlarni vaqtini hisoblab saqlashga yordam beraman.", 
        reply_markup=keyboard
    )

# --- SAQLANGANLARNI KUN, SOAT, MINUT BILAN KO'RSATISH ---
@dp.message(F.text == BTN_VIEW)
async def view_notes_handler(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid].get('notes'):
        await message.answer("Sizning barcha saqlangan eslatmalaringiz: 👇")
        
        for i, n in enumerate(user_data[uid]['notes']):
            # Vaqt farqini hisoblash
            diff = datetime.now() - n['time']
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds // 60) % 60
            
            # 0 bo'lsa ham ko'rsatiladigan format
            time_text = (f"⏳ Siz bu xabarni saqlaganingizga:\n"
                         f"➡️ {days} kun, {hours} soat va {minutes} minut bo'ldi.")
            
            builder = InlineKeyboardBuilder()
