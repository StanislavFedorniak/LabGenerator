"""Збирає Word з markdown-чернетки. Викликається командою /lab-report (або вручну).

python build_docx.py plan.json report.md output/Lab_1.docx [figs_dir]

plan.json:  {"title": "...", "lab_number": "1", "subject": "...", "title_page": {"student": "...", ...}}
report.md:  розділи за заголовками "## Назва"; рисунки — рядком [РИС: fig1.png | Підпис]
"""
import json
import re
import sys
from pathlib import Path

import docx_builder


def parse_sections(md: str) -> dict:
    parts = re.split(r"^##\s+(.+)$", md, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sections = parse_sections(Path(sys.argv[2]).read_text(encoding="utf-8"))
    out = Path(sys.argv[3])
    out.parent.mkdir(parents=True, exist_ok=True)
    figs = sys.argv[4] if len(sys.argv) > 4 else "output/figs"
    docx_builder.build(plan, sections, out, plan.get("title_page"), figs)
    print(f"OK: {out} ({len(sections)} розділів)")
