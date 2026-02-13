from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from states import LNDStates

from html import unescape

from keyboards.inline import (
    get_courses_list_kb,
    get_course_details_kb,
    get_knowledge_kb,
    get_experience_kb,
    get_question_list_kb,
    get_back_to_list_kb
)

from parser import Parser

router = Router()
parser = Parser()

courses_list = parser.parse_courses()

active_courses = [c for c in courses_list if not c['is_time_expired']]

# Сценарій 2: Список курсів
@router.message(F.text == "1. Список наявних курсів")
async def show_courses_list(message: types.Message):
    await message.answer("Ось актуальні курси Sigma Software University:", reply_markup=get_courses_list_kb(active_courses))


# Сценарій 3 & 6: Деталі курсу
@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if (course):

        text = (
            f"📘<b>{course['title']}</b>\n\n"
            f"{unescape(course['content'])} <a href='{course['permalink']}'>сайт курсу</a>\n\n"
            f"📅 Старт: <b>{course['date_start']}, {course['time_start']}</b>\n"
            f"💻 Формат: <b>{course['location']}</b>\n"
            f"🕐 Тривалість: <b>{course['duration']}</b>\n"
        )

        await callback.message.edit_text(text, reply_markup=get_course_details_kb(cid), parse_mode=ParseMode.HTML, link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    else:
        await callback.message.edit_text("Something went wrong")


# Сценарій 4: Вартість
@router.callback_query(F.data.startswith("price_"))
async def show_price(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if (course):

        price_original = course['price_original']
        price_current = course['price_current']
        currency = course['currency']

        if (price_original and price_current and price_current != price_original):
            await callback.message.answer(
                f"💰 Вартість навчання: <s>{price_original}</s> <b>{price_current} {currency}</b>\n",  parse_mode=ParseMode.HTML)
        elif (price_current):
            await callback.message.answer(
                f"💰 Вартість навчання: <b>{price_current} {currency}</b> \n",  parse_mode=ParseMode.HTML)
        else:
            price = course['free_price']
            await callback.message.answer(
                f"💰 Вартість навчання: <b>{price}</b>\n", parse_mode=ParseMode.HTML)
    
        await callback.answer()
        

# Сценарій 5: Оплата
@router.callback_query(F.data.startswith("pay_"))
async def show_payment_methods(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if (course):
        enable_payment_by_part = course['enable_payment_by_part']
        text = (
            "💳 <b>Способи оплати:</b>\n"
            "1. Карткою на сайті.\n"
            "2. Рахунок-фактура (B2B).\n"  
        )

        if(enable_payment_by_part):
            text += "3. Доступна оплата частинами\n"

        text += ("\n🎫 <i><b>Якщо у вас є персональний промокод на знижку, будь ласка, введіть його в поле коментарів реєстраційної форми на сайті</b></i>  \n \n"
            "⚠️ <i><b>Бот не приймає кошти</b></i>")
        
        await callback.message.answer(text, parse_mode=ParseMode.HTML)
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

    await callback.message.edit_text(res)
    await state.set_state(LNDStates.main_menu)  # Повертаємо в меню
    await callback.answer()

# 8. FAQ курсу (список питань)
@router.callback_query(F.data.startswith("faq_") & ~F.data.contains("_item_"))
async def show_course_faq(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    course = next((item for item in courses_list if item["postId"] == cid), None)
    
    if course:
        faq_list = parser.parse_faq(course["permalink"])

        if not faq_list:
            await callback.message.edit_text("Питання відсутні.")
            await callback.answer()
            return

        await callback.message.edit_text(
            "Часті запитання по цьому курсу:",
            reply_markup=get_question_list_kb(faq_list, course_id=cid)
        )
        await callback.answer()

# 8. FAQ курсу (відповідь на питання)
@router.callback_query(
    F.data.regexp(r"^faq_\d+_item_\d+$")
)
async def show_course_faq_item(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cid = int(parts[1])
    idx = int(parts[3])

    course = next((item for item in courses_list if item["postId"] == cid), None)

    if course:

        faq_list = parser.parse_faq(course["permalink"])

        try:
            item = faq_list[idx]
            text = f"<b>{item['question']}</b>\n\n{item['answer']}"

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_back_to_list_kb(f"faq_{cid}")
            )
        except IndexError:
            await callback.message.edit_text("Питання не знайдено")

        await callback.answer()