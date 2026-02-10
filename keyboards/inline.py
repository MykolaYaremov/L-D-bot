from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_courses_list_kb(courses):
    # Сценарій 2
    buttons = [[InlineKeyboardButton(text=c["name"], callback_data=f"course_{cid}")]
               for cid, c in courses.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_details_kb(course_id):
    # Сценарії 3, 4, 5, 8, 10
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Вартість", callback_data=f"price_{course_id}"),
         InlineKeyboardButton(text="💳 Як оплатити", callback_data=f"pay_{course_id}")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data=f"faq_{course_id}"),
         InlineKeyboardButton(text="✅ Чи підійде мені?", callback_data=f"check_{course_id}")],
        [InlineKeyboardButton(text="👨‍💼 Зв'язатися з менеджером", callback_data="contact_manager")]
    ])

def get_knowledge_kb():
    # Сценарій 7 (Питання 1)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Повний нуль", callback_data="know_0")],
        [InlineKeyboardButton(text="Маю базу", callback_data="know_1")],
        [InlineKeyboardButton(text="Працюю в IT", callback_data="know_2")]
    ])

def get_experience_kb():
    # Сценарій 7 (Питання 2)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ніколи не писав SQL", callback_data="exp_0")],
        [InlineKeyboardButton(text="Трохи пробував", callback_data="exp_1")],
        [InlineKeyboardButton(text="Пишу складні запити", callback_data="exp_2")]
    ])