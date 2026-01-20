import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from instaloader import Instaloader, Post
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- 1. RENDER UCHUN WEB SERVER (BU QISM SHART!) ---
def run_web_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active!")
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# Serverni alohida oqimda yoqish
threading.Thread(target=run_web_server, daemon=True).start()

# --- 2. BOT SOZLAMALARI ---
TOKEN = "8302977160:AAHme7pxM3bpGLr0kCqe_hLT1bAZ1Va5FMk"
bot = Bot(token=TOKEN)
dp = Dispatcher()
L = Instaloader()
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
user_notes = {}
BUTTON_TEXT = "🗄 Saqlashda foydalanish"

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text=BUTTON_TEXT))
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(f"Xush kelibsiz, {message.from_user.first_name}! 👋\nMen Instagram yuklovchi va eslatma botiman.", reply_markup=main_menu())

@dp.message(F.text.contains("instagram.com"))
async def download_insta(message: types.Message):
    wait = await message.answer("Yuklanmoqda... ⏳")
    try:
        parts = message.text.split("/")
        shortcode = parts[parts.index("p")+1] if "p" in parts else parts[parts.index("reels")+1] if "reels" in parts else parts[parts.index("reel")+1]
        post = Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            await message.answer_video(video=post.video_url, caption="Tayyor ✅")
        else:
            await message.answer_photo(photo=post.url, caption="Tayyor ✅")
        await wait.delete()
    except:
        await wait.edit_text("Xatolik! Linkni tekshiring. ❌")

@dp.message(F.text == BUTTON_TEXT)
async def show_notes(message: types.Message):
    await message.answer("Sizning saqlangan ma'lumotlaringiz bo'sh. ✨")

@dp.message()
async def save_any(message: types.Message):
    if message.text == BUTTON_TEXT: return
    await message.answer("Saqlandi! ✅")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi... ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
