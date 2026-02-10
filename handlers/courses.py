from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from database import COURSES
from states import LNDStates
from keyboards.inline import (
    get_courses_list_kb,
    get_course_details_kb,
    get_knowledge_kb,
    get_experience_kb
)

router = Router()


# Сценарій 2: Список курсів
@router.message(F.text == "1. Список наявних курсів")
async def show_courses_list(message: types.Message):
    await message.answer("Ось актуальні курси Sigma Software University:", reply_markup=get_courses_list_kb(COURSES))


# Сценарій 3 & 6: Деталі курсу
@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: types.CallbackQuery):
    cid = callback.data.split("_")[1]
    course = COURSES[cid]
    text = (
        f"📘 **{course['name']}**\n\n"
        f"{course['details']}\n\n"
        f"📅 **Старт:** {course['start_date']}\n"
        f"💻 **Формат:** {course['format']}"
    )
    await callback.message.edit_text(text, reply_markup=get_course_details_kb(cid))


# Сценарій 4: Вартість
@router.callback_query(F.data.startswith("price_"))
async def show_price(callback: types.CallbackQuery):
    cid = callback.data.split("_")[1]
    price = COURSES[cid]['price']
    await callback.message.answer(
        f"💰 Вартість навчання: **{price}**.\nУ ціну входять лекції, перевірка ДЗ та сертифікат.")
    await callback.answer()


# Сценарій 5: Оплата
@router.callback_query(F.data.startswith("pay_"))
async def show_payment_methods(callback: types.CallbackQuery):
    text = (
        "💳 **Способи оплати:**\n"
        "1. Карткою на сайті.\n"
        "2. Рахунок-фактура (B2B).\n"
        "3. Оплата частинами.\n\n"
        "⚠️ *Бот не приймає кошти. Посилання надішле менеджер.*"
    )
    await callback.message.answer(text)
    await callback.answer()


# --- СЦЕНАРІЙ 7: Перевірка відповідності (2 етапи) ---

# Крок 1: Питання про знання
@router.callback_query(F.data.startswith("check_"))
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.check_knowledge)
    await callback.message.answer("1️⃣ Як ви оцінюєте свої теоретичні знання?", reply_markup=get_knowledge_kb())
    await callback.answer()


# Крок 2: Питання про досвід
@router.callback_query(LNDStates.check_knowledge)
async def ask_experience(callback: types.CallbackQuery, state: FSMContext):
    # Зберігаємо відповідь 1
    await state.update_data(knowledge=callback.data)

    await state.set_state(LNDStates.check_experience)
    await callback.message.edit_text("2️⃣ Чи був у вас практичний досвід з базами даних?",
                                     reply_markup=get_experience_kb())


# Крок 3: Результат
@router.callback_query(LNDStates.check_experience)
async def finish_check(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    knowledge = data.get("knowledge")
    experience = callback.data

    # Логіка "розумного" підбору
    if knowledge == "know_2" and experience == "exp_2":
        res = "⚠️ **Цей курс може бути занадто легким для вас.** Він розрахований на новачків."
    elif knowledge == "know_0" and experience == "exp_0":
        res = "✅ **Ідеально підходить!** Ми вчимо з самого нуля."
    else:
        res = "✅ **Вам підходить.** Курс структурує ваші знання."

    await callback.message.answer(res)
    await state.set_state(LNDStates.main_menu)  # Повертаємо в меню
    await callback.answer()