from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import LNDStates
from keyboards.reply import get_role_kb, get_main_menu_kb
from keyboards.inline import get_support_kb
from config import ADMIN_ID

router = Router()


# --- Сценарій 1: Старт ---
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(LNDStates.choosing_role)
    await message.answer("Привіт! Я L&D бот Sigma Software.\nОберіть вашу роль:", reply_markup=get_role_kb())


@router.message(LNDStates.choosing_role)
async def process_role(message: types.Message, state: FSMContext):
    await state.update_data(role=message.text)
    await state.set_state(LNDStates.main_menu)
    await message.answer(f"Вітаю, {message.text}! Чим можу допомогти?", reply_markup=get_main_menu_kb())


# Кнопка 2: Підтримка
@router.message(F.text.contains("Потрібна підтримка"))
async def support_handler(message_or_callback):
    text = (
        "🛠 Служба підтримки\n\n"
        "Якщо у вас виникли технічні проблеми або питання щодо організації, "
        "ви можете зв'язатися з менеджером напряму або переглянути часті запитання."
    )
    if hasattr(message_or_callback, "message"):  # callback
        await message_or_callback.message.edit_text(
            text,
            reply_markup=get_support_kb()
        )
        await message_or_callback.answer()
    else:  # message
        await message_or_callback.answer(
            text,
            reply_markup=get_support_kb()
        )
        
@router.callback_query(F.data == "back_to_support")
async def back_to_support(callback: types.CallbackQuery):
    await support_handler(callback)

# Кнопка 3: Деталі мого курсу (Заглушка, бо немає бази користувачів)
@router.message(F.text.contains("Дізнатися деталі мого курсу"))
async def my_course_handler(message: types.Message):
    await message.answer(
        "ℹ️ На даний момент за вашим акаунтом не закріплено активних курсів.\nСпробуйте обрати новий курс у меню 'Список наявних курсів'.")


# --- Сценарій 10: Передача діалогу (Handover) ---
@router.callback_query(F.data == "contact_manager")
async def contact_manager(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    role = user_data.get("role", "Невідомо")
    username = callback.from_user.username or "Без ніку"

    await callback.message.answer("⏳ Запит прийнято! Менеджер отримав ваше звернення і напише вам в особисті.")

    if ADMIN_ID:
        try:
            msg = (
                f"🆘 **Новий запит!**\n"
                f"👤 Юзер: @{username} (ID: {callback.from_user.id})\n"
                f"🎓 Роль: {role}"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=msg)
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")

    await callback.answer()


# --- Сценарій 9: Fallback (Останній рубіж) ---
@router.message()
async def fallback_handler(message: types.Message):
    await message.answer("Вибачте, я не зрозумів запит 😔\nБудь ласка, скористайтеся кнопками меню.")