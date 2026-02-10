from aiogram import Router, types, F
from database import COURSES

router = Router()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq(callback: types.CallbackQuery):
    cid = callback.data.split("_")[1]
    # Витягуємо текст FAQ з бази даних
    faq_text = COURSES[cid]['faq']['text']

    await callback.message.answer(faq_text)
    await callback.answer()