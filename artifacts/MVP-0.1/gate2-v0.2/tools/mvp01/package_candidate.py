"""Freeze an explicit candidate whitelist; never overwrite an existing package."""
import argparse
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from define_auto.common import load, require, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    args = parser.parse_args()
    require(re.fullmatch(r"gate2-v[0-9]+\.[0-9]+", args.package_id), "invalid_package_id")
    destination = ROOT / "artifacts/MVP-0.1" / args.package_id
    require(not destination.exists(), "package_exists")
    old = ROOT / "artifacts/MVP-0.1/gate2-v0.1/manifest.json"
    require(sha(old.read_bytes()) == "825443dd56bd950f417d33a1922e98f283dabe4c297b0fe8a1e9fe5f109f206d", "old_candidate_manifest_changed")
    old_entries = {f["path"]: f for f in load(old)["files"]}
    files = {ROOT / relative for relative in old_entries if relative != "gate2-evaluation.json"}
    files.add(old)
    for pattern in ["define_auto/*.py", "tests/*.py", "tools/mvp01/*.py", "docs/tasks/mvp01-review/*.md",
                    "docs/contracts/MVP-0.1*.md", "expectations/mvp01/v0.3/*.json", "fixtures/mvp01/review-policy-v0.1/*"]:
        files.update(ROOT.glob(pattern))
    for identifier in args.evidence:
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", identifier), "invalid_evidence_id")
        folder = ROOT / "artifacts/MVP-0.1" / identifier
        require(folder.is_dir() and not identifier.startswith("gate2-"), "invalid_evidence_directory")
        files.update(p for p in folder.rglob("*") if p.is_file())
    # Validate every path before any write; the inherited whitelist contains no
    # arbitrary workspace data, venvs, Git directory, or work/ scratch files.
    for path in files:
        source = path if path.is_file() else old.parent / path.relative_to(ROOT)
        require(source.is_file() and source.resolve().is_relative_to(ROOT.resolve()), "package_source_missing_or_unsafe", str(path.relative_to(ROOT)))
        if source != path:
            require(sha(source.read_bytes()) == old_entries[path.relative_to(ROOT).as_posix()]["sha256"], "historical_evidence_hash_mismatch")
        require(not any(p in {".git", "work", "__pycache__"} for p in path.relative_to(ROOT).parts), "unsafe_package_source")
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        source = path if path.is_file() else old.parent / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(source.read_bytes()) == sha(target.read_bytes()), "package_copy_mismatch")
        entries.append({"path": relative.as_posix(), "bytes": target.stat().st_size, "sha256": sha(target.read_bytes())})
    evaluation = destination / "gate2-evaluation.json"
    write(evaluation, {"candidate": args.package_id, "gate2": "pending_chris", "task_status": "verification_complete",
        "technical_evidence": "artifacts/MVP-0.1/independent-policy-full-20261022-03/checks.json",
        "independent_review": "docs/tasks/mvp01-review/review-policy-implementation-review.md",
        "M01-Q01_to_Q06": "passed_current_scope", "M01-Q07": "not_run", "business_approval": "not_granted",
        "standards_conformance": "not_assessed", "actual_xml_p21": "not_run", "recovery_checks": "see_external_receipt"})
    entries.append({"path": evaluation.name, "bytes": evaluation.stat().st_size, "sha256": sha(evaluation.read_bytes())})
    write(destination / "manifest.json", {"package_id": "MVP-0.1-" + args.package_id,
        "status": "review_ready_not_approved", "scope": "CARD01-06 revision; explicit source/input/evidence whitelist, not whole repository backup",
        "files": entries})
    write(destination.parent / (args.package_id + "-receipt.json"), {"package_id": args.package_id,
        "manifest_sha256": sha((destination / "manifest.json").read_bytes()), "files": len(entries),
        "gate2": "pending_chris", "recovery_checks": "not_run"})
    print(str(destination))


if __name__ == "__main__":
    main()
