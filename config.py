"""Налаштування: модель і оформлення Word-документа. Підлаштуйте під свій шаблон."""

MODEL = "claude-sonnet-5-5"
MAX_REVIEW_ROUNDS = 2  # скільки разів Рецензент може повернути звіт Автору
ANALYSIS_MAX_ATTEMPTS = 3   # скільки разів Аналітик може виправляти свій код
ANALYSIS_TIMEOUT_SEC = 120  # ліміт часу на запуск аналізу

# Оформлення документа
FONT = "Times New Roman"
FONT_SIZE = 14           # pt
LINE_SPACING = 1.5
FIRST_LINE_INDENT_CM = 1.25
MARGINS_CM = {"left": 3.0, "right": 1.0, "top": 2.0, "bottom": 2.0}

# Титульна сторінка (змініть на свої дані)
TITLE_PAGE = {
    "university": "Національний університет «Львівська політехніка»",
    "department": "Кафедра ___",
    "student": "Студент групи ___\nПрізвище Ім'я",
    "teacher": "Викладач: ___",
    "city_year": "Львів – 2026",
}
