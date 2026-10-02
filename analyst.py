"""Агент-аналітик: модель пише Python-код для аналізу CSV, ми його запускаємо,
а при помилці віддаємо traceback назад моделі на виправлення."""
import os
import re
import subprocess
import sys
from pathlib import Path

import agents
import config


ANALYST = """Ти — аналітик даних. Напиши ОДИН самодостатній Python-скрипт, що виконує обчислення,
потрібні для лабораторної за методичкою, на CSV-файлах із папки inputs/ (шляхи відносні: inputs/<файл>).
Вимоги:
- бібліотеки: pandas, numpy, scipy, scikit-learn, matplotlib (backend 'Agg');
- ключові числові результати виводь через print() з підписами (їх прочитає автор звіту);
- кожен графік зберігай у output/figs/figN.png (N з 1), plt.savefig(..., dpi=150, bbox_inches='tight');
  підписи осей і заголовки графіків — українською;
- на початку скрипта створи папку output/figs (os.makedirs, exist_ok=True);
- не вигадуй даних: працюй лише з тим, що є у файлах.
Відповідь — лише код в одному блоці ```python ... ```."""


def _extract_code(text: str) -> str:
    m = re.search(r"```python\s*(.*?)```", text, re.S)
    return m.group(1) if m else text


def _run(code: str, workdir: Path) -> tuple[bool, str]:
    (workdir / "output").mkdir(parents=True, exist_ok=True)
    script = workdir / "output" / "analysis.py"
    script.write_text(code, encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(script)], cwd=workdir, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONUTF8": "1", "MPLBACKEND": "Agg"}, timeout=config.ANALYSIS_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return False, f"Перевищено ліміт часу {config.ANALYSIS_TIMEOUT_SEC} с"
    if p.returncode != 0:
        return False, (p.stderr or "")[-3000:]
    return True, (p.stdout or "")[-6000:]


def run_analysis(materials: str, workdir: Path) -> dict:
    """Повертає {'text': stdout скрипта, 'figures': [імена png], 'code': код}."""
    figs = workdir / "output" / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    for old in figs.glob("fig*.png"):
        old.unlink()

    prompt = f"МАТЕРІАЛИ (методичка і початок CSV):\n{materials}"
    code = _extract_code(agents.ask(ANALYST, prompt, max_tokens=6000))
    for attempt in range(1, config.ANALYSIS_MAX_ATTEMPTS + 1):
        ok, output = _run(code, workdir)
        if ok:
            figures = sorted(p.name for p in figs.glob("fig*.png"))
            return {"text": output, "figures": figures, "code": code}
        print(f"  спроба {attempt}: помилка в коді аналітика, виправляю")
        fix = (f"{prompt}\n\nТВІЙ КОД:\n```python\n{code}\n```\n\n"
               f"ПОМИЛКА ПІД ЧАС ЗАПУСКУ:\n{output}\n\nВиправ і поверни повний код.")
        code = _extract_code(agents.ask(ANALYST, fix, max_tokens=6000))
    return {"text": f"[Аналіз не вдався: {output}]", "figures": [], "code": code}
