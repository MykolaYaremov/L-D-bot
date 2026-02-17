from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# --- 1. СПИСОК КУРСІВ ---
def get_courses_list_kb(courses):
    buttons = []
    for c in courses:
        buttons.append([InlineKeyboardButton(text=c["title"], callback_data=f"course_{c['postId']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- 2. ДЕТАЛІ КУРСУ ---
def get_course_details_kb(course_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        # Ціна і Оплата (просто повідомлення, не змінюють стан)
        [InlineKeyboardButton(text="💰 Вартість", callback_data=f"price_{course_id}"),
         InlineKeyboardButton(text="💳 Як оплатити", callback_data=f"pay_{course_id}")],
        # Активні дії (FAQ, Тест, Менеджер - приховують меню курсу)
        [InlineKeyboardButton(text="❓ FAQ", callback_data=f"faq_{course_id}"),
         InlineKeyboardButton(text="✅ Чи підійде мені?", callback_data=f"check_{course_id}")],
        [InlineKeyboardButton(text="👨‍💼 Зв'язатися з менеджером", callback_data=f"contact_manager_course_{course_id}")],
        # Назад до списку
        [InlineKeyboardButton(text="⬅️ До списку курсів", callback_data="back_to_list")]
    ])


# --- 3. УНІВЕРСАЛЬНА КНОПКА "НАЗАД ДО КУРСУ" ---
def get_back_to_course_kb(course_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад до курсу", callback_data=f"back_to_course_{course_id}")]
    ])


# --- 4. ГОЛОВНЕ МЕНЮ ПІДТРИМКИ ---
def get_support_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ FAQ (Загальне)", callback_data="faq_general")],
        [InlineKeyboardButton(text="👨‍💼 Зв'язатися з менеджером", callback_data="contact_manager")]
    ])


# --- 5. МЕНЮ КОНТАКТУ З МЕНЕДЖЕРОМ (Кнопка Назад) ---
def get_contact_inline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_support_menu")]
    ])


# --- 6. ТЕСТ (QUIZ) ---
def get_knowledge_kb(course_id=None):
    buttons = [
        [InlineKeyboardButton(text="Повний нуль", callback_data="know_0")],
        [InlineKeyboardButton(text="Маю базу", callback_data="know_1")],
        [InlineKeyboardButton(text="Високий рівень", callback_data="know_2")]
    ]
    # Додаємо кнопку повернення, якщо передано ID курсу
    if course_id:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад до курсу", callback_data=f"back_to_course_{course_id}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- 7. СПИСОК ПИТАНЬ FAQ ---
def get_question_list_kb(faq_data, course_id=None):
    buttons = []
    # Генеруємо кнопки для кожного питання
    for i, item in enumerate(faq_data):
        # callback: faq_{id_курсу}_item_{номер_питання}
        buttons.append([InlineKeyboardButton(text=item['question'], callback_data=f"faq_{course_id}_item_{i}")])

    # ЛОГІКА КНОПКИ НАЗАД
    if course_id:
        # Якщо ми в курсі -> Назад до курсу
        buttons.append([InlineKeyboardButton(text="⬅️ Назад до курсу", callback_data=f"back_to_course_{course_id}")])
    else:
        # Якщо ми в загальному FAQ -> Назад до меню підтримки
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_support")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- 8. КНОПКА ПОВЕРНЕННЯ ДО СПИСКУ ПИТАНЬ ---
def get_back_to_list_kb(back_callback_data):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад до питань", callback_data=back_callback_data)]
    ])