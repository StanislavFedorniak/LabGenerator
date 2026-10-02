"""Перевірка без виклику API: запуск коду аналітика + збирання Word з рисунком.
Запуск: python test_build.py"""
from pathlib import Path

import analyst
import docx_builder
from readers import read_file

ROOT = Path(__file__).parent
(ROOT / "output" / "figs").mkdir(parents=True, exist_ok=True)

csv = ROOT / "output" / "_sample.csv"
csv.write_text("x,y\n1,2.1\n2,3.9\n3,6.2\n4,7.8\n5,10.1\n", encoding="utf-8")

code = '''
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
os.makedirs("output/figs", exist_ok=True)
df = pd.read_csv("output/_sample.csv")
print("Середнє y:", df.y.mean())
plt.plot(df.x, df.y, "o-"); plt.xlabel("x"); plt.ylabel("y")
plt.savefig("output/figs/fig1.png", dpi=100, bbox_inches="tight")
'''
ok, out = analyst._run(code, ROOT)
print("аналіз:", ok, out.strip())
assert ok

plan = {"title": "Тест", "lab_number": "1", "subject": "Інтелектуальний аналіз даних"}
text = ("Дослідити залежність.\n- пункт 1\n```\nprint(1)\n```\n"
        "[РИС: fig1.png | Залежність y від x]")
out_docx = ROOT / "output" / "test.docx"
docx_builder.build(plan, {"Результати": text}, out_docx, figs_dir=ROOT / "output" / "figs")
print(read_file(out_docx)[-120:])
print("inline images:", len(__import__("docx").Document(out_docx).inline_shapes))
