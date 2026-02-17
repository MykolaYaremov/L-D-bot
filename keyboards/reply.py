from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Головне меню (постійне)
def get_main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📚 Список наявних курсів")],
        [KeyboardButton(text="🛠 Потрібна підтримка")],
        [KeyboardButton(text="ℹ️ Дізнатися деталі мого курсу")]
    ], resize_keyboard=True)

# Меню запиту контакту (тимчасове)
def get_request_contact_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Надіслати свій контакт", request_contact=True)],
        [KeyboardButton(text="⬅️ Назад в меню")] # Ця кнопка поверне старе меню
    ], resize_keyboard=True, one_time_keyboard=True)

