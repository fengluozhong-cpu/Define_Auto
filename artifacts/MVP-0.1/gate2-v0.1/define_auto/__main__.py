"""python -m define_auto --help"""
import argparse
import datetime as dt
import json
import platform
import sys
from pathlib import Path

from .common import ContractError, canonical, load, require, sha, write
from .decisions import apply_decision, resume_model
from .engine import reconcile
from .model import validate_model, dependency_digest
from .reporting import html_report, markdown


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local XPT + JSON Spec metadata reconciliation")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--read-context")
    parser.add_argument("--provenance", action="append", default=[], metavar="SOURCE_ID=PATH")
    parser.add_argument("--encoding", help="Explicit fallback codec when no declaration supplies one")
    parser.add_argument("--isolated-test", action="store_true", help="Accept test-only sources/decisions; never produce real approvals")
    parser.add_argument("--patch")
    parser.add_argument("--previous-dependency")
    parser.add_argument("--prior-model", help="Restore immutable history and conditionally reuse current selections")
    parser.add_argument("--authorization", help="Human-authored authorization JSON; authenticity belongs to delivery process")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    if out.exists():
        print(json.dumps({"result": "failed", "error": "output_exists"})); return 2
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    paths = [Path(args.manifest)]
    try:
        provenance = {}
        for value in args.provenance:
            require("=" in value, "invalid_provenance_argument")
            key, path = value.split("=", 1)
            require(key not in provenance, "duplicate_provenance_source")
            provenance[key] = path; paths.append(Path(path))
        if args.read_context:
            paths.append(Path(args.read_context))
        model = reconcile(args.manifest, context_path=args.read_context, provenance_paths=provenance,
                          test_mode=args.isolated_test, config={"encoding": args.encoding} if args.encoding else {})
        if args.prior_model:
            paths.append(Path(args.prior_model))
            prior_model = load(args.prior_model)
            validate_model(prior_model, sealed=True)
            model = resume_model(model, prior_model)
        patch_result = {"status": "not_provided", "business_changes": 0}
        if args.patch:
            require(args.previous_dependency and args.authorization, "patch_context_required")
            paths += [Path(args.patch), Path(args.previous_dependency), Path(args.authorization)]
            auth = load(args.authorization)
            require(isinstance(auth, dict), "invalid_authorization_record")
            auth_source = "AUTHORIZATION-" + sha(Path(args.authorization).read_bytes())
            auth = {**auth, "source_id": auth_source, "source_sha256": sha(Path(args.authorization).read_bytes())}
            if not any(s["source_id"] == auth_source for s in model["sources"]):
                model["sources"].append(dict(source_id=auth_source, relative_path=Path(args.authorization).name,
                sha256=auth["source_sha256"], version="sha256:" + auth["source_sha256"], source_type="authorization",
                acquired_at="recorded_in_run", confidentiality="local", completeness_scope={"scope": "human_decision"},
                    provision_status="provided", read_status="readable"))
            previous_dep = load(args.previous_dependency)
            require(isinstance(previous_dep, dict), "invalid_dependency_snapshot")
            require(previous_dep.get("dependency_snapshot_id") == dependency_digest(previous_dep), "dependency_snapshot_hash_mismatch")
            model, patch_result = apply_decision(model, load(args.patch), previous_dep, auth,
                                                 test_mode=args.isolated_test)
        require(not ((args.authorization or args.previous_dependency) and not args.patch), "unused_patch_arguments")
        validate_model(model, sealed=True)
        out.mkdir(parents=True, exist_ok=False)
        write(out / "model.json", model)
        write(out / "issues.json", model["issues"])
        write(out / "evidence.json", model["evidence"])
        write(out / "dependencies.json", model["dependency_snapshot"])
        write(out / "patch-applicability.json", patch_result)
        (out / "review.md").write_text(markdown(model), encoding="utf-8")
        (out / "review.html").write_text(html_report(model), encoding="utf-8")
        write(out / "inputs-manifest.json", {"files": [{"path": str(p.resolve()), "sha256": sha(p.read_bytes())} for p in paths],
             "sources": model["sources"], "source_content_recovery": "Source files remain read-only at manifest root; preserve them with the delivery."})
        write(out / "checks.json", {"checks": [{"check_id": "runtime_model_constraints", "result": "passed"}],
              "scope": "runtime construction only, not full regression suite", "gate2": "not_assessed"})
        write(out / "coverage.json", {"scope": "runtime only", "requirement_acceptance": "not_assessed",
              "full_suite_evidence": "Run tools/mvp01/run_checks.py separately."})
        write(out / "run.json", {"command": sys.argv if argv is None else argv, "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(), "python": sys.version, "platform": platform.platform(),
            "result": "completed_with_review_items", "exit_code": 0, "model_snapshot_id": model["model_snapshot_id"],
            "gate2": "pending_chris", "test_only": model["test_only"]})
        write(out / "outputs-manifest.json", {"files": [{"path": p.name, "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
              for p in sorted(out.iterdir())], "excludes_self": True})
        print(json.dumps({"out": str(out), "model": model["model_snapshot_id"], "issues": len(model["issues"]),
                          "gate2": "pending_chris"})); return 0
    except (ContractError, OSError, UnicodeError) as exc:
        error = exc.code if isinstance(exc, ContractError) else type(exc).__name__
        print(json.dumps({"result": "failed", "error": error})); return 1


if __name__ == "__main__":
    raise SystemExit(main())
