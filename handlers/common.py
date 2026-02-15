from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import LNDStates
from keyboards.reply import get_contact_kb, get_main_menu_kb
from keyboards.inline import get_support_kb
from config import ADMIN_ID

router = Router()


# Сценарій 1: Старт
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(LNDStates.authorisation)
    await message.answer("Привіт! Я L&D бот Sigma Software\nПоділіться контактом для подальшої роботи", reply_markup=get_contact_kb())


@router.message(LNDStates.authorisation, F.contact)
async def process_contact(message: types.Message, state: FSMContext):

    contact = message.contact

    await state.update_data(
        phone_number=contact.phone_number,
        first_name=contact.first_name,
        user_id=contact.user_id
    )

    await state.set_state(LNDStates.main_menu)

    await message.answer(f"Вітаю, {contact.first_name}! Чим можу допомогти?", reply_markup=get_main_menu_kb())


# Кнопка 2: Підтримка
@router.message(F.text.lower().contains("підтримка") | 
                F.text.lower().contains("допомога")) 
async def support_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.main_menu)
    text = (
        "🛠 Служба підтримки\n\n"
        "Якщо у вас виникли технічні проблеми або питання щодо організації, "
        "ви можете зв'язатися з менеджером напряму або переглянути часті запитання."
    )
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(
            text,
            reply_markup=get_support_kb()
        )
        await event.answer()
    else:
        await event.answer(
            text,
            reply_markup=get_support_kb()
        )
        
@router.callback_query(F.data == "back_to_support")
async def back_to_support(callback: types.CallbackQuery, state: FSMContext):
    await support_handler(callback, state)

# Кнопка 3: Деталі мого курсу (Заглушка, бо немає бази користувачів)
@router.message(F.text.contains("Дізнатися деталі мого курсу"))
async def my_course_handler(message: types.Message):
    await message.answer(
        "ℹ️ На даний момент за вашим акаунтом не закріплено активних курсів.\nСпробуйте обрати новий курс у меню 'Список наявних курсів'.")

# Кнопка зв'язатися з менеджером
@router.callback_query(F.data == "contact_manager")
async def ask_support_reason(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.support_reason)
    text = "Будь ласка, коротко опишіть причину звернення:"
    if isinstance(event, types.CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else: 
        await event.answer(text)

# Виклик зв'язку з менеджером через message       
@router.message(F.text.lower().contains("менеджер") | 
                F.text.lower().contains("зв'язатися"))
async def support_text(message: types.Message, state: FSMContext):
    await ask_support_reason(message, state)

# Сценарій 10: Передача діалогу (Handover)
@router.message(LNDStates.support_reason)
async def contact_manager(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(support_reason=message.text)

    user_data = await state.get_data()
    username = message.from_user.username or "Без ніку"
    phone_number = user_data.get("phone_number", "Немає")
    reason = user_data.get("support_reason", "Немає причини")

    await message.answer("⏳ Запит прийнято! Менеджер отримав ваше звернення і напише вам в особисті.")
    
    if ADMIN_ID:
        try:
            msg = (
                f"🆘 Новий запит!\n"
                f"👤 Юзер: @{username} (ID: {message.from_user.id})\n"
                f"📞 Телефон: {phone_number}\n"
                f"💬 Причина: {reason}"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=msg)
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")

    await state.set_state(LNDStates.main_menu)
    await message.answer("Чим можу допомогти?", reply_markup=get_main_menu_kb())

# Сценарій 9: Fallback (Останній рубіж)
@router.message()
async def fallback_handler(message: types.Message):
    await message.answer("Вибачте, я не зрозумів запит 😔\nБудь ласка, скористайтеся кнопками меню.")