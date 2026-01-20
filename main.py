import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from instaloader import Instaloader, Post
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Sizning API Tokeningiz
TOKEN = "8302977160:AAHme7pxM3bpGLr0kCqe_hLT1bAZ1Va5FMk"

bot = Bot(token=TOKEN)
dp = Dispatcher()
L = Instaloader()
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

# Ma'lumotlarni saqlash uchun lug'at
user_notes = {}

# Tugma nomi (Hamma joyda bir xil bo'lishi uchun o'zgaruvchiga oldik)
BUTTON_TEXT = "🗄 Saqlashda foydalanish"

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text=BUTTON_TEXT))
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    # Emojilar bilan boyitilgan yangi salomlashish matni
    welcome_text = (
        f"Xush kelibsiz, {message.from_user.first_name}! 👋\n\n"
        "Men sizga qo'limdan kelgancha hamma narsani eslab qolishga harakat qilaman. 🧠 "
        "Qo'shimchasiga siz tashlagan narsani o'sha vaqtdan boshlab hisoblayman va sizga buni eslataman! ⏳\n\n"
        "Shuningdek, Instagramdan har qanday video va rasmlarni yuklashga harakat qilaman. 📥\n"
        "Boshlash uchun o'zingiz esla olmaydigan parol 🔐 yoki eslatma 📝 yuboring.\n"
        "Hammasi xuddi tepada aytilganidek! ✅"
    )
    await message.answer(welcome_text, reply_markup=main_menu())

@dp.message(F.text.contains("instagram.com"))
async def download_insta(message: types.Message):
    wait = await message.answer("Instagramdan qidirilmoqda... ⏳")
    try:
        parts = message.text.split("/")
        # Shortcodeni aniqlash (p, reels yoki reel)
        if "p" in parts:
            shortcode = parts[parts.index("p")+1]
        elif "reels" in parts:
            shortcode = parts[parts.index("reels")+1]
        else:
            shortcode = parts[parts.index("reel")+1]
            
        post = Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            await message.answer_video(video=post.video_url, caption="Yuklandi ✅")
        else:
            await message.answer_photo(photo=post.url, caption="Rasm yuklandi ✅")
        await wait.delete()
    except:
        await wait.edit_text("Xatolik: Link noto'g'ri yoki profil yopiq. ❌")

@dp.message(F.text == BUTTON_TEXT)
async def show_my_notes(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_notes or not user_notes[user_id]:
        await message.answer("Hozircha hech narsa saqlanmagan. ✨")
        return
    
    await message.answer("🗂 Sizning saqlangan ma'lumotlaringiz:")
    for note_id, data in user_notes[user_id].items():
        diff = datetime.now() - data['date']
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="❌ O'chirish", callback_data=f"del_{note_id}"))
        
        await message.answer(
            f"📌 **Ma'lumot:** {data['text']}\n"
            f"📅 **Sana:** {data['date'].strftime('%Y-%m-%d %H:%M')}\n"
            f"⏳ **O'tgan vaqt:** {diff.days} kun", 
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data.startswith("del_"))
async def delete_note(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    note_id = int(callback.data.split("_")[1])
    if user_id in user_notes and note_id in user_notes[user_id]:
        del user_notes[user_id][note_id]
        await callback.message.delete()
        await callback.answer("O'chirildi ✅")

@dp.message()
async def save_note(message: types.Message):
    # Tugma bosilganda matn sifatida saqlab qo'ymaslik uchun
    if message.text == BUTTON_TEXT: return
    
    user_id = message.from_user.id
    if user_id not in user_notes: user_notes[user_id] = {}
    
    note_id = int(datetime.now().timestamp())
    user_notes[user_id][note_id] = {
        "text": message.text, 
        "date": datetime.now()
    }
    
    await message.answer(
        "Muvaffaqiyatli saqlandi! ✅\nMen buni eslab qoldim va vaqtini sanashni boshladim. 🕒",
        reply_markup=main_menu()
    )

async def daily_reminder():
    for user_id, notes in user_notes.items():
        for note_id, data in notes.items():
            diff = datetime.now() - data['date']
            try:
                await bot.send_message(
                    user_id, 
                    f"Eslatma! 👋\n\n📌 **{data['text']}**\n⏳ Saqlanganiga **{diff.days} kun** bo'ldi. ✨",
                    parse_mode="Markdown"
                )
            except:
                pass

async def main():
    # Har kuni ertalab soat 08:00 da avtomatik eslatma
    scheduler.add_job(daily_reminder, "cron", hour=8, minute=0)
    scheduler.start()
    print("Bot muvaffaqiyatli ishga tushdi... ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi!")