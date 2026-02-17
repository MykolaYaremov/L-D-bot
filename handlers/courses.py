import asyncio
from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from html import unescape

from config import COURSE_CONFIG, DEFAULT_QUESTIONS
from keyboards.reply import get_request_contact_kb, get_main_menu_kb
from states import LNDStates
from parser import Parser

# Імпорт клавіатур
from keyboards.inline import (
    get_courses_list_kb, get_course_details_kb, get_knowledge_kb,
    get_back_to_course_kb, get_question_list_kb, get_back_to_list_kb
)
from handlers.common import send_interface_message

router = Router()
parser = Parser()


# --- ВАЖЛИВА ЗМІНА: ОТРИМАННЯ ДАНИХ ---
# Ми прибираємо глобальні змінні courses_list = ...
# Замість цього створюємо асинхронну функцію, яка бере дані з парсера.

async def get_dataset():
    """
    Отримує актуальний список курсів.
    Використовує run_in_executor (to_thread), щоб запит до сайту
    не блокував роботу бота, якщо настав час оновлення (раз на 24 год).
    """
    # Запускаємо синхронний метод парсера в окремому потоці
    raw_courses = await asyncio.to_thread(parser.parse_courses)
    # Фільтруємо прострочені курси
    return [c for c in raw_courses if not c['is_time_expired']]


async def get_course_by_id(course_id: int):
    """Шукає курс за ID в актуальному датасеті."""
    courses = await get_dataset()  # Отримуємо свіжі дані
    return next((c for c in courses if c["postId"] == course_id), None)


# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def extract_id(callback: types.CallbackQuery, index: int = 1) -> int:
    try:
        return int(callback.data.split("_")[index])
    except (ValueError, IndexError):
        return 0


async def handle_missing_course(event: types.Message | types.CallbackQuery):
    text = "⚠️ Курс не знайдено або він більше не актуальний."
    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text)


# --- 1. СПИСОК КУРСІВ ---

@router.message(~StateFilter(LNDStates.waiting_for_support_reason),
                F.text.lower().in_({"список наявних курсів", "хочу курс", "курси", "каталог"}) |
                (F.text.lower().contains("список") & F.text.lower().contains("курсів")))
async def show_courses_list(message: types.Message, state: FSMContext):
    if await state.get_state() == LNDStates.waiting_for_support_contact:
        await message.answer("🔄 Меню оновлено", reply_markup=get_main_menu_kb())

    await state.set_state(LNDStates.course_list)

    # Завантажуємо актуальні курси
    active_courses = await get_dataset()

    await send_interface_message(
        state, message,
        "📚 <b>Актуальні курси Sigma Software University:</b>\nОберіть курс, щоб дізнатися деталі:",
        get_courses_list_kb(active_courses)
    )


# --- 2. ДЕТАЛІ КУРСУ ---

async def render_course_details(target: types.Message | types.CallbackQuery, cid: int, state: FSMContext):
    course = await get_course_by_id(cid)  # <-- Оновлено (await)
    if not course:
        return await handle_missing_course(target)

    await state.set_state(LNDStates.current_course)
    await state.update_data(current_course_id=cid)

    text = (
        f"📘 <b>{course['title']}</b>\n\n"
        f"{unescape(course['content'][:500])}... <a href='{course['permalink']}'>Читати далі ➡️</a>\n\n"
        f"📅 Старт: <b>{course['date_start']}</b>\n"
        f"💻 Формат: <b>{course['location']}</b>\n"
        f"🕐 Тривалість: <b>{course['duration']}</b>"
    )
    kb = get_course_details_kb(cid)

    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                                       link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    else:
        await target.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: types.CallbackQuery, state: FSMContext):
    await render_course_details(callback, extract_id(callback), state)


@router.callback_query(F.data.startswith("back_to_course_"))
async def back_to_course_handler(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[-1])
    await render_course_details(callback, cid, state)


@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.course_list)

    active_courses = await get_dataset()  # <-- Оновлено

    await callback.message.edit_text(
        "📚 <b>Актуальні курси Sigma Software University:</b>",
        reply_markup=get_courses_list_kb(active_courses),
        parse_mode=ParseMode.HTML
    )


# --- 3. ФІНАНСОВИЙ БЛОК ---

