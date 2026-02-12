from aiogram import Router, types, F
from keyboards.inline import (
    get_question_list_kb,
    get_back_to_list_kb
)
from parser import Parser

router = Router()
parser = Parser()

@router.callback_query(F.data == "faq")
async def default_faq_list(callback: types.CallbackQuery):
    faq_list = parser.parse_faq()

    if not faq_list:
        await callback.message.edit_text("Питання відсутні наразі.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Часті питання (FAQ):",
        reply_markup=get_question_list_kb(faq_list)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_item_"))
async def default_faq_item(callback: types.CallbackQuery):
    try:
        idx = int(callback.data.split("_")[-1])
        faq_list = parser.parse_faq()
        item = faq_list[idx]

        text = f"<b>{item['question']}</b>\n\n{item['answer']}"

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_to_list_kb("faq")
        )
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "Питання не знайдено.",
            reply_markup=get_back_to_list_kb("faq")
        )
    await callback.answer()