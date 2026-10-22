"""Full production-path suite with mandatory-case and collection guards."""
import argparse
import datetime as dt
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from define_auto.common import load, sha, write

# Mandatory regression registration: discovery cannot silently define its own bar.
RUNTIME_TESTS = ["tests.test_boundaries.RuntimeBoundaryTests." + name for name in [
    "test_cli_contract_errors", "test_cli_decision_history", "test_cli_recovery_and_no_overwrite", "test_html_and_markdown_escape",
    "test_manifest_failures", "test_model_review_regressions", "test_persisted_model_integrity",
    "test_provenance_wrong_target_and_pointer", "test_raw_label_and_privacy",
    "test_report_field_provenance_and_length", "test_stability_and_reordered_input"]]
RUNTIME_TESTS += ["tests.test_review_runtime.ReviewRuntimeTests." + name for name in [
    "test_unavailable_rule_is_not_pass", "test_manual_return_routes_and_blocks_selection",
    "test_rule_label_versions_and_invalid_values", "test_persisted_policy_and_review_history_constraints",
    "test_review_time_and_supersedes"]]


def clause_cases(requirement):
    c = lambda *n: [f"T001-C{i:02}" for i in n]
    a = lambda *n: [f"M01-A{i:02}" for i in n]
    rc = lambda start, end: [f"M01-RC{i:02}" for i in range(start, end + 1)]
    runtime = lambda *names: ["tests.test_boundaries.RuntimeBoundaryTests.test_" + n for n in names]
    return {
        "FR-001": c(1, 2, 3) + rc(12, 24) + runtime("manifest_failures", "provenance_wrong_target_and_pointer"),
        "FR-002": c(1, 4, 5, 6, 7, 8, 9, 10, 11) + a(1, 2, 3, 4, 5, 6, 7, 8, 20, 21) + rc(1, 28),
        "FR-003": c(2, 5, 8, 9, 10, 11, 12) + a(9, 10, 11, 12, 13, 14),
        "FR-005": c(23),
        "FR-006": c(1, 2, 3, 5, 8, 9, 10, 11, 12, 24) + a(9, 10, 11, 12, 13, 14, 15),
        "FR-007": c(23, 24) + a(15) + runtime("persisted_model_integrity"),
        "FR-008": c(2, 3, 4, 5, 6, 7),
        "FR-014": a(15, 21) + runtime("model_review_regressions", "persisted_model_integrity", "cli_recovery_and_no_overwrite"),
        "FR-015": c(13, 14, 15, 16, 17, 18, 19, 20, 21, 22) + a(16, 17, 18, 19) + rc(29, 32) + runtime("cli_decision_history"),
        "FR-018": c(14, 15, 16, 17, 18, 19, 20, 21) + a(19) + rc(29, 32) + runtime("stability_and_reordered_input", "cli_decision_history"),
        "NFR-001": c(13, 21, 24) + a(18, 19) + rc(32, 32) + runtime("stability_and_reordered_input", "cli_decision_history"),
        "NFR-002": c(1) + runtime("raw_label_and_privacy"),
        "NFR-003": runtime("report_field_provenance_and_length", "html_and_markdown_escape", "cli_recovery_and_no_overwrite"),
        "NFR-004": c(3, 22) + a(2, 3, 9, 10, 11, 14, 15, 16, 17, 21) + rc(12, 28) + runtime("manifest_failures", "persisted_model_integrity", "cli_recovery_and_no_overwrite"),
        "NFR-005": c(23) + runtime("cli_recovery_and_no_overwrite"),
        "NFR-006": c(23),
        "NFR-007": runtime("cli_recovery_and_no_overwrite")
    }.get(requirement, [])


def flatten(suite):
    result = []
    for test in suite:
        result.extend(flatten(test) if isinstance(test, unittest.TestSuite) else [test])
    return result


def case_id(test):
    method = test.id().split(".")[-1]
    if method.startswith("test_T001_C"):
        return "T001-C" + method[-2:]
    if method.startswith("test_M01_A"):
        return "M01-A" + method[-2:]
    if method.startswith("test_M01_RC"):
        return "M01-RC" + method[-2:]
    if method.startswith("test_M01_RP"):
        return "M01-RP" + method[-2:]
    return test.id()