async def _send_info_block(event, cid: int, text_generator_func):
    course = await get_course_by_id(cid)  # <-- Оновлено (await)
    if not course:
        return await handle_missing_course(event)

    text = text_generator_func(course)

    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text, parse_mode=ParseMode.HTML)


# Функції генерації тексту залишаються без змін
def _get_price_text(course):
    p_orig, p_curr = course.get('price_original'), course.get('price_current')
    currency = course.get('currency', 'грн')
    if p_orig and p_curr and str(p_orig) != str(p_curr):
        return (f"💳 ВАРТІСТЬ КУРСУ\n\n🔥 ЗНИЖКА!\n"
                f"❌ Було: {p_orig} {currency}\n✅ Зараз: {p_curr} {currency}")
    elif p_curr:
        return f"💳 ВАРТІСТЬ КУРСУ\n\n💰 Ціна: {p_curr} {currency}"
    return f"💳 ВАРТІСТЬ КУРСУ\n\nℹ️ {course.get('free_price') or 'Уточнюйте у менеджера'}"


def _get_payment_text(course):
    text = ("💳 СПОСОБИ ОПЛАТИ\n\n1. Карткою на сайті\n2. Рахунок-фактура (B2B)\n" +
            ("3. ✅ Доступна оплата частинами\n" if course.get('enable_payment_by_part') else "") +
            "\n🎫 ПРОМОКОД:\nЯкщо маєте код на знижку — введіть його при оплаті на сайті.")
    return text


@router.callback_query(F.data.startswith("price_"))
async def show_price(callback: types.CallbackQuery):
    await _send_info_block(callback, extract_id(callback), _get_price_text)


@router.message(LNDStates.current_course, F.text.lower().regexp(r"(скільки|вартість|оплата|ціна)"))
async def text_price(message: types.Message, state: FSMContext):
    if cid := (await state.get_data()).get("current_course_id"):
        await _send_info_block(message, cid, _get_price_text)


@router.callback_query(F.data.startswith("pay_"))
async def show_payment(callback: types.CallbackQuery):
    await _send_info_block(callback, extract_id(callback), _get_payment_text)


@router.message(LNDStates.current_course, F.text.lower().contains("оплат"))
async def text_payment_methods(message: types.Message, state: FSMContext):
    if cid := (await state.get_data()).get("current_course_id"):
        await _send_info_block(message, cid, _get_payment_text)


# --- 4. ЗВ'ЯЗОК З МЕНЕДЖЕРОМ ---

@router.callback_query(F.data.startswith("contact_manager_course_"))
async def contact_manager_from_course(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[-1])
    course = await get_course_by_id(cid)  # <-- Оновлено (await)

    await state.update_data(current_course_id=cid)
    if course:
        await state.update_data(support_course_title=course['title'], support_course_link=course['permalink'])

    await state.set_state(LNDStates.waiting_for_support_contact)
    await callback.message.edit_text(
        "📞 <b>Зв'язок з менеджером</b>\n"
        "Для зв'язку з вами, нам потрібен ваш номер телефону.\n\n"
        "👇 Натисніть кнопку <b>«📱 Надіслати свій контакт»</b> знизу екрану.",
        reply_markup=None, parse_mode="HTML"
    )
    msg = await callback.message.answer("Очікую контакт 👇", reply_markup=get_request_contact_kb())
    await state.update_data(last_interface_message_id=msg.message_id)
    await callback.answer()


# --- 5. ТЕСТ НА ВІДПОВІДНІСТЬ (QUIZ) ---

def calculate_quiz_result(course, scores: list) -> str:
    # Логіка без змін
    avg_score = sum(scores) / len(scores)
    user_level = round(avg_score)
    seniority_slugs = [s['slug'] for s in course.get('seniority', [])]
    if 'advanced' in seniority_slugs:
        course_level = 2
    elif 'middle' in seniority_slugs:
        course_level = 1
    else:
        course_level = 0
    level_name = course.get('seniority', [{'name': 'Middle'}])[0]['name']

    if user_level < course_level:
        return (f"⚠️ <b>Вам може бути складно.</b>\n\nЦей курс розрахований на рівень <b>{level_name}</b>. "
                "Ваші відповіді вказують на те, що вам може бракувати необхідної бази.")
    elif course_level == 0 and user_level >= 2:
        return (f"⚠️ <b>Курс може бути залегким.</b>\n\nЦе програма для старту з нуля. "
                "Вам може бути нудно на перших модулях.")
    else:
        return f"✅ <b>Це ідеальний метч!</b>\n\nВаш поточний рівень відповідає вимогам програми «{course['title']}»."


