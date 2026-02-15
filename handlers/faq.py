from aiogram import Router, types, F
from keyboards.inline import (
    get_question_list_kb,
    get_back_to_list_kb
)
from parser import Parser

router = Router()
parser = Parser()

@router.callback_query(F.data == "faq")
async def default_faq_list(event: types.Message | types.CallbackQuery):
    faq_list = parser.parse_faq()

    if not faq_list:
        text = "Питання відсутні наразі."
    else:
        text = "Часті питання (FAQ):"
        kb = get_question_list_kb(faq_list)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb if 'kb' in locals() else None)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb if 'kb' in locals() else None)


@router.message(F.text.lower().contains("питання") | 
                F.text.lower().contains("часті запит") | 
                F.text.lower().contains("faq"))
async def default_faq_text(message: types.Message):
    await default_faq_list(message)      


@router.callback_query(F.data.startswith("faq_item_"))
async def default_faq_item(callback: types.CallbackQuery):
    try:
        idx = int(callback.data.split("_")[-1])
        faq_list = parser.parse_faq()
        item = faq_list[idx]

        text = f"<b>{item['question']}</b>\n\n{item['answer']}"
        kb = get_back_to_list_kb("faq")
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "Питання не знайдено.",
            reply_markup=kb
        )
    await callback.answer()