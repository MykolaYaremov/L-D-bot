from aiogram import Router, types, F
from keyboards.inline import get_question_list_kb, get_back_to_list_kb
from parser import Parser

router = Router()
parser = Parser()


# Вхід в ЗАГАЛЬНИЙ FAQ (з меню підтримки)
# Важливо: в inline.py кнопка має callback_data="faq_general"
@router.callback_query(F.data == "faq_general")
async def default_faq_list(callback: types.CallbackQuery):
    # Парсимо загальні питання
    faq_list = parser.parse_faq()

    if not faq_list:
        text = "Питання відсутні наразі."
        kb = None  # Або кнопка назад
    else:
        text = "❓ <b>Часті питання (Загальні):</b>"
        # course_id=None -> означає, що кнопки "Назад до курсу" не буде
        kb = get_question_list_kb(faq_list, course_id=None)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# Перегляд конкретного питання (Загальне)
# callback формат: faq_None_item_{index} (бо course_id=None)
@router.callback_query(F.data.startswith("faq_None_item_"))
async def default_faq_item(callback: types.CallbackQuery):
    try:
        idx = int(callback.data.split("_")[-1])
        faq_list = parser.parse_faq()
        item = faq_list[idx]

        text = f"<b>{item['question']}</b>\n\n{item['answer']}"

        # Кнопка повернення до списку загальних питань
        kb = get_back_to_list_kb("faq_general")

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except (ValueError, IndexError):
        await callback.message.edit_text("Питання не знайдено.", reply_markup=get_back_to_list_kb("faq_general"))

    await callback.answer()