async def run_quiz_step(target, state: FSMContext, step: int, cid: int = None, prev_score: int = None):
    if step > 1:
        await state.update_data({f"score_{step - 1}": prev_score})
        cid = (await state.get_data()).get("current_course_id")
    else:
        await state.set_state(LNDStates.check_knowledge)
        if cid:
            await state.update_data(current_course_id=cid)
        else:
            cid = (await state.get_data()).get("current_course_id")

    course = await get_course_by_id(cid)  # <-- Оновлено (await)
    if not course: return await handle_missing_course(target)

    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    if step == 1:
        text, next_state = f"1️⃣ {questions['q1']}", LNDStates.check_knowledge
    elif step == 2:
        text, next_state = f"2️⃣ {questions['q2']}", LNDStates.check_experience
    elif step == 3:
        text, next_state = f"3️⃣ {questions['q3']}", LNDStates.check_extra
    else:
        data = await state.get_data()
        scores = [data.get("score_1", 0), data.get("score_2", 0), prev_score]
        result_text = calculate_quiz_result(course, scores)
        await target.message.edit_text(result_text, reply_markup=get_back_to_course_kb(cid), parse_mode=ParseMode.HTML)
        return

    if step > 1: await state.set_state(next_state)
    kb = get_knowledge_kb(course_id=cid)

    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# Хендлери кнопок тесту (без змін)
@router.callback_query(F.data.startswith("check_"))
async def start_check_btn(callback: types.CallbackQuery, state: FSMContext):
    await run_quiz_step(callback, state, step=1, cid=extract_id(callback))


@router.message(LNDStates.current_course, F.text.lower().regexp(r"(чи підійде|рівень|тест)"))
async def start_check_txt(message: types.Message, state: FSMContext):
    await run_quiz_step(message, state, step=1)


@router.callback_query(LNDStates.check_knowledge)
async def quiz_q2(callback: types.CallbackQuery, state: FSMContext):
    await run_quiz_step(callback, state, step=2, prev_score=int(callback.data.split("_")[-1]))


@router.callback_query(LNDStates.check_experience)
async def quiz_q3(callback: types.CallbackQuery, state: FSMContext):
    await run_quiz_step(callback, state, step=3, prev_score=int(callback.data.split("_")[-1]))


@router.callback_query(LNDStates.check_extra)
async def quiz_finish(callback: types.CallbackQuery, state: FSMContext):
    await run_quiz_step(callback, state, step=4, prev_score=int(callback.data.split("_")[-1]))


# --- 6. FAQ КУРСУ ---

async def show_faq_content(event, cid: int, item_index: int = None):
    course = await get_course_by_id(cid)  # <-- Оновлено (await)
    if not course: return await handle_missing_course(event)

    # FAQ парсинг легкий, можна залишити в потоці, або теж огорнути в to_thread за бажанням
    faq_list = await asyncio.to_thread(parser.parse_faq, course.get("permalink") or course.get("url"))

    if item_index is not None:
        try:
            item = faq_list[item_index]
            text, kb = f"<b>{item['question']}</b>\n\n{item['answer']}", get_back_to_list_kb(f"faq_{cid}")
        except IndexError:
            text, kb = "Помилка відображення.", get_back_to_course_kb(cid)
    else:
        if not faq_list:
            text, kb = "Питання відсутні для цього курсу.", get_back_to_course_kb(cid)
        else:
            text, kb = f"❓ <b>FAQ курсу «{course['title']}»:</b>", get_question_list_kb(faq_list, course_id=cid)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("faq_") & ~F.data.contains("general") & ~F.data.contains("item"))
async def faq_list_handler(callback: types.CallbackQuery):
    await show_faq_content(callback, cid=extract_id(callback))


@router.message(LNDStates.current_course, F.text.lower().regexp(r"(питання|faq)"))
async def faq_text_handler(message: types.Message, state: FSMContext):
    if cid := (await state.get_data()).get("current_course_id"):
        await show_faq_content(message, cid)


@router.callback_query(F.data.regexp(r"^faq_\d+_item_\d+$"))
async def faq_item_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    await show_faq_content(callback, cid=int(parts[1]), item_index=int(parts[3]))
    await callback.answer()