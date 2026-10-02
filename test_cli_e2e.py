"""Наскрізний тест Claude Code-режиму на мінімальних даних (витрачає ліміт підписки).
python test_cli_e2e.py"""
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent
run = ROOT / "runs" / ("e2e_" + time.strftime("%H%M%S"))
(run / "inputs").mkdir(parents=True)
(run / "output" / "figs").mkdir(parents=True)
shutil.copytree(ROOT / ".claude" / "agents", run / ".claude" / "agents")
for n in ["build_docx.py", "docx_builder.py", "config.py"]:
    shutil.copy(ROOT / n, run / n)
(run / "inputs" / "metodychka.txt").write_text(
    "Лабораторна робота №1. Лінійна регресія.\nМета: побудувати лінійну регресію y=ax+b за даними data.csv, "
    "знайти коефіцієнти та R2, побудувати графік.\nЗвіт: мета, хід роботи, результати, висновки.\n", encoding="utf-8")
(run / "inputs" / "data.csv").write_text("x,y\n1,2.1\n2,3.9\n3,6.2\n4,7.8\n5,10.1\n6,12.2\n", encoding="utf-8")

body = (ROOT / ".claude" / "commands" / "lab-report.md").read_text(encoding="utf-8").split("---", 2)[-1]
prompt = body.replace("$ARGUMENTS", "(немає)")
allowed = ["Read", "Write", "Edit", "Glob", "Grep", "Task", "Agent", "Bash(python *)", "Bash(python3 *)"]
cmd = [shutil.which("claude"), "-p", "--output-format", "stream-json", "--verbose",
       "--permission-mode", "acceptEdits", "--allowedTools", *allowed]
p = subprocess.Popen(cmd, cwd=run, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, encoding="utf-8", errors="replace")
p.stdin.write(prompt); p.stdin.close()
for line in p.stdout:
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("type") == "assistant":
        for b in ev["message"]["content"]:
            if b.get("type") == "tool_use":
                print("TOOL:", b["name"], str(b["input"])[:90].encode("ascii", "replace").decode())
    elif ev.get("type") == "result":
        print("RESULT error:", ev.get("is_error"))
p.wait()
print("docx:", [str(f.name) for f in (run / "output").glob("*.docx")], "run dir:", run.name)
