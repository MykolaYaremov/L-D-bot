from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from config import COURSE_CONFIG, DEFAULT_QUESTIONS
from states import LNDStates

from html import unescape

from keyboards.inline import (
    get_courses_list_kb,
    get_course_details_kb,
    get_knowledge_kb,
    get_question_list_kb,
    get_back_to_list_kb
)

from parser import Parser

router = Router()
parser = Parser()

courses_list = parser.parse_courses()

active_courses = [c for c in courses_list if not c['is_time_expired']]

# Сценарій 2: Список курсів
@router.message(F.text.lower().contains("хочу курс") | 
                (F.text.lower().contains("список") & F.text.lower().contains("курсів")) | 
                F.text.lower().contains("курси") | 
                F.text.lower().contains("каталог"))
async def show_courses_list(message: types.Message, state: FSMContext):
    await state.set_state(LNDStates.course_list)
    await message.answer("Ось актуальні курси Sigma Software University:", reply_markup=get_courses_list_kb(active_courses))


# Сценарій 3 & 6: Деталі курсу
@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[1])
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if (course):
        await state.set_state(LNDStates.current_course)
        await state.update_data(current_course_id=cid)

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
async def perform_show_price(event: types.Message | types.CallbackQuery, cid: int):
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if (course):

        price_original = course['price_original']
        price_current = course['price_current']
        currency = course['currency']

        if (price_original and price_current and price_current != price_original):
            text = f"💰 Вартість навчання: <s>{price_original}</s> <b>{price_current} {currency}</b>\n"
        elif (price_current):
            text = f"💰 Вартість навчання: <b>{price_current} {currency}</b> \n"
        else:
            price = course['free_price']
            text = f"💰 Вартість навчання: <b>{price}</b>\n"
    
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(text, parse_mode=ParseMode.HTML)
            await event.answer()
        else:
            await event.answer(text, parse_mode=ParseMode.HTML)

