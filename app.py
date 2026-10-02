"""Веб-інтерфейс. Запуск: streamlit run app.py"""
import os
import tempfile
from pathlib import Path

import streamlit as st

import agents
import pipeline

st.set_page_config(page_title="LabGenerator", page_icon="🧪", layout="wide")
st.title("🧪 LabGenerator")
st.caption("Методичка + дані → готовий Word-звіт. Працюють агенти: Планувальник → Аналітик → Автор → Рецензент.")

STAGES = {"plan": "📋 Планувальник", "analysis": "📊 Аналітик", "write": "✍️ Автор",
          "review": "🔍 Рецензент", "build": "📄 Збирач Word"}

with st.sidebar:
    st.header("Налаштування")
    api_key = st.text_input("API-ключ Anthropic", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""),
                            help="Ключ не зберігається, живе лише в цій сесії.")
    st.subheader("Титульна сторінка")
    department = st.text_input("Кафедра", "Кафедра ___")
    student = st.text_area("Студент", "Студент групи ___\nПрізвище Ім'я", height=80)
    teacher = st.text_input("Викладач", "Викладач: ___")
    city_year = st.text_input("Місто, рік", "Львів – 2026")

files = st.file_uploader("Методичка та дані (pdf, docx, txt, csv)", accept_multiple_files=True,
                         type=["pdf", "docx", "txt", "md", "csv"])

if st.button("Згенерувати звіт", type="primary", disabled=not files):
    if not api_key:
        st.error("Вкажіть API-ключ у боковій панелі.")
        st.stop()
    agents.set_api_key(api_key)

    # Кожен запуск — власна тимчасова папка, щоб користувачі не заважали одне одному
    workdir = Path(tempfile.mkdtemp(prefix="labgen_"))
    (workdir / "inputs").mkdir()
    for f in files:
        (workdir / "inputs" / Path(f.name).name).write_bytes(f.getvalue())

    with st.status("Агенти працюють...", expanded=True) as status:
        def log(stage, msg, data=None):
            st.write(f"**{STAGES[stage]}** — {msg}")
        try:
            st.session_state["result"] = pipeline.generate(
                workdir, {"department": department, "student": student, "teacher": teacher, "city_year": city_year},
                log=log)
            status.update(label="Готово!", state="complete")
        except Exception as e:  # показуємо помилку, а не падаємо
            status.update(label="Помилка", state="error")
            st.exception(e)

res = st.session_state.get("result")
if res:
    st.success(f"Звіт готовий: лабораторна № {res['plan'].get('lab_number', '')} — {res['plan'].get('title', '')}")
    st.download_button("⬇️ Завантажити Word", res["docx"].read_bytes(), file_name=res["docx"].name,
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    tab_text, tab_plan, tab_an, tab_rev = st.tabs(["Текст звіту", "План", "Аналіз", "Рецензія"])
    with tab_text:
        for name, text in res["sections"].items():
            st.subheader(name)
            st.markdown(text)
    with tab_plan:
        st.json(res["plan"])
    with tab_an:
        an = res["analysis"]
        if not an:
            st.info("CSV-файлів не було, аналіз пропущено.")
        else:
            st.text(an["text"])
            for fig in an["figures"]:
                st.image(str(res["docx"].parent / "figs" / fig), caption=fig)
            with st.expander("Код, який написав Аналітик"):
                st.code(an["code"], language="python")
    with tab_rev:
        for i, r in enumerate(res["reviews"], 1):
            st.markdown(f"**Раунд {i}:** {'✅ схвалено' if r['ok'] else '❌ є зауваження'}")
            for issue in r.get("issues", []):
                st.markdown(f"- {issue}")
    st.warning("Перевірте місця з міткою [ПОТРІБНІ ДАНІ: ...] — їх має доповнити студент.")
