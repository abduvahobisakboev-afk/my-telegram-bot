import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

# --- SOZLAMALAR ---
TOKEN = "8302977160:AAHme7pxM3bpGLr0kCqe_hLT1bAZ1Va5FMk"
BUTTON_TEXT = "🗄 Saqlanganlarni ko'rish"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {} # Note'larni saqlash uchun

# --- WEB SERVER (Render uxlab qolmasligi uchun) ---
async def handle(request): return web.Response(text="Bot ishlayapti!")
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

# --- COMMANDS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text=BUTTON_TEXT)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Salom! Menga Instagram video silkasini yoki matn yuborsangiz saqlab qo'yaman. 📥✨", reply_markup=keyboard)

# --- INSTAGRAM LINKI KELSA ---
@dp.message(F.text.contains("instagram.com"))
async def handle_insta(message: types.Message):
    wait_msg = await message.answer("Video yuklanmoqda... ⏳")
    try:
        path = await asyncio.to_thread(download_video, message.text)
        await message.answer_video(video=types.FSInputFile(path), caption="Tayyor! ✅")
        os.remove(path)
        await wait_msg.delete()
    except Exception:
        await wait_msg.edit_text("Xatolik: Videoni yuklab bo'lmadi. ❌")

# --- SAQLANGANLARNI KO'RISH ---
@dp.message(F.text == BUTTON_TEXT)
async def show_notes(message: types.Message):
    uid = message.from_user.id
    if uid in user_data and user_data[uid]:
        notes = "\n".join([f"• {n}" for n in user_data[uid]])
        await message.answer(f"Sizning eslatmalaringiz:\n\n{notes}")
    else:
        await message.answer("Hozircha hech narsa saqlanmagan. ✨")

# --- ODDIY MATN KELSA (NOTE SIFATIDA SAQLASH) ---
@dp.message(F.text)
async def save_note(message: types.Message):
    if message.text == BUTTON_TEXT: return
    uid = message.from_user.id
    if uid not in user_data: user_data[uid] = []
    user_data[uid].append(message.text)
    await message.answer(f"'{message.text}' xotiraga saqlandi! ✅")

async def main():
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())

