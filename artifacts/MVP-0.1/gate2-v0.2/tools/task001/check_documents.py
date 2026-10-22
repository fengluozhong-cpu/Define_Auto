"""Check current Task 001 documentation structure and in-project links only."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        parser.error("simple run-id required")
    root = Path(__file__).resolve().parents[2]
    out = root / "artifacts/TASK-001" / args.run_id
    out.mkdir(exist_ok=False)
    files = [root / p for p in ["AGENTS.md", "GOALS.md", "REQUIREMENTS.md", "ARCHITECTURE.md", "PLANS.md", "README.md", "docs/tasks/TASK-001.md"]] + list((root / "docs/contracts").glob("*.md"))
    checks = []
    for p in files:
        text = p.read_text("utf-8-sig")
        checks.append({"check": "fences", "path": str(p.relative_to(root)), "result": "passed" if len(re.findall(r"^```", text, flags=re.M)) % 2 == 0 else "failed"})
        for label, href in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
            href = unquote(href.strip("<>")); parsed = urlsplit(href)
            if parsed.scheme and not re.match(r"^[A-Za-z]:[/\\]", href):
                continue
            path_text = href.split("#")[0]
            if not path_text:
                continue
            target = (p.parent / path_text).resolve()
            if target.is_relative_to(root):
                checks.append({"check": "local_link", "path": str(p.relative_to(root)), "target": str(target.relative_to(root)), "result": "passed" if target.exists() else "failed"})
        for line in text.splitlines():
            if line.startswith("|"):
                checks.append({"check": "table_row_end", "path": str(p.relative_to(root)), "result": "passed" if line.endswith("|") else "failed"})
    failures = [c for c in checks if c["result"] != "passed"]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = {"result": "passed" if checks and not failures else "failed", "performed_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
              "command": sys.argv, "scope": "UTF-8 decode, paired fences, in-project link target existence, table row endings only. No external page/anchor/semantic validation.",
              "script_sha256": sha(Path(__file__)), "files": [{"path": str(p.relative_to(root)).replace("\\", "/"), "sha256": sha(p)} for p in files],
              "check_count": len(checks), "failed_count": len(failures), "skipped_checks": 0, "checks": checks}
    (out / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "checks": len(checks), "failures": failures}, ensure_ascii=False))
    return 0 if result["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