# Виклик через callback
@router.callback_query(F.data.startswith("price_"))
async def show_price(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_price(callback, cid)

# Виклик через message
@router.message(LNDStates.current_course, 
                F.text.lower().contains("скільки коштує") | 
                F.text.lower().contains("вартість") |
                F.text.lower().contains("оплата") | 
                F.text.lower().contains("ціна"))
async def text_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("current_course_id")
    if cid:
        await perform_show_price(message, cid)


# Сценарій 5: Оплата
async def perform_show_payment_methods(event: types.Message | types.CallbackQuery, cid: int):
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
        
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(text, parse_mode=ParseMode.HTML)
            await event.answer()
        else:
            await event.answer(text, parse_mode=ParseMode.HTML)

# Виклик через callback
@router.callback_query(F.data.startswith("pay_"))
async def show_payment_methods(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_payment_methods(callback, cid)

# Виклик через message
@router.message(LNDStates.current_course, 
                F.text.lower().contains("способи оплати") | 
                F.text.lower().contains("методи оплати") | 
                F.text.lower().contains("оплатити"))
async def text_payment_methods(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("current_course_id")
    if cid:
        await perform_show_payment_methods(message, cid)


# --- СЦЕНАРІЙ 7: Глибока перевірка (3 питання) ---

# Допоміжна функція для визначення мінімального рівня курсу
def get_min_course_level(seniority_list: list) -> int:
    slugs = [s['slug'] for s in seniority_list]
    if 'beginner' in slugs:
        return 0
    elif 'middle' in slugs:
        return 1
    elif 'advanced' in slugs:
        return 2
    return 0


# ----------------- ПИТАННЯ 1 -----------------
async def perform_start_check(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.check_knowledge)

    data = await state.get_data()
    cid = data.get("current_course_id")
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if not course:
        await event.answer("Спочатку оберіть курс.")
        return

    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    text = (
        f"🎯 <b>Тест на відповідність курсу «{course['title']}»</b>\n\n"
        f"1️⃣ {questions['q1']}"
    )

    # Використовуємо клавіатуру (0=Ні, 1=Трохи, 2=Так)
    kb = get_knowledge_kb()

    if isinstance(event, types.CallbackQuery):
        await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("check_"))
@router.message(LNDStates.current_course,
                F.text.lower().contains("чи підійде") |
                F.text.lower().contains("рівень"))
async def start_check(event: types.Message | types.CallbackQuery, state: FSMContext):
    if isinstance(event, types.CallbackQuery):
        await perform_start_check(event, state)
    else:
        data = await state.get_data()
        if data.get("current_course_id"):
            await perform_start_check(event, state)
        else:
            await event.answer("Оберіть курс зі списку.")


# ----------------- ПИТАННЯ 2 -----------------
@router.callback_query(LNDStates.check_knowledge)
async def ask_q2(callback: types.CallbackQuery, state: FSMContext):
    # Зберігаємо бал за 1 питання (0, 1 або 2)
    score_1 = int(callback.data.split("_")[1])
    await state.update_data(score_1=score_1)

    await state.set_state(LNDStates.check_experience)  # Переходимо до 2 питання

    data = await state.get_data()
    cid = data.get("current_course_id")
    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    text = f"2️⃣ {questions['q2']}"

    # Використовуємо ту саму клавіатуру, або get_experience_kb, якщо вона повертає такі ж значення
    await callback.message.edit_text(text, reply_markup=get_knowledge_kb(), parse_mode=ParseMode.HTML)


# ----------------- ПИТАННЯ 3 (НОВЕ) -----------------
@router.callback_query(LNDStates.check_experience)
async def ask_q3(callback: types.CallbackQuery, state: FSMContext):
    # Зберігаємо бал за 2 питання
    score_2 = int(callback.data.split("_")[1])
    await state.update_data(score_2=score_2)

    await state.set_state(LNDStates.check_extra)  # Переходимо до 3 питання

    data = await state.get_data()
    cid = data.get("current_course_id")
    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    text = f"3️⃣ {questions['q3']}"

    await callback.message.edit_text(text, reply_markup=get_knowledge_kb(), parse_mode=ParseMode.HTML)


# ----------------- ФІНАЛ (Розрахунок) -----------------
@router.callback_query(LNDStates.check_extra)
async def finish_check(callback: types.CallbackQuery, state: FSMContext):
    # Отримуємо бал за 3 питання
    score_3 = int(callback.data.split("_")[1])

    data = await state.get_data()
    score_1 = data.get("score_1", 0)
    score_2 = data.get("score_2", 0)
    cid = data.get("current_course_id")

    # --- МАТЕМАТИКА ---
    # Максимальна сума балів = 6. Ділимо на 3 питання.
    # Результат: 0..0.6 -> Beginner (0), 0.7..1.4 -> Middle (1), 1.5..2 -> Advanced (2)
    avg_score = (score_1 + score_2 + score_3) / 3
    user_level = round(avg_score)

    # Отримуємо дані про курс
    course = next((item for item in courses_list if item["postId"] == cid), None)
    course_level = get_min_course_level(course.get('seniority', []))

    res_text = ""

    # Логіка порівняння (та сама, але тепер точніша завдяки 3 питанням)
    if user_level < course_level:
        res_text = (
            "⚠️ <b>Вам може бути складно.</b>\n\n"
            f"Курс вимагає рівня <b>{course.get('seniority', [{'name': 'Middle'}])[0]['name']}</b>, а ваші відповіді вказують на те, що вам бракує деяких базових навичок. "
            "Рекомендуємо підтягнути базу перед стартом."
        )
    elif course_level == 0 and user_level == 2:
        res_text = (
            "⚠️ <b>Курс може бути залегким.</b>\n\n"
            "Це програма для старту з нуля. З вашим досвідом (бали 3/3) вам може бути нудно на перших модулях."
        )
    else:
        res_text = (
            "✅ <b>Це ідеальний метч!</b>\n\n"
            "Ваш рівень знань та досвід чудово відповідають вимогам програми. "
            "Ви зможете взяти максимум від цього навчання."
        )

    # Додаємо кнопку повернення
    back_kb = get_course_details_kb(cid)

    await callback.message.edit_text(res_text, reply_markup=back_kb, parse_mode=ParseMode.HTML)
    await state.set_state(LNDStates.current_course)
    await callback.answer()


# 8. FAQ курсу (список питань) 
async def perform_show_course_faq(event: types.Message | types.CallbackQuery, cid: int):
    course = next((item for item in courses_list if item["postId"] == cid), None)
    
    if course:
        faq_list = parser.parse_faq(course["permalink"])

        if not faq_list:
            text = "Питання відсутні для цього курсу."
        else:
            text = "Часті запитання по цьому курсу:"
            kb = get_question_list_kb(faq_list, course_id=cid)

        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=kb if 'kb' in locals() else None)
            await event.answer()
        else:
            await event.answer(text, reply_markup=kb if 'kb' in locals() else None)

# Виклик через callback
@router.callback_query((F.data.startswith("faq_") & ~F.data.contains("_item_")))
async def show_course_faq(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_course_faq(callback, cid)

# Виклик через message
@router.message(LNDStates.current_course, 
                F.text.lower().contains("питання") | 
                F.text.lower().contains("часті запит") | 
                F.text.lower().contains("faq"))
async def text_course_faq(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("current_course_id")
    if cid:
        await perform_show_course_faq(message, cid)


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