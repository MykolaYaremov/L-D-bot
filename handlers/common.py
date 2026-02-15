from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove  # Треба додати імпорт

from states import LNDStates
from keyboards.reply import get_contact_kb, get_main_menu_kb
from keyboards.inline import get_support_kb
from config import ADMIN_ID

router = Router()


# --- Сценарій 1: Старт (Спрощений) ---
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    # Зберігаємо базову інфу про юзера, яку дає Телеграм
    await state.update_data(
        first_name=message.from_user.first_name,
        user_id=message.from_user.id,
        username=message.from_user.username
    )

    await state.set_state(LNDStates.main_menu)
    await message.answer(
        f"Привіт, {message.from_user.first_name}! Я L&D бот Sigma Software.\nЧим можу допомогти?",
        reply_markup=get_main_menu_kb()
    )


# --- Кнопка: Підтримка ---
@router.message(F.text.lower().contains("підтримка") |
                F.text.lower().contains("допомога"))
async def support_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.main_menu)  # Лишаємось в меню, поки не оберуть дію
    text = (
        "🛠 **Служба підтримки**\n\n"
        "Якщо у вас виникли технічні проблеми або питання щодо організації, "
        "ви можете зв'язатися з менеджером напряму або переглянути часті запитання."
    )

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_support_kb(), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_support_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "back_to_support")
async def back_to_support(callback: types.CallbackQuery, state: FSMContext):
    await support_handler(callback, state)


# --- ЛОГІКА ЗВ'ЯЗКУ З МЕНЕДЖЕРОМ (Новий флоу) ---

# Крок 1: Запитуємо телефон
@router.callback_query(F.data == "contact_manager")
@router.message(F.text.lower().contains("менеджер") |
                F.text.lower().contains("зв'язатися"))
async def ask_contact_for_support(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.waiting_for_support_contact)

    text = (
        "📞 **Щоб менеджер міг з вами зв'язатися, нам потрібен ваш номер телефону.**\n\n"
        "Натисніть кнопку нижче, щоб поділитися контактом 👇"
    )

    # Використовуємо твою існуючу клавіатуру get_contact_kb()
    if isinstance(event, types.CallbackQuery):
        # Оскільки get_contact_kb - це Reply клавіатура (внизу),
        # ми не можемо "редагувати" повідомлення з Inline кнопками на неї.
        # Тому просто надсилаємо нове повідомлення.
        await event.message.answer(text, reply_markup=get_contact_kb(), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_contact_kb(), parse_mode="Markdown")


# Крок 2: Отримали телефон -> Запитуємо причину
@router.message(LNDStates.waiting_for_support_contact, F.contact)
async def receive_support_contact(message: types.Message, state: FSMContext):
    contact = message.contact

    # Зберігаємо номер
    await state.update_data(phone_number=contact.phone_number)

    await state.set_state(LNDStates.waiting_for_support_reason)

    # ReplyKeyboardRemove прибирає кнопку "Поділитися контактом"
    await message.answer(
        "✅ Контакт отримано!\n\nТеперь коротко опишіть причину вашого звернення:",
        reply_markup=ReplyKeyboardRemove()
    )


# Крок 3: Отримали причину -> Відправляємо адміну
@router.message(LNDStates.waiting_for_support_reason)
async def finish_support_request(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()

    reason = message.text
    phone = user_data.get("phone_number", "Не вказано")
    username = user_data.get("username", "Немає ніку")
    first_name = user_data.get("first_name", "User")
    user_id = message.from_user.id

    # Відповідь користувачу
    await message.answer("⏳ Запит прийнято! Менеджер зв'яжеться з вами найближчим часом.")

    # Відправка адміну
    if ADMIN_ID:
        try:
            msg = (
                f"🆘 **Новий запит підтримки!**\n\n"
                f"👤 **Користувач:** {first_name} (@{username})\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"📞 **Телефон:** `{phone}`\n"
                f"📝 **Питання:** {reason}"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")

    # Повертаємо в головне меню
    await state.set_state(LNDStates.main_menu)
    await message.answer("Чим ще можу допомогти?", reply_markup=get_main_menu_kb())


# --- Інше ---
@router.message(F.text.contains("Дізнатися деталі мого курсу"))
async def my_course_handler(message: types.Message):
    await message.answer(
        "ℹ️ На даний момент за вашим акаунтом не закріплено активних курсів.\n"
        "Спробуйте обрати новий курс у меню 'Список наявних курсів'."
    )


@router.message()
async def fallback_handler(message: types.Message):
    await message.answer("Вибачте, я не зрозумів запит 😔\nБудь ласка, скористайтеся кнопками меню.")