"""Запуск з терміналу: python main.py  (методичка і дані лежать у inputs/).
Зручніше з інтерфейсом: streamlit run app.py"""
from pathlib import Path

import pipeline

if __name__ == "__main__":
    res = pipeline.generate(Path(__file__).parent)
    print(f"Готово: {res['docx']}")
