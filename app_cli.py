"""Графічна оболонка над Claude Code CLI (без API-ключа, за вашою підпискою).
Запуск: streamlit run app_cli.py

Кожен запуск — окрема папка runs/<час>/ з копією агентів і збирача Word.
Усередині запускається `claude -p` зі сценарієм із .claude/commands/lab-report.md."""
import json
import shutil
import subprocess
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
RUNS = ROOT / "runs"
COPY_FILES = ["build_docx.py", "docx_builder.py", "config.py"]
ALLOWED = ["Read", "Write", "Edit", "Glob", "Grep", "Task", "Agent", "Bash(python *)", "Bash(python3 *)"]
TIMEOUT_SEC = 30 * 60

st.set_page_config(page_title="LabGenerator · Claude Code", page_icon="🧪", layout="wide")
st.title("🧪 LabGenerator · через Claude Code")
st.caption("Працює через встановлений Claude Code за вашою підпискою — API-ключ не потрібен.")

if not shutil.which("claude"):
    st.error("Не знайдено команду `claude`. Встановіть Claude Code та увійдіть у ньому.")
    st.stop()

with st.sidebar:
    st.header("Титульна сторінка")
    department = st.text_input("Кафедра", "Кафедра ___")
    student = st.text_area("Студент", "Студент групи ___\nПрізвище Ім'я", height=80)
    teacher = st.text_input("Викладач", "Викладач: ___")
    city_year = st.text_input("Місто, рік", "Львів – 2026")

files = st.file_uploader("Методичка та дані (pdf, docx, txt, csv)", accept_multiple_files=True,
                         type=["pdf", "docx", "txt", "md", "csv"])
extra = st.text_area("Додаткові вимоги", placeholder="Напр.: варіант 7, без теоретичної частини, висновки на пів сторінки",
                     height=80)


def build_prompt(extra_text: str) -> str:
    cmd = (ROOT / ".claude" / "commands" / "lab-report.md").read_text(encoding="utf-8")
    body = cmd.split("---", 2)[-1].strip()  # без YAML-шапки
    title = (f"Дані титульної сторінки (занеси в title_page у plan.json): "
             f"department={department!r}, student={student!r}, teacher={teacher!r}, city_year={city_year!r}.")
    return body.replace("$ARGUMENTS", f"{extra_text or '(немає)'}\n{title}")


def prepare_run(uploaded) -> Path:
    run = RUNS / time.strftime("%Y%m%d_%H%M%S")
    (run / "inputs").mkdir(parents=True)
    (run / "output" / "figs").mkdir(parents=True)
    shutil.copytree(ROOT / ".claude" / "agents", run / ".claude" / "agents")
    for name in COPY_FILES:
        shutil.copy(ROOT / name, run / name)
    for f in uploaded:
        (run / "inputs" / Path(f.name).name).write_bytes(f.getvalue())
    return run


def describe_tool(block: dict) -> str:
    name, inp = block.get("name", ""), block.get("input", {})
    if name in ("Task", "Agent"):
        return f"🤖 Агент **{inp.get('subagent_type', '?')}**: {inp.get('description', '')}"
    if name == "Bash":
        return f"⚙️ Виконую: `{str(inp.get('command', ''))[:120]}`"
    if name in ("Write", "Edit"):
        return f"📝 Пишу файл `{Path(str(inp.get('file_path', ''))).name}`"
    if name == "Read":
        return f"📖 Читаю `{Path(str(inp.get('file_path', ''))).name}`"
    return f"🔧 {name}"


def run_claude(run: Path, prompt: str, log):
    """Запускає claude -p, читає потік JSON-подій, повертає (текст підсумку, помилка?)."""
    cmd = [shutil.which("claude"), "-p", "--output-format", "stream-json", "--verbose",
           "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED]
    proc = subprocess.Popen(cmd, cwd=run, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    proc.stdin.write(prompt)
    proc.stdin.close()
    started, final, is_error = time.time(), "", False
    for line in proc.stdout:
        if time.time() - started > TIMEOUT_SEC:
            proc.kill()
            return "Перевищено ліміт часу (30 хв).", True
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for block in ev["message"].get("content", []):
                if block.get("type") == "tool_use":
                    log(describe_tool(block))
                elif block.get("type") == "text" and block["text"].strip():
                    log(block["text"].strip())
        elif ev.get("type") == "result":
            final, is_error = ev.get("result", ""), bool(ev.get("is_error"))
    proc.wait()
    return final, is_error or proc.returncode != 0


if st.button("Згенерувати звіт", type="primary", disabled=not files):
    run = prepare_run(files)
    with st.status("Claude Code працює (кілька хвилин)...", expanded=True) as status:
        final, failed = run_claude(run, build_prompt(extra), lambda m: st.write(m))
        status.update(label="Помилка" if failed else "Готово!", state="error" if failed else "complete")
    st.session_state["run"] = {"dir": run, "final": final, "failed": failed}

res = st.session_state.get("run")
if res:
    run = res["dir"]
    docs = sorted((run / "output").glob("*.docx"))
    if docs and not res["failed"]:
        st.success("Звіт готовий")
        st.download_button("⬇️ Завантажити Word", docs[0].read_bytes(), file_name=docs[0].name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif res["failed"]:
        st.error("Не вдалося завершити. Деталі нижче.")
    st.markdown("### Підсумок від Claude")
    st.markdown(res["final"] or "_(порожньо)_")
    figs = sorted((run / "output" / "figs").glob("*.png"))
    if figs:
        st.markdown("### Графіки")
        for fig in figs:
            st.image(str(fig), caption=fig.name)
    st.caption(f"Папка запуску: runs/{run.name}")
