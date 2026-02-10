from aiogram.fsm.state import StatesGroup, State


class LNDStates(StatesGroup):
    choosing_role = State()  # Сценарій 1
    main_menu = State()  # Головне меню

    # Сценарій 7 (Quiz)
    check_knowledge = State()  # Питання 1: Рівень знань
    check_experience = State()  # Питання 2: Досвід