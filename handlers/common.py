import logging
from contextlib import suppress

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

# --- КОНСТАНТИ ТЕКСТУ (Щоб текст був однаковим всюди) ---
TEXT_SUPPORT_MENU = (
    "🛠 <b>Служба підтримки</b>\n\n"
    "Якщо у вас виникли технічні проблеми або питання щодо організації, "
    "ви можете зв'язатися з менеджером напряму або переглянути часті запитання."
)

TEXT_CONTACT_REQUEST = (
    "📞 <b>Зв'язок з менеджером</b>\n\n"
    "Натисніть кнопку <b>«📱 Надіслати свій контакт»</b> знизу екрану."
)


# --- УТИЛІТИ ---

async def clear_previous_interface(state: FSMContext, message: types.Message):
    """Видаляє старі інлайн-кнопки, щоб не засмічувати чат."""
    data = await state.get_data()
    last_msg_id = data.get("last_interface_message_id")

    if last_msg_id:
        with suppress(TelegramBadRequest):
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                reply_markup=None
            )


async def send_interface_message(state: FSMContext, message: types.Message, text: str, reply_markup=None):
    """Універсальна функція: видаляє старе меню і надсилає нове."""
    await clear_previous_interface(state, message)
    msg = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_interface_message_id=msg.message_id)


# --- СТАРТ ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await send_interface_message(
        state, message,
        f"Привіт, {message.from_user.first_name}! Я L&D бот Sigma Software.",
        get_main_menu_kb()
    )


# --- 1. ПІДТРИМКА (Вхід в меню) ---

# ✅ ВИПРАВЛЕНО: Використовуємо .contains(), щоб ловити "🛠 Потрібна підтримка"
@router.message(F.text.lower().contains("підтримка") | F.text.lower().contains("допомога"))
async def support_handler(message: types.Message, state: FSMContext):
    # Якщо юзер натиснув це під час введення контакту — повертаємо меню
    if await state.get_state() == LNDStates.waiting_for_support_contact:
        await message.answer("🔄 Меню оновлено", reply_markup=get_main_menu_kb())

    await state.update_data(current_course_id=None, support_course_title=None)
    await state.set_state(LNDStates.main_menu)

    # Використовуємо спільну змінну з текстом
    await send_interface_message(state, message, TEXT_SUPPORT_MENU, get_support_kb())


# --- 2. ЗВ'ЯЗОК З МЕНЕДЖЕРОМ ---

@router.callback_query(F.data == "contact_manager")
async def ask_contact_for_support(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.waiting_for_support_contact)

    # Прибираємо кнопки з попереднього повідомлення
    await callback.message.edit_text(TEXT_CONTACT_REQUEST, reply_markup=None, parse_mode="HTML")

    # Надсилаємо нове повідомлення з кнопкою внизу
    msg = await callback.message.answer("Очікую ваш контакт 👇", reply_markup=get_request_contact_kb())
    await state.update_data(last_interface_message_id=msg.message_id)
    await callback.answer()


@router.message(LNDStates.waiting_for_support_contact, F.text.contains("Назад"))
async def back_from_contact_request(message: types.Message, state: FSMContext):
    await state.set_state(LNDStates.main_menu)
    await send_interface_message(
        state, message,
        "❌ Дія скасована. Повертаємось до головного меню.",
        get_main_menu_kb()
    )


# ✅ ОБРОБКА ПОМИЛКИ: Якщо юзер пише текст замість натискання кнопки контакту
@router.message(LNDStates.waiting_for_support_contact, ~F.contact)
async def incorrect_contact_input(message: types.Message):
    await message.answer(
        "⚠️ <b>Я очікую номер телефону.</b>\n\n"
        "Будь ласка, натисніть кнопку <b>«📱 Надіслати свій контакт»</b> внизу екрану "
        "або поверніться назад.",
        parse_mode="HTML"
    )


@router.message(LNDStates.waiting_for_support_contact, F.contact)
async def receive_support_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.contact.phone_number)
    await state.set_state(LNDStates.waiting_for_support_reason)

    # ✅ ВИПРАВЛЕНО: Додано parse_mode="HTML", щоб <b> працював
    await message.answer(
        "✅ Контакт отримано!\n\n"
        "✍️ Тепер напишіть <b>причину вашого звернення</b> одним повідомленням:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )


# --- 3. ВІДПРАВКА ЗАЯВКИ ---

@router.message(LNDStates.waiting_for_support_reason, F.text)
async def receive_support_reason(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # Формуємо звіт для адміна
    report = [
        "🆘 <b>Новий запит підтримки!</b>",
        f"👤 <b>Користувач:</b> {message.from_user.full_name} (@{message.from_user.username or 'не вказано'})",
        f"📱 <b>Телефон:</b> {data.get('phone_number')}",
        f"📝 <b>Причина:</b> {message.text}"
    ]

    if course := data.get("support_course_title"):
        link = data.get("support_course_link", "#")
        report.append(f"\n📚 <b>Цікавиться курсом:</b> <a href='{link}'>{course}</a>")

    full_text = "\n".join(report)

    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                full_text,
                parse_mode="HTML",
                link_preview_options=types.LinkPreviewOptions(is_disabled=True)
            )
        except Exception as e:
            logging.error(f"Не вдалося надіслати адміну: {e}")

    await state.set_state(LNDStates.main_menu)
    await state.update_data(phone_number=None, support_course_title=None)

    await send_interface_message(
        state, message,
        "✅ <b>Запит прийнято!</b>\n\nМенеджер зв'яжеться з вами найближчим часом.",
        get_main_menu_kb()
    )


# --- НАВІГАЦІЯ ---

@router.callback_query(F.data == "back_to_support")
async def back_to_support_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.main_menu)
    # ✅ ВИПРАВЛЕНО: Використовуємо ту саму змінну TEXT_SUPPORT_MENU
    await callback.message.edit_text(
        TEXT_SUPPORT_MENU,
        reply_markup=get_support_kb(),
        parse_mode="HTML"
    )


@router.message(F.text.contains("Дізнатися деталі мого курсу"))
async def my_course_handler(message: types.Message, state: FSMContext):
    await send_interface_message(state, message, "ℹ️ Ця функція ще в розробці.")


# --- ЗАГЛУШКА (FALLBACK) ---

@router.message()
async def fallback(message: types.Message):
    # Реагуємо тільки на текст, ігноруємо системні повідомлення
    if message.content_type == types.ContentType.TEXT:
        await message.answer("🤔 Я вас не зрозумів. Будь ласка, скористайтесь кнопками меню.")