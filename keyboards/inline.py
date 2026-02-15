from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_courses_list_kb(courses):
    # Сценарій 2
    buttons = [[InlineKeyboardButton(text=c["title"], callback_data=f"course_{c["postId"]}")]
               for c in courses]
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
        [InlineKeyboardButton(text="Високий рівень", callback_data="know_2")]
    ])

def get_support_kb():
    # Сценарії 8, 10
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ FAQ", callback_data=f"faq")],
        [InlineKeyboardButton(text="👨‍💼 Зв'язатися з менеджером", callback_data="contact_manager")]
    ])

def get_question_list_kb(questions, course_id = None):
    # Сценарій 8
    buttons = []
    for idx, item in enumerate(questions):
        question_text = item.get("question", "").strip()
        if course_id is not None:
            callback_data = f"faq_{course_id}_item_{idx}"
            back_data = f"course_{course_id}"
        else:
            callback_data = f"faq_item_{idx}"
            back_data = "back_to_support"
        buttons.append([
            InlineKeyboardButton(
                text=question_text,
                callback_data=callback_data
            )
        ])
    buttons.append([InlineKeyboardButton(
                text="⬅️ Повернутися назад",
                callback_data=back_data
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_list_kb(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Повернутися до списку", callback_data=prefix)],
    ])