from aiogram.fsm.state import StatesGroup, State


class LNDStates(StatesGroup):
    main_menu = State()  # Головне меню

    # Стани підтримки
    waiting_for_support_contact = State()  # 1. Чекаємо номер телефону
    waiting_for_support_reason = State()  # 2. Чекаємо текст звернення

    # Стани курсів
    course_list = State()  # Перегляд списку
    current_course = State()  # Перегляд конкретного курсу

    # Стани тесту (Quiz)
    check_knowledge = State()  # Питання 1
    check_experience = State()  # Питання 2
    check_extra = State()  # Фінал