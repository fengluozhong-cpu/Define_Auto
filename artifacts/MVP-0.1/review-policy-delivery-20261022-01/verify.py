"""Read-only delivery audit. Execute from any cwd with the same source tree."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
records = []
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def check(identifier, actual, expected):
    records.append(dict(check_id=identifier, actual=actual, expected=expected,
                        result="passed" if actual == expected else "failed"))


for relative, expected_hash, count in [
    ("artifacts/TASK-001/gate1-v0.1", "b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3", 82),
    ("artifacts/MVP-0.1/gate2-v0.1", "825443dd56bd950f417d33a1922e98f283dabe4c297b0fe8a1e9fe5f109f206d", 358)]:
    folder = ROOT / relative
    check(relative + "/manifest", digest(folder / "manifest.json"), expected_hash)
    if digest(folder / "manifest.json") != expected_hash:
        raise SystemExit("Frozen manifest changed; dependent audit blocked")
    items = json.loads((folder / "manifest.json").read_text("utf-8"))["files"]
    check(relative + "/count", len(items), count)
    for item in items:
        path = (folder / item["path"]).resolve()
        if not path.is_relative_to(folder.resolve()): raise SystemExit("Unsafe frozen path")
        check(relative + "/" + item["path"], [path.stat().st_size, digest(path)], [item["bytes"], item["sha256"]])
        if relative.startswith("artifacts/TASK") and item["path"].startswith(("fixtures/task001/", "expectations/task001/", "baselines/")):
            original = ROOT / item["path"]
            check("original/" + item["path"], digest(original), item["sha256"])

old = ROOT / "artifacts/MVP-0.1/gate2-v0.1"
for relative in ["AGENTS.md", "docs/agents/issue-tracker.md", "docs/agents/triage-labels.md", "docs/agents/domain.md",
                 "docs/tasks/MVP-0.1-skill-setup-draft.md", "docs/approvals/APR-20261020-01.md", "docs/approvals/APR-20261020-02.md"]:
    check("formal_config_or_approval/" + relative, digest(ROOT / relative), digest(old / relative))
check("independent_expectations", digest(ROOT / "expectations/mvp01/v0.3/review-policy-cases.json"),
      "0e36a52f457072f624f094ffd426e8a7357bcf9fb22df75c3299043fd418fdf0")
for identifier in ["review-policy-demo-20261022-02", "review-policy-confirm-20261022-02", "review-policy-rerun-20261022-02"]:
    folder = ROOT / "artifacts/MVP-0.1" / identifier
    for item in json.loads((folder / "outputs-manifest.json").read_text("utf-8"))["files"]:
        check(identifier + "/" + item["path"], digest(folder / item["path"]), item["sha256"])
check("complete_model_rerun_bytes", digest(ROOT / "artifacts/MVP-0.1/review-policy-confirm-20261022-02/model.json"),
      digest(ROOT / "artifacts/MVP-0.1/review-policy-rerun-20261022-02/model.json"))
for identifier in ["review-policy-suite-20261022-05"]:
    summary = json.loads((ROOT / "artifacts/MVP-0.1" / identifier / "checks.json").read_text("utf-8"))
    check(identifier, {k: summary[k] for k in ["result", "collected", "executed", "failed", "errors", "skipped", "missing", "not_run"]},
          dict(result="passed", collected=133, executed=133, failed=0, errors=0, skipped=0, missing=[], not_run=[]))
result = {"checks": records, "total": len(records), "failed": sum(r["result"] != "passed" for r in records)}
target = Path(__file__).with_name("checks.json")
if target.exists(): raise SystemExit("Audit output exists; copy this audit to a new run directory")
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in ["total", "failed"]}))
raise SystemExit(bool(result["failed"]))
