# ... (tepadagi importlar va Web Server qismi o'sha-o'sh qoladi)

user_data = {} # Ma'lumotlarni saqlash uchun lug'at

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
    if message.text == BUTTON_TEXT: return
    
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = []
    
    user_data[user_id].append(message.text)
    await message.answer(f"'{message.text}' muvaffaqiyatli saqlandi! ✅")

# ... (pastki qismi o'sha-o'sh)
