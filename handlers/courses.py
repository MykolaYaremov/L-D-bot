# from aiogram import Router, types, F
# from aiogram.enums import ParseMode
# from aiogram.fsm.context import FSMContext
# from html import unescape
#
# from config import COURSE_CONFIG, DEFAULT_QUESTIONS
# from keyboards.reply import get_request_contact_kb
# from states import LNDStates
# from parser import Parser
#
# # Імпортуємо клавіатури
# from keyboards.inline import (
#     get_courses_list_kb,
#     get_course_details_kb,
#     get_knowledge_kb,
#     get_back_to_course_kb,  # Переконайся, що додав цю функцію в inline.py
#     get_question_list_kb,
#     get_back_to_list_kb
# )
#
# # Імпортуємо функцію для "чистого" надсилання (з common.py)
# # УВАГА: Переконайся, що в handlers/common.py є функція send_interface_message
# from handlers.common import send_interface_message
#
# router = Router()
# parser = Parser()
#
# # Завантажуємо курси при старті
# courses_list = parser.parse_courses()
# active_courses = [c for c in courses_list if not c['is_time_expired']]
#
#
# # --- 1. СПИСОК КУРСІВ (Вхід з головного меню) ---
# @router.message(F.text.contains("Список наявних курсів"))
# async def show_courses_list(message: types.Message, state: FSMContext):
#     await state.set_state(LNDStates.course_list)
#     # Використовуємо функцію з common.py, щоб видалити старі кнопки меню
#     await send_interface_message(
#         state, message,
#         "📚 <b>Актуальні курси Sigma Software University:</b>\nОберіть курс, щоб дізнатися деталі:",
#         get_courses_list_kb(active_courses)
#     )
#
#
# # --- 2. ДЕТАЛІ КУРСУ (Перехід зі списку або повернення кнопкою "Назад") ---
# # Ця функція обробляє і відкриття курсу, і повернення до нього з підменю
# async def render_course_details(target: types.Message | types.CallbackQuery, cid: int, state: FSMContext):
#     course = next((item for item in courses_list if item["postId"] == cid), None)
#
#     if not course:
#         if isinstance(target, types.CallbackQuery):
#             await target.answer("Курс не знайдено.")
#         return
#
#     await state.set_state(LNDStates.current_course)
#     await state.update_data(current_course_id=cid)
#     print(course)
#     text = (
#         f"📘 <b>{course['title']}</b>\n\n"
#         f"{unescape(course['content'][:500])}... <a href='{course['permalink']}'>Читати далі ➡️</a>\n\n"
#         f"📅 Старт: <b>{course['date_start']}</b>\n"
#         f"💻 Формат: <b>{course['location']}</b>\n"
#         f"🕐 Тривалість: <b>{course['duration']}</b>"
#     )
#
#     kb = get_course_details_kb(cid)
#
#     if isinstance(target, types.CallbackQuery):
#         # РЕДАГУЄМО старе повідомлення (список або тест) на курс
#         await target.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML,
#                                        link_preview_options=types.LinkPreviewOptions(is_disabled=True))
#     else:
#         await target.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # Хендлер для натискання на кнопку курсу
# @router.callback_query(F.data.startswith("course_"))
# async def show_course_details(callback: types.CallbackQuery, state: FSMContext):
#     cid = int(callback.data.split("_")[1])
#     await render_course_details(callback, cid, state)
#
#
# # Хендлер для кнопки "Назад до курсу" (з тестів, FAQ тощо)
# @router.callback_query(F.data.startswith("back_to_course_"))
# async def back_to_course_handler(callback: types.CallbackQuery, state: FSMContext):
#     cid = int(callback.data.split("_")[-1])
#     await render_course_details(callback, cid, state)
#
#
# # --- 3. ПОВЕРНЕННЯ ДО СПИСКУ КУРСІВ ---
# @router.callback_query(F.data == "back_to_list")
# async def back_to_list(callback: types.CallbackQuery, state: FSMContext):
#     await state.set_state(LNDStates.course_list)
#     await callback.message.edit_text(
#         "📚 <b>Актуальні курси Sigma Software University:</b>",
#         reply_markup=get_courses_list_kb(active_courses),
#         parse_mode=ParseMode.HTML
#     )
#
#
# # # --- 4. ЦІНА ТА ОПЛАТА (Просто інфо, кнопки курсу ЛИШАЮТЬСЯ) ---
# # # Ти просив, щоб тут нічого не зникало, просто приходило повідомлення
# # @router.callback_query(F.data.startswith("price_"))
# # async def show_price(callback: types.CallbackQuery):
# #     cid = int(callback.data.split("_")[1])
# #     course = next((item for item in courses_list if item["postId"] == cid), None)
# #
# #     if course:
# #         price = course.get('price_current', course.get('free_price', 'Безкоштовно'))
# #         curr = course.get('currency', '')
# #         await callback.answer(f"💰 Вартість: {price} {curr}", show_alert=True)
# #     else:
# #         await callback.answer("Інформація відсутня", show_alert=True)
# # --- 4. ЦІНА ТА ОПЛАТА ---
# @router.callback_query(F.data.startswith("price_"))
# async def show_price(callback: types.CallbackQuery):
#     cid = int(callback.data.split("_")[1])
#
#     # Знаходимо курс
#     course = next((item for item in active_courses if item["postId"] == cid), None)
#
#     if not course:
#         await callback.answer("Інформація відсутня", show_alert=True)
#         return
#
#     # Отримуємо дані
#     price_original = course.get('price_original')
#     price_current = course.get('price_current')
#     currency = course.get('currency', 'грн')
#     free_price = course.get('free_price')
#
#     # Логіка формування тексту
#     text = ""
#
#     # СЦЕНАРІЙ 1: Є знижка (стара ціна != нова ціна)
#     if price_original and price_current and str(price_original) != str(price_current):
#         text = (
#             f"💳 ВАРТІСТЬ КУРСУ\n\n"  # Заголовок
#             f"🔥 ЗНИЖКА!\n"
#             f"❌ Було: {price_original} {currency}\n"
#             f"✅ Зараз: {price_current} {currency}"
#         )
#
#     # СЦЕНАРІЙ 2: Просто ціна (без знижки)
#     elif price_current:
#         text = (
#             f"💳 ВАРТІСТЬ КУРСУ\n\n"  # Заголовок
#             f"💰 Ціна: {price_current} {currency}"
#         )
#
#     # СЦЕНАРІЙ 3: Безкоштовно або немає ціни
#     else:
#         val = free_price if free_price else "Уточнюйте у менеджера"
#         text = (
#             f"💳 ВАРТІСТЬ КУРСУ\n\n"  # Заголовок
#             f"ℹ️ {val}"
#         )
#
#     # Відправляємо як Alert
#     await callback.answer(text, show_alert=True)
#     await callback.answer(text, show_alert=True)
#
#
# # --- 5. СПОСОБИ ОПЛАТИ ---
# @router.callback_query(F.data.startswith("pay_"))
# async def show_payment(callback: types.CallbackQuery):
#     cid = int(callback.data.split("_")[1])
#
#     # Знаходимо курс
#     course = next((item for item in active_courses if item["postId"] == cid), None)
#
#     if not course:
#         await callback.answer("Інформація відсутня", show_alert=True)
#         return
#
#     # Логіка (як у вашому старому коді)
#     enable_payment_by_part = course.get('enable_payment_by_part', False)
#
#     # Формуємо текст без HTML, але з гарною структурою
#     text = "💳 СПОСОБИ ОПЛАТИ\n\n"  # Заголовок
#
#     # Список методів
#     text += "1. Карткою на сайті\n"
#     text += "2. Рахунок-фактура (B2B)\n"
#
#     # Додаткова опція (якщо увімкнена)
#     if enable_payment_by_part:
#         text += "3. ✅ Доступна оплата частинами\n"
#
#     # Важлива інформація (замість курсиву та bold використовуємо відступи та знаки)
#     text += "\n🎫 ПРОМОКОД:\n"
#     text += "Якщо маєте код на знижку — введіть його при оплаті на сайті.\n\n"
#
#     text += "⚠️ Бот не приймає кошти!"
#
#     # Відправляємо спливаюче вікно
#     await callback.answer(text, show_alert=True)
#
#
# # Обробка кнопки "Зв'язатися з менеджером" (з меню курсу)
# @router.callback_query(F.data.startswith("contact_manager_course_"))
# async def contact_manager_from_course(callback: types.CallbackQuery, state: FSMContext):
#     # Отримуємо ID курсу
#     cid = int(callback.data.split("_")[-1])
#
#
#     # Зберігаємо ID курсу
#     await state.update_data(current_course_id=cid)
#
#     selected_course = next((c for c in active_courses if c['postId'] == cid), None)
#
#     if selected_course:
#         await state.update_data(
#             support_course_title=selected_course['title'],  # Назва
#             support_course_link=selected_course['permalink']  # Посилання
#         )
#
#     await state.set_state(LNDStates.waiting_for_support_contact)
#
#
#
#     # 1. Прибираємо inline-кнопки курсу, пишемо інструкцію
#     await callback.message.edit_text(
#         "📞 <b>Зв'язок з менеджером</b>\n"
#         "Для зв'язку з вами, нам потрібен ваш номер телефону.\n\n"
#         "👇 Натисніть кнопку <b>«📱 Надіслати свій контакт»</b> знизу екрану.\n"
#         "Або натисніть «Назад в меню» для скасування.",
#         reply_markup=None,
#         parse_mode="HTML"
#     )
#
#     # 2. Відкриваємо нижню клавіатуру для запиту контакту
#     msg = await callback.message.answer("Очікую контакт 👇", reply_markup=get_request_contact_kb())
#
#     # Зберігаємо ID повідомлення (щоб видалити потім, якщо треба, через common.py)
#     await state.update_data(last_interface_message_id=msg.message_id)
#     await callback.answer()
#
#
# # --- 5. ТЕСТ НА ВІДПОВІДНІСТЬ (Логіка зі старого коду + Структура нового) ---
#
# # 🛠 Допоміжна функція (визначає рівень курсу: 0=Beginner, 1=Middle, 2=Advanced)
# def get_min_course_level(seniority_list: list) -> int:
#     slugs = [s['slug'] for s in seniority_list]
#     if 'beginner' in slugs:
#         return 0
#     elif 'middle' in slugs:
#         return 1
#     elif 'advanced' in slugs:
#         return 2
#     return 0  # За замовчуванням
#
#
# # 1. СТАРТ ТЕСТУ (Питання 1)
# @router.callback_query(F.data.startswith("check_"))
# async def start_check_logic(callback: types.CallbackQuery, state: FSMContext):
#     cid = int(callback.data.split("_")[1])
#     await state.set_state(LNDStates.check_knowledge)
#
#     # Зберігаємо ID курсу в стан, щоб не загубити
#     await state.update_data(current_course_id=cid)
#
#     # Знаходимо питання для цього курсу
#     questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)
#
#     course = next((item for item in courses_list if item["postId"] == cid), None) # переробити отримання назви через state current_course_id
#
#     text = (
#         f"🎯 <b>Тест на відповідність курсу «{course['title']}»</b>\n\n"
#         f"1️⃣ {questions['q1']}"
#     )
#
#     # Клавіатура з варіантами відповіді (0, 1, 2)
#     # Передаємо cid, якщо у твоїй клавіатурі є кнопка "Назад"
#     kb = get_knowledge_kb(course_id=cid)
#
#     await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # 2. ПИТАННЯ 2
# @router.callback_query(LNDStates.check_knowledge)
# async def ask_q2(callback: types.CallbackQuery, state: FSMContext):
#     # Отримуємо відповідь на 1-ше питання (0, 1 або 2) із callback data
#     # Припускаємо, що кнопки повертають щось типу "ans_0", "ans_1" або просто цифри
#     # Якщо у тебе кнопки просто "0", "1", "2" -> то int(callback.data)
#     # Якщо формат "score_1", "score_2" -> то спліт.
#     # 👇 АДАПТУЙ ЦЕЙ РЯДОК ПІД СВОЮ КЛАВІАТУРУ get_knowledge_kb 👇
#     score_1 = int(callback.data.split("_")[-1])
#
#     await state.update_data(score_1=score_1)
#     await state.set_state(LNDStates.check_experience)
#
#     data = await state.get_data()
#     cid = data.get("current_course_id")
#     questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)
#
#     text = f"2️⃣ {questions['q2']}"
#     kb = get_knowledge_kb(course_id=cid)
#
#     await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # 3. ПИТАННЯ 3
# @router.callback_query(LNDStates.check_experience)
# async def ask_q3(callback: types.CallbackQuery, state: FSMContext):
#     score_2 = int(callback.data.split("_")[-1])
#     await state.update_data(score_2=score_2)
#     await state.set_state(LNDStates.check_extra)
#
#     data = await state.get_data()
#     cid = data.get("current_course_id")
#     questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)
#
#     text = f"3️⃣ {questions['q3']}"
#     kb = get_knowledge_kb(course_id=cid)
#
#     await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # 4. ФІНАЛ (Розрахунок результату)
# @router.callback_query(LNDStates.check_extra)
# async def finish_check(callback: types.CallbackQuery, state: FSMContext):
#     score_3 = int(callback.data.split("_")[-1])
#
#     data = await state.get_data()
#     score_1 = data.get("score_1", 0)
#     score_2 = data.get("score_2", 0)
#     cid = data.get("current_course_id")
#
#     # Знаходимо сам об'єкт курсу, щоб дізнатися його рівень (Seniority)
#     course = next((item for item in active_courses if item["postId"] == cid), None)
#
#     if not course:
#         await callback.message.edit_text("Помилка: курс не знайдено.")
#         return
#
#     # --- МАТЕМАТИКА (Зі старого коду) ---
#     # 1. Рахуємо рівень користувача (0, 1 або 2)
#     avg_score = (score_1 + score_2 + score_3) / 3
#     user_level = round(avg_score)
#
#     # 2. Рахуємо рівень курсу (0=Beginner, 1=Middle, 2=Advanced)
#     course_level = get_min_course_level(course.get('seniority', []))
#
#     # Отримуємо гарну назву рівня для тексту
#     level_name = course.get('seniority', [{'name': 'Middle'}])[0]['name']
#
#     res_text = ""
#
#     # --- ЛОГІКА ПОРІВНЯННЯ ---
#
#     # Ситуація А: Користувач слабший за курс
#     if user_level < course_level:
#         res_text = (
#             f"⚠️ <b>Вам може бути складно.</b>\n\n"
#             f"Цей курс розрахований на рівень <b>{level_name}</b>.\n"
#             f"Ваші відповіді вказують на те, що вам може бракувати необхідної бази. "
#             f"Радимо переглянути програму детальніше або почати з простішого курсу."
#         )
#
#     # Ситуація Б: Курс для новачків, а користувач профі (User=2, Course=0)
#     elif course_level == 0 and user_level >= 2:
#         res_text = (
#             f"⚠️ <b>Курс може бути залегким.</b>\n\n"
#             f"Це програма для старту з нуля. Судячи з ваших відповідей (3/3 балів), "
#             f"вам може бути нудно на перших модулях. Але якщо хочете систематизувати знання — велкам!"
#         )
#
#     # Ситуація В: Ідеальний метч
#     else:
#         res_text = (
#             f"✅ <b>Це ідеальний метч!</b>\n\n"
#             f"Ваш поточний рівень чудово відповідає вимогам програми «{course['title']}». "
#             f"Ви зможете засвоювати матеріал у комфортному темпі."
#         )
#
#     # Кнопка "Назад до курсу"
#     kb = get_back_to_course_kb(cid)
#
#     await callback.message.edit_text(res_text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # --- 6. FAQ КУРСУ (Курс зникає -> З'являється FAQ) ---
#
# # Допоміжна функція відображення списку
# async def perform_show_course_faq(event: types.Message | types.CallbackQuery, cid: int):
#     # Шукаємо курс у списку
#     course = next((item for item in courses_list if item["postId"] == cid), None)
#
#     if not course:
#         if isinstance(event, types.CallbackQuery):
#             await event.answer("Курс не знайдено.")
#         return
#
#     # !!! ТВОЯ ЛОГІКА: беремо питання за посиланням курсу !!!
#     # Якщо parser.parse_faq вміє приймати url - це спрацює
#     faq_list = parser.parse_faq(course.get("permalink") or course.get("url"))
#
#     if not faq_list:
#         text = "Питання відсутні для цього курсу."
#         # Все одно даємо кнопку назад до курсу
#         kb = get_back_to_course_kb(cid)
#     else:
#         text = f"❓ <b>FAQ курсу «{course['title']}»:</b>"
#         # Передаємо cid, щоб працювала кнопка "Назад до курсу"
#         kb = get_question_list_kb(faq_list, course_id=cid)
#
#     if isinstance(event, types.CallbackQuery):
#         await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#     else:
#         await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
#
#
# # Хендлер списку питань (Callback)
# @router.callback_query(F.data.startswith("faq_") & ~F.data.contains("general") & ~F.data.contains("item"))
# async def show_course_faq(callback: types.CallbackQuery):
#     cid = int(callback.data.split("_")[1])
#     await perform_show_course_faq(callback, cid)
#
#
# # Хендлер відповіді на питання (Callback)
# @router.callback_query(F.data.regexp(r"^faq_\d+_item_\d+$"))
# async def show_course_faq_item(callback: types.CallbackQuery):
#     parts = callback.data.split("_")
#     cid = int(parts[1])
#     idx = int(parts[3])
#
#     course = next((item for item in courses_list if item["postId"] == cid), None)
#
#     if course:
#         # Знову парсимо, щоб знайти відповідь (або краще кешувати, але робимо як ти просив)
#         faq_list = parser.parse_faq(course.get("permalink") or course.get("url"))
#
#         try:
#             item = faq_list[idx]
#             text = f"<b>{item['question']}</b>\n\n{item['answer']}"
#
#             # Кнопка повернення до списку питань цього курсу
#             kb = get_back_to_list_kb(f"faq_{cid}")
#
#             await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
#         except (IndexError, TypeError):
#             await callback.message.answer("Помилка відображення питання.")
#
#     await callback.answer()



