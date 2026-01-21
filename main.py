import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- WEB SERVER (Render uchun) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# --- BOT SOZLAMALARI ---
TOKEN = "7880913847:AAFe7u0G0-rS-7A6u9642W-P3_L-9jE_eG8"
BUTTON_TEXT = "🗄 Saqlashda foydalanish"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {} # Ma'lumotlarni vaqtincha saqlash

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text=BUTTON_TEXT)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Xush kelibsiz! Ma'lumot yuboring va men uni saqlab qo'yaman.", reply_markup=keyboard)

@dp.message(F.text == BUTTON_TEXT)
async def show_notes(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]:
        notes = "\n".join([f"• {n}" for n in user_data[user_id]])
        await message.answer(f"Sizning saqlangan ma'lumotlaringiz:\n\n{notes}")
    else:
        await message.answer("Sizning saqlangan ma'lumotlaringiz hali bo'sh. ✨")

@dp.message()
async def save_any(message: types.Message):
    if not message.text or message.text == BUTTON_TEXT: return
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = []
    user_data[user_id].append(message.text)
    await message.answer(f"'{message.text}' muvaffaqiyatli saqlandi! ✅")

async def main():
    # Web server va Botni birga ishga tushirish
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
