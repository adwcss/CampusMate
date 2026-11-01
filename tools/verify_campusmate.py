"""Run the actual regression commands and save a reproducible report."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
commands = [[sys.executable, "-X", "utf8", "-I", "-S", "tools/verify.py"],
            [sys.executable, "-X", "utf8", "-I", "-S", "tools/verify_multi.py"],
            ["node", "--test", "tools/verify_appearance_state.mjs"],
            [sys.executable, "-X", "utf8", "-I", "-S", "tools/evaluate_retrieval.py", "--output", "docs/evaluation-campusmate.json"]]
rows = []
for command in commands:
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    output = result.stdout + result.stderr
    matches = re.findall(r"Ran (\d+) tests|(?:ℹ|#) tests (\d+)", output)
    count = int(next(value for value in matches[-1] if value)) if matches else None
    rows.append({"command": command[1:] if command[0] == sys.executable else command, "returncode": result.returncode,
                 "tests": count, "elapsed_seconds": round(time.monotonic()-started, 3), "output": output})
    print(command[-1], "PASS" if result.returncode == 0 else "FAIL", count if count is not None else "")
report = {"verified_at": datetime.now(timezone.utc).isoformat(), "all_passed": all(row["returncode"] == 0 for row in rows),
          "automated_tests": sum(row["tests"] or 0 for row in rows), "real_paid_search_calls": 0, "real_paid_llm_calls": 0,
          "scope": "Local HTTP and unit regressions; search/LLM upstream protocols mocked. Not a live provider quality evaluation.", "runs": rows}
(ROOT / "docs/campusmate-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if report["all_passed"] else 1)