from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from html import unescape

from config import COURSE_CONFIG, DEFAULT_QUESTIONS
from keyboards.reply import get_request_contact_kb, get_main_menu_kb
from states import LNDStates
from parser import Parser

# Імпортуємо клавіатури
from keyboards.inline import (
    get_courses_list_kb,
    get_course_details_kb,
    get_knowledge_kb,
    get_back_to_course_kb,
    get_question_list_kb,
    get_back_to_list_kb
)

# Імпортуємо функцію для "чистого" надсилання
from handlers.common import send_interface_message

router = Router()
parser = Parser()

# Завантажуємо курси при старті
courses_list = parser.parse_courses()
active_courses = [c for c in courses_list if not c['is_time_expired']]


# --- 1. СПИСОК КУРСІВ (Вхід з головного меню + Текстові тригери) ---
@router.message(~StateFilter(LNDStates.waiting_for_support_reason),
                F.text.contains("Список наявних курсів") |
                F.text.lower().contains("хочу курс") |
                (F.text.lower().contains("список") & F.text.lower().contains("курсів")) |
                F.text.lower().contains("курси") |
                F.text.lower().contains("каталог"))
async def show_courses_list(message: types.Message, state: FSMContext):
    # --- ФІКС КЛАВІАТУРИ ---
    # Якщо юзер був у стані надсилання контакту, примусово повертаємо головне меню
    current_state = await state.get_state()
    if current_state == LNDStates.waiting_for_support_contact:
        await message.answer("", reply_markup=get_main_menu_kb()) # 🔄 Меню оновлено
    # -----------------------

    await state.set_state(LNDStates.course_list)
    # Використовуємо функцію з common.py
    await send_interface_message(
        state, message,
        "📚 <b>Актуальні курси Sigma Software University:</b>\nОберіть курс, щоб дізнатися деталі:",
        get_courses_list_kb(active_courses)
    )


