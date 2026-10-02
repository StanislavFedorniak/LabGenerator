"""Повний прогін конвеєра з підміненою моделлю (без API): python test_flow.py"""
import tempfile
from pathlib import Path

import agents
import analyst
import pipeline

W = Path(tempfile.mkdtemp(prefix="labgen_test_")); (W / "inputs").mkdir()
(W / "inputs" / "metodychka.txt").write_text("Лабораторна 3. Лінійна регресія.", encoding="utf-8")
(W / "inputs" / "data.csv").write_text("x,y\n1,2\n2,4.1\n3,5.9\n", encoding="utf-8")

CODE = """```python
import os, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, pandas as pd
os.makedirs('output/figs', exist_ok=True)
d = pd.read_csv('inputs/data.csv'); print('mean y =', d.y.mean())
plt.plot(d.x, d.y); plt.savefig('output/figs/fig1.png')
```"""
calls = {"review": 0}

def fake_ask(system, user, max_tokens=4000):
    if system is analyst.ANALYST: return CODE
    return "Текст розділу.\n[РИС: fig1.png | Графік]" if "Хід" in user else "Текст розділу."

def fake_json(system, user):
    if system is agents.PLANNER:
        return {"title": "Регресія", "lab_number": "3", "subject": "ІАД",
                "sections": [{"name": "Мета", "goal": "g", "needs": "n"}, {"name": "Хід роботи", "goal": "g", "needs": "n"}]}
    calls["review"] += 1
    return {"ok": calls["review"] > 1, "issues": ["додай цифри"]}

agents.ask, agents.ask_json = fake_ask, fake_json
res = pipeline.generate(W)
print(res["docx"], res["docx"].exists(), "reviews:", len(res["reviews"]), "figs:", res["analysis"]["figures"])
assert res["docx"].exists() and len(res["reviews"]) == 2
