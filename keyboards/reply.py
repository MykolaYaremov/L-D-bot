from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_role_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Студент"), KeyboardButton(text="Кандидат")],
        [KeyboardButton(text="PRO"), KeyboardButton(text="Admin")]
    ], resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="1. Список наявних курсів")],
        [KeyboardButton(text="2. Потрібна підтримка")],
        [KeyboardButton(text="3. Дізнатися деталі мого курсу")],
        [KeyboardButton(text="⬅️ Назад")] # ДОБАВИЛ КНОПКУ
    ], resize_keyboard=True)