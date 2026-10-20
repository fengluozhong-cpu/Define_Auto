"""Freeze and independently re-read an immutable review package; never approve it."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-id", required=True)
    args = parser.parse_args()
    if not args.package_id.startswith("gate1-") or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_" for c in args.package_id):
        parser.error("Use a new simple gate1-* identifier")
    root = Path(__file__).resolve().parents[2]
    out = root / "artifacts/TASK-001" / args.package_id
    submission = out.parent / (args.package_id + "-submission.json")
    if out.exists() or submission.exists():
        parser.error("Refusing to overwrite a frozen package or submission record")
    review = root / "docs/tasks/task001-review/final-review.json"
    if not review.is_file():
        parser.error("Independent final review evidence must exist first")
    report = json.loads(review.read_text("utf-8-sig"))
    if report.get("technical_result") != "passed" or report.get("open_technical_blockers") != []:
        parser.error("Independent technical review has not passed")
    for run_id in ["materials-04", "rebuild-01", "documents-02"]:
        result = json.loads((root / f"artifacts/TASK-001/{run_id}/checks.json").read_text("utf-8"))
        if result.get("result") != "passed":
            parser.error(f"Required evidence failed: {run_id}")
    files = {root / p for p in ["AGENTS.md", "GOALS.md", "REQUIREMENTS.md", "ARCHITECTURE.md", "PLANS.md", "README.md", ".gitignore", "docs/tasks/TASK-001.md", "docs/tasks/TASK-001-findings.json"]}
    folders = ["docs/contracts", "docs/tasks/task001-review", "fixtures/task001/v0.1", "expectations/task001/v0.1", "tools/task001",
               "baselines/BL-20261020-01", "docs/approvals", "artifacts/TASK-001/start", "artifacts/TASK-001/references",
               "artifacts/TASK-001/materials-01", "artifacts/TASK-001/materials-02", "artifacts/TASK-001/materials-03", "artifacts/TASK-001/materials-04", "artifacts/TASK-001/rebuild-01", "artifacts/TASK-001/documents-01", "artifacts/TASK-001/documents-02"]
    for folder in folders:
        files.update(p for p in (root / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    out.mkdir()
    entries = []
    for path in sorted(files):
        relative = path.relative_to(root)
        dest = out / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        category = ("independent_expected" if relative.parts[0] == "expectations" else
                    "fixed_input" if relative.parts[0] == "fixtures" else
                    "tool_source" if relative.parts[0] == "tools" else
                    "execution_or_reference_evidence" if relative.parts[0] == "artifacts" else
                    "approved_baseline_dependency" if relative.parts[0] == "baselines" else
                    "review_or_contract_document")
        entries.append({"path": relative.as_posix(), "role": category, "bytes": path.stat().st_size, "sha256": sha(path)})
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
    manifest = {"package_id": args.package_id, "task_id": "TASK-001", "version": "0.1", "created_at": now,
                "baseline": "BL-20261020-01", "purpose": "GATE-1 review only", "delivery_state": "review_ready",
                "business_confirmation": "pending_chris", "gate1": "pending_chris", "approved": False,
                "excludes": ["manifest itself", "post-freeze submission/approval", "venv", "work", "private discussion and knowledge base"],
                "reference_resolution": "Resolve project paths against this package root, not the mutable workspace; BL references use its own nested snapshot. Private/historical/external references are not implementation dependencies.",
                "files": entries}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Verify from copied bytes, not from source paths or copy return codes.
    verified = [{"path": row["path"], "result": "passed" if sha(out / row["path"]) == row["sha256"] and (out / row["path"]).stat().st_size == row["bytes"] else "failed"} for row in entries]
    passed = bool(verified) and all(row["result"] == "passed" for row in verified)
    record = {"package_id": args.package_id, "manifest_sha256": sha(out / "manifest.json"), "checked_at": now,
              "check_id": "Q06", "result": "passed" if passed else "failed", "files_verified": len(verified), "file_results": verified,
              "excluded_from_frozen_package": True, "gate1": "pending_chris", "approved": False,
              "Q07": {"result": "not_run", "decision_owner": "Chris", "blocking": True},
              "restore": "Read manifest, copy listed files to a new independent folder maintaining relative paths, then verify every size and SHA-256. Never overwrite the current workspace or original package."}
    submission.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"package": str(out), "submission": str(submission), "Q06": record["result"], "files_verified": len(verified), "manifest_sha256": record["manifest_sha256"], "gate1": "pending_chris"}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