def guard(expected, collected, executed, *, failures=0, errors=0, skipped=0):
    missing = sorted(set(expected) - set(collected))
    not_run = sorted(set(collected) - set(executed))
    duplicates = len(collected) != len(set(collected))
    passed = bool(collected) and not (missing or not_run or duplicates or failures or errors or skipped)
    return {"result": "passed" if passed else "failed", "missing": missing, "not_run": not_run,
            "duplicate_cases": duplicates, "failed": failures, "errors": errors, "skipped": skipped,
            "collected": len(collected), "executed": len(executed)}


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}

    def startTest(self, test):
        super().startTest(test)
        self.records[test.id()] = {"case_id": case_id(test), "test_id": test.id(), "result": "running", "subcases": []}

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.records[test.id()]["result"] == "running":
            self.records[test.id()]["result"] = "passed"

    def addFailure(self, test, err):
        super().addFailure(test, err); self.records[test.id()]["result"] = "failed"

    def addError(self, test, err):
        super().addError(test, err); self.records[test.id()]["result"] = "failed"

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self.records[test.id()]["result"] = "not_run"

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        self.records[test.id()]["subcases"].append({"id": str(subtest), "result": "failed" if err else "passed"})
        if err:
            self.records[test.id()]["result"] = "failed"

    def stopTest(self, test):
        if self.records[test.id()]["result"] == "running":
            self.records[test.id()]["result"] = "passed"
        super().stopTest(test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--probe", choices=["missing", "zero", "skipped", "error"], help="Guard fault injection only; never a real suite pass")
    args = parser.parse_args()
    if not args.run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_id):
        parser.error("run-id must be a simple unique directory name")
    out = ROOT / "artifacts/MVP-0.1" / args.run_id
    if out.exists():
        parser.error("run-id already exists")
    out.mkdir(parents=True, exist_ok=False)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    if args.probe:
        g = guard(["required"], [] if args.probe in {"missing", "zero"} else ["required"],
                  [] if args.probe in {"missing", "zero"} else ["required"],
                  skipped=int(args.probe == "skipped"), errors=int(args.probe == "error"))
        write(out / "checks.json", {"scope": "guard_fault_injection_not_real_suite", **g})
        print(json.dumps(g)); return 1 if g["result"] == "failed" else 0
    package = ROOT / "artifacts/TASK-001/gate1-v0.1"
    expected = [c["id"] for c in load(package / "expectations/task001/v0.1/expected.json")["cases"]]
    expected += [f"M01-A{i:02}" for i in range(1, 22)]
    expected += [c["case_id"] for c in load(ROOT / "expectations/mvp01/v0.2/read-context-cases.json")["cases"]]
    expected += [c["case_id"] for c in load(ROOT / "expectations/mvp01/v0.3/review-policy-cases.json")["cases"]]
    expected += RUNTIME_TESTS
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT))
    collected = [case_id(t) for t in flatten(suite)]
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=RecordingResult).run(suite)
    (out / "unittest-output.txt").write_text(output.getvalue(), encoding="utf-8")
    executed = [r["case_id"] for r in result.records.values()]
    g = guard(expected, collected, executed, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    if any(r["result"] != "passed" for r in result.records.values()): g["result"] = "failed"
    write(out / "checks.json", {"scope": "full_engine_suite", **g, "expected_ids": expected, "collected_ids": collected, "executed_ids": executed})
    from tests.test_baseline import ACTUAL as BASE_ACTUAL
    from tests.test_boundaries import ACTUAL as ADDITIONAL_ACTUAL
    from tests.test_review_policy import ACTUAL as POLICY_ACTUAL
    write(out / "case-results.json", {"cases": list(result.records.values()), "actual_baseline": BASE_ACTUAL,
           "actual_additional": ADDITIONAL_ACTUAL, "actual_review_policy": POLICY_ACTUAL,
           "historical_pending_cases": {"M01-A22": "superseded_by_RC01_RC06", "M01-A23": "superseded_by_RC07_RC11"}})
    original_coverage = load(package / "expectations/task001/v0.1/coverage.json")["rows"]
    # Explicit clause carry-over; an engine test pass does not cover future generators.
    rows = []
    for row in original_coverage:
        policy_cases = [c["case_id"] for c in load(ROOT / "expectations/mvp01/v0.3/review-policy-cases.json")["cases"]
                        if row["requirement"] in c["requirements"]]
        if row["requirement"] == "FR-011":
            policy_cases = ["M01-RP11", "M01-RP12"]
        applicable = bool(policy_cases) or "MVP 0.1" in row["deferred_to"] or row["requirement"] in {"NFR-003", "NFR-007", "FR-014"}
        linked = clause_cases(row["requirement"]) if applicable else []
        linked += policy_cases
        linked = sorted(set(linked))
        results_by_case = {r["case_id"]: r["result"] for r in result.records.values()}
        mapped_results = {cid: results_by_case.get(cid, "not_run") for cid in linked}
        rows.append({"requirement": row["requirement"], "clause": row["clause"], "current_scope": row["current_scope"],
            "current_task_applicable": applicable, "case_ids": linked,
            "coverage_status": "partial" if applicable else row["coverage_status"],
            "execution_result": ("passed" if mapped_results and all(v == "passed" for v in mapped_results.values()) else "not_run") if applicable else "not_run",
            "case_results": mapped_results, "evidence": "case-results.json" if applicable else None,
            "expected_sources": ["artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/expected.json",
                "expectations/mvp01/v0.1/additional-cases.json", "expectations/mvp01/v0.2/read-context-cases.json",
                "expectations/mvp01/v0.3/review-policy-cases.json",
                "docs/tasks/mvp01-review/implementation-review-round1.md", "docs/tasks/mvp01-review/final-review.md"],
            "uncovered_long_term": row["uncovered"], "receiving_stage": row["deferred_to"],
            "scope_note": "Current MVP clauses only; cumulative long-term requirement is not declared fully covered."})
        if policy_cases:
            rows[-1]["new_policy_scope"] = {"FR-005": "Explicit locked local type/flag/label rules and unselected-version gap; no complete Standard Provider or CT validation.",
                "FR-008": "Dataset/variable automatic flag, authorized reason, invalidation and future XML Comment mapping; no VLM or XML generation.",
                "FR-011": "Structured future Comment target and retained confirmed reason only (RP11/RP12); actual XML generation/XSD/P21 remain not_run in MVP0.3.",
                "FR-015": "Authorized reason, upstream-return and human-confirmed reuse; immutable history and isolation.",
                "FR-018": "Input/dependency changes, current eligibility and mandatory downstream rerun."}.get(row["requirement"], "CARD-01..06 applicable clause; see independently fixed RP cases.")
    write(out / "coverage.json", {"rows": rows, "current_required_cases": expected,
           "gate2": "pending_independent_review_and_chris", "coverage_and_pass_are_separate": True})
    inputs = sorted(set([*ROOT.glob("define_auto/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("tools/mvp01/*.py"),
                         ROOT / "expectations/mvp01/v0.1/additional-cases.json", ROOT / "expectations/mvp01/v0.2/read-context-cases.json",
                         ROOT / "expectations/mvp01/v0.3/review-policy-cases.json",
                         package / "manifest.json", package / "expectations/task001/v0.1/expected.json"]))
    write(out / "inputs-manifest.json", {"files": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p.read_bytes())} for p in inputs],
          "fixture_provenance": ["fixtures/mvp01/v0.1/manifest.json", "fixtures/mvp01/baseline-context-v0.1/manifest.json"],
          "frozen_inputs": "artifacts/TASK-001/gate1-v0.1/manifest.json"})
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True) if shutil.which("git") else None
    write(out / "run.json", {"command": sys.argv, "started_at": started, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
          "python": sys.version, "platform": platform.platform(), "head": git.stdout.strip() if git and git.returncode == 0 else "unavailable_in_source_bundle",
          "result": g["result"], "tests_run": result.testsRun, "exit_code": 0 if g["result"] == "passed" else 1, "gate2": "not_approved"})
    write(out / "outputs-manifest.json", {"files": [{"path": p.name, "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size} for p in sorted(out.iterdir())], "excludes_self": True})
    print(json.dumps({"out": str(out), **g})); return 0 if g["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
