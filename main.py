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
# Eng oxirgi yangilangan tokeningiz
TOKEN = "8302977160:AAEMqZB0VHWTvNuCJQBCyqdzWZju-645Jd4"
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

# --- SERVER VA SCHEDULER (KOMPYUTERSIZ ISHLASH UCHUN) ---
async def handle(request): return web.Response(text="Bot is Live and Stable!")

async def start_services():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    
    # O'zbekiston vaqti bilan scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(daily_reminder, 'cron', hour=8, minute=0)
    scheduler.start()

# --- INSTAGRAM YUKLOVCHI ---
def download_video(url):
    ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
    return 'video.mp4'

# --- ASOSIY BUYRUQLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text=BTN_VIEW)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "Salom! Matn yuboring yoki Instagram link tashlang. ✨\n\nBu bot @save_bot_pro uchun maxsus sozlangan.",
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
            
            # Matnni shakllantirish
            time_text = f"⏳ Siz bu xabarni saqlaganingizga:\n"
            if days > 0:
                time_text += f"➡️ {days} kun\n"
            time_text += f"➡️ {hours} soat va {minutes} minut bo'ldi."
            
            # Alohida o'chirish tugmasi
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{i}"))
            
            await message.answer(
                f"📌 **Xabar:** {n['text']}\n\n{time_text}",
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
    else:
        await message.answer("Hozircha hech qanday ma'lumot saqlanmagan. ✨")

# --- XABARLARNI QABUL QILISH VA TASDIQLASH ---
@dp.message(F.text)
async def handle_msg(message: types.Message):
    if "instagram.com" in message.text:
        wait = await message.answer("Video yuklanmoqda... ⏳")
        try:
            path = await asyncio.to_thread(download_video, message.text)
            await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
            os.remove(path); await wait.delete()
        except:
            await wait.edit_text("Xatolik! Linkni tekshiring. ❌")
        return

    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = {'notes': [], 'temp': ""}
    user_data[uid]['temp'] = message.text
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Ha, saqlansin ✅", callback_data="confirm_save"))
    builder.row(types.InlineKeyboardButton(text="Yo'q ❌", callback_data="cancel_save"))
    await message.answer(f"'{message.text}' - Saqlaymi?", reply_markup=builder.as_markup())

# --- TUGMA CALLBACKLARI ---
@dp.callback_query(F.data == "confirm_save")
async def save_ok(callback: types.CallbackQuery):
    uid = callback.from_user.id
    note = user_data[uid].get('temp', "")
    if note:
        user_data[uid]['notes'].append({'text': note, 'time': datetime.now()})
        await callback.message.edit_text(f"'{note}' muvaffaqiyatli saqlandi! ✅")
    user_data[uid]['temp'] = ""

@dp.callback_query(F.data == "cancel_save")
async def save_no(callback: types.CallbackQuery):
    await callback.message.edit_text("Amaliyot bekor qilindi. ❌")

@dp.callback_query(F.data.startswith("del_"))
async def delete_callback(callback: types.CallbackQuery):
    try:
        index = int(callback.data.split("_")[1])
        uid = callback.from_user.id
        if uid in user_data and len(user_data[uid]['notes']) > index:
            user_data[uid]['notes'].pop(index)
            await callback.message.delete()
            await callback.answer("O'chirildi ✅")
    except:
        await callback.answer("Xatolik! ❌")

# --- ISHGA TUSHIRISH ---
async def main():
    # Webhookni tozalash (Conflict oldini olish uchun muhim!)
    await bot.delete_webhook(drop_pending_updates=True)
    # Server va botni birga ishga tushirish
    await asyncio.gather(start_services(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