# --- 2. ДЕТАЛІ КУРСУ ---
async def render_course_details(target: types.Message | types.CallbackQuery, cid: int, state: FSMContext):
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if not course:
        if isinstance(target, types.CallbackQuery):
            await target.answer("Курс не знайдено.")
        return

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
    cid = int(callback.data.split("_")[1])
    await render_course_details(callback, cid, state)


@router.callback_query(F.data.startswith("back_to_course_"))
async def back_to_course_handler(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[-1])
    await render_course_details(callback, cid, state)


# --- 3. ПОВЕРНЕННЯ ДО СПИСКУ КУРСІВ ---
@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LNDStates.course_list)
    await callback.message.edit_text(
        "📚 <b>Актуальні курси Sigma Software University:</b>",
        reply_markup=get_courses_list_kb(active_courses),
        parse_mode=ParseMode.HTML
    )


# --- 4. ЦІНА ТА ОПЛАТА (Універсальна функція) ---
async def perform_show_price(event: types.Message | types.CallbackQuery, cid: int):
    # Знаходимо курс
    course = next((item for item in active_courses if item["postId"] == cid), None)

    if not course:
        if isinstance(event, types.CallbackQuery):
            await event.answer("Інформація відсутня", show_alert=True)
        else:
            await event.answer("Інформація відсутня")
        return

    # Отримуємо дані
    price_original = course.get('price_original')
    price_current = course.get('price_current')
    currency = course.get('currency', 'грн')
    free_price = course.get('free_price')

    text = ""
    # СЦЕНАРІЙ 1: Є знижка
    if price_original and price_current and str(price_original) != str(price_current):
        text = (
            f"💳 ВАРТІСТЬ КУРСУ\n\n"
            f"🔥 ЗНИЖКА!\n"
            f"❌ Було: {price_original} {currency}\n"
            f"✅ Зараз: {price_current} {currency}"
        )
    # СЦЕНАРІЙ 2: Просто ціна
    elif price_current:
        text = (
            f"💳 ВАРТІСТЬ КУРСУ\n\n"
            f"💰 Ціна: {price_current} {currency}"
        )
    # СЦЕНАРІЙ 3: Безкоштовно або немає ціни
    else:
        val = free_price if free_price else "Уточнюйте у менеджера"
        text = (
            f"💳 ВАРТІСТЬ КУРСУ\n\n"
            f"ℹ️ {val}"
        )

    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text, parse_mode=ParseMode.HTML)


