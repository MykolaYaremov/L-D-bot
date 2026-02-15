from aiogram.fsm.state import StatesGroup, State


class LNDStates(StatesGroup):
    main_menu = State()  # Головне меню
    waiting_for_support_contact = State()  # НОВИЙ СТАН (чекаємо номер)
    waiting_for_support_reason = State()  # НОВИЙ СТАН (чекаємо текст питання)
    support_reason = State()  # новий стан для введення причини
    course_list = State() # список курсів
    current_course = State() # поточний курс
    # Сценарій 7 (Quiz)
    check_knowledge = State()  # Питання 1: Рівень знань
    check_experience = State()  # Питання 2: Досвід
    check_extra = State() # Досвід/Задачі