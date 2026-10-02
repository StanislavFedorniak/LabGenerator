# LabGenerator

Мультиагентна система: методичка + дані -> Word-звіт.

1. `pip install -r requirements.txt`
2. Задати ключ: `$env:ANTHROPIC_API_KEY = "..."` (PowerShell)
3. Покласти методичку/дані (pdf, docx, txt, csv) у `inputs/`
4. `python main.py` -> `output/Lab_<номер>.docx`

Агенти: Планувальник -> Аналітик (код + графіки, якщо є CSV) -> Автор -> Рецензент (цикл) -> збирач Word.
Оформлення документа налаштовується в `config.py`.
`python test_build.py` перевіряє аналітику й Word без API.

## Робота через Claude Code (без API-ключа)

1. Покласти методичку й дані в `inputs/`.
2. Відкрити Claude Code в цій папці й виконати `/lab-report [додаткові вимоги]`.
3. Забрати `output/Lab_<номер>.docx`.

Агенти (`.claude/agents/`): `lab-analyst`, `lab-writer`, `lab-reviewer`. Сценарій — `.claude/commands/lab-report.md`.
Word збирає `build_docx.py` (оформлення в `config.py`).
Веб-інтерфейс: `streamlit run app.py` (потрібен API-ключ).
