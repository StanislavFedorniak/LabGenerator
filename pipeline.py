"""Уся логіка конвеєра в одному місці. Її викликають і main.py (термінал), і app.py (веб)."""
from pathlib import Path

import agents
import analyst
import config
import docx_builder
from readers import read_inputs

ROOT = Path(__file__).parent


def generate(workdir: Path, title_page: dict | None = None, log=lambda stage, msg, data=None: print(f"[{stage}] {msg}")) -> dict:
    """workdir — окрема папка запуску: workdir/inputs (вхід) і workdir/output (результат).
    log(stage, msg, data) викликається на кожному кроці — інтерфейс показує це користувачу."""
    workdir = Path(workdir)
    inputs = workdir / "inputs"
    materials = read_inputs(inputs)
    has_csv = any(inputs.glob("*.csv"))

    log("plan", "Планувальник складає структуру...")
    plan = agents.ask_json(agents.PLANNER, materials)
    log("plan", "Структуру складено", plan)

    analysis_block, analysis = "", None
    if has_csv:
        log("analysis", "Аналітик пише й запускає код...")
        analysis = analyst.run_analysis(materials, workdir)
        figs = ", ".join(analysis["figures"]) or "(немає)"
        analysis_block = (f"\n\nРЕЗУЛЬТАТИ АНАЛІЗУ (вивід скрипта):\n{analysis['text']}\n"
                          f"ДОСТУПНІ РИСУНКИ: {figs}\n")
        log("analysis", f"Готово, рисунків: {len(analysis['figures'])}", analysis)
    else:
        log("analysis", "CSV немає — крок пропущено")
    context = materials + analysis_block

    log("write", "Автор пише розділи...")
    sections = {}
    for sec in plan["sections"]:
        log("write", f"Розділ «{sec['name']}»")
        task = (f"МАТЕРІАЛИ:\n{context}\n\nНапиши розділ «{sec['name']}».\n"
                f"Що має бути: {sec['goal']}\nПотрібні дані: {sec['needs']}")
        sections[sec["name"]] = agents.ask(agents.WRITER, task)

    reviews = []
    for round_no in range(1, config.MAX_REVIEW_ROUNDS + 1):
        log("review", f"Рецензент перевіряє (раунд {round_no})...")
        draft = "\n\n".join(f"## {n}\n{t}" for n, t in sections.items())
        review = agents.ask_json(agents.REVIEWER, f"МАТЕРІАЛИ:\n{context}\n\nЧЕРНЕТКА:\n{draft}")
        reviews.append(review)
        if review["ok"]:
            log("review", "Схвалено", review)
            break
        log("review", f"Зауважень: {len(review['issues'])}, Автор переписує", review)
        feedback = "\n".join(f"- {i}" for i in review["issues"])
        for name in sections:
            task = (f"МАТЕРІАЛИ:\n{context}\n\nРозділ «{name}», поточна версія:\n{sections[name]}\n\n"
                    f"Зауваження рецензента до всього звіту:\n{feedback}\n\n"
                    "Виправ цей розділ з урахуванням релевантних зауважень. Якщо до нього їх нема — "
                    "поверни без змін.")
            sections[name] = agents.ask(agents.WRITER, task)

    log("build", "Збираю Word...")
    out = workdir / "output" / f"Lab_{plan.get('lab_number', 'X')}.docx"
    out.parent.mkdir(exist_ok=True)
    docx_builder.build(plan, sections, out, title_page, workdir / "output" / "figs")
    log("build", f"Готово: {out.name}")
    return {"plan": plan, "analysis": analysis, "sections": sections, "reviews": reviews, "docx": out}
