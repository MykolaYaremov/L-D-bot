from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from states import LNDStates
from keyboards.reply import get_main_menu_kb, get_request_contact_kb
from keyboards.inline import get_support_kb
from config import ADMIN_ID

router = Router()

# --- ДОПОМІЖНА ФУНКЦІЯ: ВИДАЛЕННЯ СТАРИХ КНОПОК ---
async def clear_previous_interface(state: FSMContext, message: types.Message):
    data = await state.get_data()
    last_msg_id = data.get("last_interface_message_id")
    if last_msg_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                reply_markup=None
            )
        except Exception:
            pass

async def send_interface_message(state: FSMContext, message: types.Message, text: str, reply_markup=None):
    await clear_previous_interface(state, message)
    msg = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_interface_message_id=msg.message_id)


# --- СТАРТ ---
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привіт, {message.from_user.first_name}! Я L&D бот Sigma Software.",
        reply_markup=get_main_menu_kb()
    )


# --- 1. ПІДТРИМКА (Головне меню) ---
@router.message(~StateFilter(LNDStates.waiting_for_support_reason),
                F.text.lower().contains("підтримка") |
                F.text.lower().contains("допомога"))
async def support_handler(message: types.Message, state: FSMContext):
    # --- ФІКС КЛАВІАТУРИ ---
    current_state = await state.get_state()
    if current_state == LNDStates.waiting_for_support_contact:
        await message.answer("🔄 Меню оновлено", reply_markup=get_main_menu_kb()) #
    # -----------------------

    await state.update_data(
        current_course_id=None,
        support_course_title=None,
        support_course_link=None
    )
    await state.set_state(LNDStates.main_menu)
    text = (
        "🛠 <b>Служба підтримки</b>\n\n"
        "Якщо у вас виникли технічні проблеми або питання щодо організації, "
        "ви можете зв'язатися з менеджером напряму або переглянути часті запитання."
    )
    await send_interface_message(state, message, text, get_support_kb())


# --- 2. ЛОГІКА ЗВ'ЯЗКУ З МЕНЕДЖЕРОМ (Перехід на нижню клавіатуру) ---
@router.callback_query(F.data == "contact_manager")
async def ask_contact_for_support(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.waiting_for_support_contact)

    # 1. Редагуємо повідомлення: прибираємо кнопки "FAQ/Менеджер", залишаємо текст інструкції
    await callback.message.edit_text(
        "📞 <b>Зв'язок з менеджером</b>\n"
        "Для зв'язку з вами, нам потрібен ваш номер телефону.\n\n"
        "👇 Натисніть кнопку <b>«📱 Надіслати свій контакт»</b> знизу екрану.\n"
        "Або натисніть «Назад в меню» для скасування.",
        reply_markup=None,
        parse_mode="HTML"
    )

    # 2. Надсилаємо повідомлення, яке відкриває Reply клавіатуру (знизу)
    msg = await callback.message.answer("Очікую ваш контакт:", reply_markup=get_request_contact_kb())

    # Запам'ятовуємо ID цього повідомлення
    await state.update_data(last_interface_message_id=msg.message_id)
    await callback.answer()


# --- 3. ОБРОБКА КНОПКИ "НАЗАД В МЕНЮ" (З нижньої клавіатури) ---
@router.message(LNDStates.waiting_for_support_contact, F.text == "⬅️ Назад в меню")
async def back_from_contact_request(message: types.Message, state: FSMContext):
    await state.set_state(LNDStates.main_menu)

    # Повертаємо головне меню
    await message.answer(
        "❌ Дія скасована. Повертаємось до головного меню.",
        reply_markup=get_main_menu_kb()
    )


# --- 4. ОБРОБКА ОТРИМАНОГО КОНТАКТУ ---
@router.message(LNDStates.waiting_for_support_contact, F.contact)
async def receive_support_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone_number=phone)

    # Переходимо в стан очікування причини
    await state.set_state(LNDStates.waiting_for_support_reason)

    # Прибираємо кнопку "Надіслати контакт" і просимо текст
    await message.answer(
        "✅ Контакт отримано!\n\n"
        "Тепер коротко опишіть причину вашого звернення:",
        reply_markup=ReplyKeyboardRemove()  # Прибираємо нижню клавіатуру
    )


# --- 5. ОБРОБКА ПРИЧИНИ ЗВЕРНЕННЯ (Текст) ---
@router.message(LNDStates.waiting_for_support_reason, F.text)
async def receive_support_reason(message: types.Message, state: FSMContext, bot: Bot):
    reason = message.text
    data = await state.get_data()
    phone = data.get("phone_number")
    course_id = data.get("current_course_id")
    course_title = data.get("support_course_title")
    course_link = data.get("support_course_link")


    # Отримуємо дані користувача
    user = message.from_user
    # Перевіряємо, чи є юзернейм (якщо ні, пишемо "не вказано")
    username_text = f"@{user.username}" if user.username else "не вказано"

    # Формуємо повідомлення для адміна
    admin_text = (
        f"🆘 <b>Новий запит підтримки!</b>\n\n"
        f"👤 <b>Користувач:</b> {user.full_name} ({username_text})\n"
        f"📱 Телефон: {phone}\n"
        f"📝 Причина: {reason}"
    )

    if course_id:
        admin_text += f"\n\n📚 <b>Цікавиться курсом:</b> <a href='{course_link}'>{course_title}</a>"

    # Відправка адміну
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")

    await state.clear()
    # Повертаємо користувача в головне меню
    await state.set_state(LNDStates.main_menu)
    await message.answer(
        "⏳ Запит прийнято! Менеджер зв'яжеться з вами найближчим часом.",
        reply_markup=get_main_menu_kb()
    )


# --- ДІЗНАТИСЯ ДЕТАЛІ КУРСУ ---
@router.message(~StateFilter(LNDStates.waiting_for_support_reason),
                F.text.contains("Дізнатися деталі мого курсу"))
async def my_course_handler(message: types.Message, state: FSMContext):
    await send_interface_message(state, message, "ℹ️ Активних курсів не знайдено.")


# --- ОБРОБКА КНОПКИ "НАЗАД" (Із загального FAQ до меню Підтримки) ---
@router.callback_query(F.data == "back_to_support")
async def back_to_support_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.main_menu)
    text = (
        "🛠 <b>Служба підтримки</b>\n\n"
        "Оберіть, що вас цікавить:"
    )
    # Редагуємо повідомлення: замість списку питань показуємо кнопки підтримки
    await callback.message.edit_text(text, reply_markup=get_support_kb(), parse_mode="HTML")



# --- ЗАГЛУШКА ---
@router.message()
async def fallback(message: types.Message):
    pass