# Виклик кнопкою
@router.callback_query(F.data.startswith("price_"))
async def show_price(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_price(callback, cid)


# Виклик текстом
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


# --- 5. СПОСОБИ ОПЛАТИ (Універсальна функція) ---
async def perform_show_payment(event: types.Message | types.CallbackQuery, cid: int):
    course = next((item for item in active_courses if item["postId"] == cid), None)

    if not course:
        if isinstance(event, types.CallbackQuery):
            await event.answer("Інформація відсутня", show_alert=True)
        return

    enable_payment_by_part = course.get('enable_payment_by_part', False)

    text = "💳 СПОСОБИ ОПЛАТИ\n\n"
    text += "1. Карткою на сайті\n"
    text += "2. Рахунок-фактура (B2B)\n"

    if enable_payment_by_part:
        text += "3. ✅ Доступна оплата частинами\n"

    text += "\n🎫 ПРОМОКОД:\n"
    text += "Якщо маєте код на знижку — введіть його при оплаті на сайті.\n\n"
    text += "⚠️ Бот не приймає кошти!"

    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text, parse_mode=ParseMode.HTML)


# Виклик кнопкою
@router.callback_query(F.data.startswith("pay_"))
async def show_payment(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_payment(callback, cid)


# Виклик текстом
@router.message(LNDStates.current_course,
                F.text.lower().contains("способи оплати") |
                F.text.lower().contains("методи оплати") |
                F.text.lower().contains("оплатити"))
async def text_payment_methods(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("current_course_id")
    if cid:
        await perform_show_payment(message, cid)


# --- ЗВ'ЯЗОК З МЕНЕДЖЕРОМ ---
@router.callback_query(F.data.startswith("contact_manager_course_"))
async def contact_manager_from_course(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[-1])
    await state.update_data(current_course_id=cid)

    selected_course = next((c for c in active_courses if c['postId'] == cid), None)
    if selected_course:
        await state.update_data(
            support_course_title=selected_course['title'],
            support_course_link=selected_course['permalink']
        )

    await state.set_state(LNDStates.waiting_for_support_contact)

    await callback.message.edit_text(
        "📞 <b>Зв'язок з менеджером</b>\n"
        "Для зв'язку з вами, нам потрібен ваш номер телефону.\n\n"
        "👇 Натисніть кнопку <b>«📱 Надіслати свій контакт»</b> знизу екрану.\n"
        "Або натисніть «Назад в меню» для скасування.",
        reply_markup=None,
        parse_mode="HTML"
    )

    msg = await callback.message.answer("Очікую контакт 👇", reply_markup=get_request_contact_kb())
    await state.update_data(last_interface_message_id=msg.message_id)
    await callback.answer()


# --- 5. ТЕСТ НА ВІДПОВІДНІСТЬ (Універсальна функція) ---

def get_min_course_level(seniority_list: list) -> int:
    slugs = [s['slug'] for s in seniority_list]
    if 'beginner' in slugs:
        return 0
    elif 'middle' in slugs:
        return 1
    elif 'advanced' in slugs:
        return 2
    return 0


# 1. СТАРТ ТЕСТУ (Питання 1)
async def perform_start_check(event: types.Message | types.CallbackQuery, state: FSMContext, cid: int = None):
    await state.set_state(LNDStates.check_knowledge)

    # Якщо викликали кнопкою, CID в кнопці. Якщо текстом - беремо зі стейту
    if cid:
        await state.update_data(current_course_id=cid)
    else:
        data = await state.get_data()
        cid = data.get("current_course_id")

    if not cid:
        if isinstance(event, types.Message): await event.answer("Курс не обрано")
        return

    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)
    course = next((item for item in courses_list if item["postId"] == cid), None)

    text = (
        f"🎯 <b>Тест на відповідність курсу «{course['title']}»</b>\n\n"
        f"1️⃣ {questions['q1']}"
    )
    kb = get_knowledge_kb(course_id=cid)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# Виклик кнопкою
@router.callback_query(F.data.startswith("check_"))
async def start_check_logic(callback: types.CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[1])
    await perform_start_check(callback, state, cid)


# Виклик текстом
@router.message(LNDStates.current_course,
                F.text.lower().contains("чи підійде") |
                F.text.lower().contains("рівень") |
                F.text.lower().contains("тест"))
async def start_check_text(message: types.Message, state: FSMContext):
    await perform_start_check(message, state)


# 2. ПИТАННЯ 2
@router.callback_query(LNDStates.check_knowledge)
async def ask_q2(callback: types.CallbackQuery, state: FSMContext):
    score_1 = int(callback.data.split("_")[-1])
    await state.update_data(score_1=score_1)
    await state.set_state(LNDStates.check_experience)

    data = await state.get_data()
    cid = data.get("current_course_id")
    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    text = f"2️⃣ {questions['q2']}"
    kb = get_knowledge_kb(course_id=cid)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# 3. ПИТАННЯ 3
@router.callback_query(LNDStates.check_experience)
async def ask_q3(callback: types.CallbackQuery, state: FSMContext):
    score_2 = int(callback.data.split("_")[-1])
    await state.update_data(score_2=score_2)
    await state.set_state(LNDStates.check_extra)

    data = await state.get_data()
    cid = data.get("current_course_id")
    questions = COURSE_CONFIG.get(cid, DEFAULT_QUESTIONS)

    text = f"3️⃣ {questions['q3']}"
    kb = get_knowledge_kb(course_id=cid)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# 4. ФІНАЛ
@router.callback_query(LNDStates.check_extra)
async def finish_check(callback: types.CallbackQuery, state: FSMContext):
    score_3 = int(callback.data.split("_")[-1])

    data = await state.get_data()
    score_1 = data.get("score_1", 0)
    score_2 = data.get("score_2", 0)
    cid = data.get("current_course_id")

    course = next((item for item in active_courses if item["postId"] == cid), None)

    if not course:
        await callback.message.edit_text("Помилка: курс не знайдено.")
        return

    avg_score = (score_1 + score_2 + score_3) / 3
    user_level = round(avg_score)
    course_level = get_min_course_level(course.get('seniority', []))
    level_name = course.get('seniority', [{'name': 'Middle'}])[0]['name']

    res_text = ""
    if user_level < course_level:
        res_text = (
            f"⚠️ <b>Вам може бути складно.</b>\n\n"
            f"Цей курс розрахований на рівень <b>{level_name}</b>.\n"
            f"Ваші відповіді вказують на те, що вам може бракувати необхідної бази. "
        )
    elif course_level == 0 and user_level >= 2:
        res_text = (
            f"⚠️ <b>Курс може бути залегким.</b>\n\n"
            f"Це програма для старту з нуля. Судячи з ваших відповідей (3/3 балів), "
            f"вам може бути нудно на перших модулях."
        )
    else:
        res_text = (
            f"✅ <b>Це ідеальний метч!</b>\n\n"
            f"Ваш поточний рівень чудово відповідає вимогам програми «{course['title']}»."
        )

    kb = get_back_to_course_kb(cid)
    await callback.message.edit_text(res_text, reply_markup=kb, parse_mode=ParseMode.HTML)


# --- 6. FAQ КУРСУ (Універсальна функція) ---

async def perform_show_course_faq(event: types.Message | types.CallbackQuery, cid: int):
    course = next((item for item in courses_list if item["postId"] == cid), None)

    if not course:
        if isinstance(event, types.CallbackQuery):
            await event.answer("Курс не знайдено.")
        return

    faq_list = parser.parse_faq(course.get("permalink") or course.get("url"))

    if not faq_list:
        text = "Питання відсутні для цього курсу."
        kb = get_back_to_course_kb(cid)
    else:
        text = f"❓ <b>FAQ курсу «{course['title']}»:</b>"
        kb = get_question_list_kb(faq_list, course_id=cid)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# Хендлер списку питань (Callback)
@router.callback_query(F.data.startswith("faq_") & ~F.data.contains("general") & ~F.data.contains("item"))
async def show_course_faq(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    await perform_show_course_faq(callback, cid)


# Хендлер списку питань (Текст)
@router.message(LNDStates.current_course,
                F.text.lower().contains("питання") |
                F.text.lower().contains("часті запит") |
                F.text.lower().contains("faq"))
async def text_course_faq(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("current_course_id")
    if cid:
        await perform_show_course_faq(message, cid)


# Хендлер відповіді на питання (Callback)
@router.callback_query(F.data.regexp(r"^faq_\d+_item_\d+$"))
async def show_course_faq_item(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cid = int(parts[1])
    idx = int(parts[3])

    course = next((item for item in courses_list if item["postId"] == cid), None)

    if course:
        faq_list = parser.parse_faq(course.get("permalink") or course.get("url"))
        try:
            item = faq_list[idx]
            text = f"<b>{item['question']}</b>\n\n{item['answer']}"
            kb = get_back_to_list_kb(f"faq_{cid}")
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except (IndexError, TypeError):
            await callback.message.answer("Помилка відображення питання.")

    await callback.answer()