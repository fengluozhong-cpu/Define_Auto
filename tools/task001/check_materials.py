"""Audit fixed Task 001 materials, not reconciliation behavior or patch application.

Expected facts are hand-authored. This module never compares Spec with XPT.
Every new run writes a new directory, preserving failed/older evidence.
"""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import struct
import sys

import pandas as pd
import pyreadstat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text("utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        parser.error("run-id must be a simple directory name")
    root = Path(__file__).resolve().parents[2]
    fixture = root / "fixtures/task001/v0.1"
    expected_path = root / "expectations/task001/v0.1/expected.json"
    out = root / "artifacts/TASK-001" / args.run_id
    out.mkdir(exist_ok=False)
    started = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
    checks = []
    selected_case_ids = []

    def check(cid, actual, expected, detail=None):
        checks.append({"check_id": cid, "actual": actual, "expected": expected,
                       "result": "passed" if actual == expected else "failed", "detail": detail})

    def audit():
        expected = load(expected_path)
        baseline = root / "baselines/BL-20261020-01/manifest.json"
        check("Q01.manifest_hash", sha(baseline), "55b68829f17a489060281174c901a9de6fd2f5902831ed3b7aa717696e5e802c")
        for f in load(baseline)["files"]:
            p = baseline.parent / f["path"]
            check("Q01.baseline." + f["path"], [sha(p), p.stat().st_size], [f["sha256"], f["bytes"]])
        for f in load(root / "artifacts/TASK-001/start/dependencies.json")["protected_files"]:
            check("Q01.protected." + f["path"], sha(root / f["path"]), f["sha256"])
        manifest = load(fixture / "input-manifest.json")
        check("Q02.source_ids_unique", len({s["source_id"] for s in manifest["sources"]}), 5)
        for s in manifest["sources"]:
            p = (fixture / s["relative_path"]).resolve()
            check("Q02.root_containment." + s["source_id"], p.is_relative_to(fixture.resolve()), True)
            check("Q02.exists." + s["source_id"], p.is_file(), s["provision_status"] == "provided")
            check("Q02.hash." + s["source_id"], sha(p) if p.is_file() else None, s["sha256"])
        check("Q02.AE_absent", (fixture / "ae.xpt").exists(), False)
        try:
            pyreadstat.read_xport(str(fixture / "cm.xpt"))
        except pyreadstat.ReadstatError as exc:
            check("Q02.CM_unreadable", True, True, {"exception_type": type(exc).__name__, "message": str(exc)})
        else:
            check("Q02.CM_unreadable", False, True)
        for name, facts in expected["facts"].items():
            path = fixture / (name.lower() + ".xpt")
            df, meta = pyreadstat.read_xport(str(path))
            actual = {"row_count": len(df), "label": meta.file_label, "column_names": meta.column_names,
                      "storage_widths": meta.variable_storage_width, "types": meta.readstat_variable_types,
                      "labels": meta.column_names_to_labels}
            missing_counts = {}
            distinct_counts = {}
            max_lengths = {}
            for col in df.columns:
                if meta.readstat_variable_types[col] == "string":
                    values = [str(v).strip(" ") for v in df[col]]
                    nonmissing = [v for v in values if v != ""]
                    max_lengths[col] = max((len(v.encode("ascii")) for v in nonmissing), default=0)
                else:
                    nonmissing = [float(v) for v in df[col] if not pd.isna(v)]
                missing_counts[col] = len(df) - len(nonmissing)
                distinct_counts[col] = len(set(nonmissing))
            actual.update(missing_counts=missing_counts, nonmissing_distinct_counts=distinct_counts,
                          observed_max_content_lengths=max_lengths)
            for key, value in facts.items():
                if key != "numeric_missing_code_counts":
                    check("Q02.library." + name + "." + key, actual.get(key), value)
            # Independent fixed-fixture byte audit per SAS vendor paper pp. 5-7.
            raw = path.read_bytes()
            check("Q02.raw." + name + ".80byte_records", len(raw) % 80, 0)
            count = int(raw[560 + 54:560 + 58])
            descriptors = []
            for i in range(count):
                record = raw[640 + i * 140:640 + (i + 1) * 140]
                typ, _, width, _ = struct.unpack(">hhhh", record[:8])
                cname = record[8:16].decode("ascii").rstrip(" ")
                descriptors.append({"name": cname, "width": width, "type": "string" if typ == 2 else "double",
                                    "label": record[16:56].decode("ascii").rstrip(" "),
                                    "position": struct.unpack(">i", record[84:88])[0]})
            check("Q02.raw." + name + ".names", [d["name"] for d in descriptors], facts["column_names"])
            for field, fact in [("width", "storage_widths"), ("type", "types"), ("label", "labels")]:
                check("Q02.raw." + name + "." + field, {d["name"]: d[field] for d in descriptors}, facts[fact])
            data_start = 640 + ((count * 140 + 79) // 80) * 80 + 80
            stride = sum(d["width"] for d in descriptors)
            data_bytes = raw[data_start:].rstrip(b" ")
            # These two fixtures have no trailing blank-valued final observation.
            check("Q02.raw." + name + ".data_bytes", len(data_bytes), facts["row_count"] * stride)
            if name == "DM":
                age = next(d for d in descriptors if d["name"] == "AGE")
                codes = {}
                for i in range(3):
                    offset = data_start + i * stride + age["position"]
                    cell = raw[offset:offset + age["width"]]
                    check("Q02.raw.DM.AGE.zero_tail." + str(i), cell[1:].hex(), "00" * 7)
                    code = chr(cell[0]); codes[code] = codes.get(code, 0) + 1
                check("Q02.raw.DM.AGE.missing_codes", codes, facts["numeric_missing_code_counts"]["AGE"])
        spec = load(fixture / "spec.json")
        check("Q02.spec.datasets", [d["name"] for d in spec["datasets"]], ["DM", "VS", "AE", "CM"])
        check("Q02.spec.unique_datasets", len({d["name"] for d in spec["datasets"]}), len(spec["datasets"]))
        for dataset in spec["datasets"]:
            names = [v["name"] for v in dataset["variables"]]
            check("Q02.spec.unique_variables." + dataset["name"], len(names), len(set(names)))
            check("Q02.spec.minimum_fields." + dataset["name"], all(set(["name", "label", "type", "declared_length"]) <= set(v) for v in dataset["variables"]), True)
        cases = expected["cases"]
        selected_case_ids.extend(c["id"] for c in cases)
        check("Q03.case_count", len(cases), 24)
        check("Q03.unique_cases", len({c["id"] for c in cases}), 24)
        check("Q03.derivations_present", all(c.get("source") and c.get("derivation") and c.get("expected") for c in cases), True)
        changes = load(fixture / "dependency-changes.json")["changes"]
        check("Q03.dependency_variants", [c["component"] for c in changes], ["inputs", "standards", "rules", "config", "model_schema", "upstream_decisions", "tools", "audit"])
        check("Q03.patch_synthetic", load(fixture / "patch.json")["authorization_status"], "synthetic_only")
        coverage = load(root / "expectations/task001/v0.1/coverage.json")["rows"]
        required_ids = ([f"FR-{i:03d}" for i in range(1, 19)] + [f"NFR-{i:03d}" for i in range(1, 8)] + [f"AC-{i:02d}" for i in range(1, 12)])
        check("Q04.requirements_registered", sorted(row["requirement"] for row in coverage), sorted(required_ids))
        check("Q04.case_refs_exist", all(set(row["case_ids"]) <= set(selected_case_ids) for row in coverage), True)
        check("Q04.unimplemented_behaviors_not_run", all(row["engine_behavior_result"] == "not_run" for row in coverage), True)
        gates = load(root / "expectations/task001/v0.1/gate1-checklist.json")["checks"]
        check("Q04.gates_registered", [row["check_id"] for row in gates], [f"Q0{i}" for i in range(1, 8)])
        check("Q04.gates_required", all(row["required"] for row in gates), True)
        check("Q04.business_not_approved", expected["business_confirmation"]["status"], "pending")
        save(out / "coverage.json", {"scope": "material audit only; independent technical review recorded separately",
             "rows": [{"requirement": row["requirement"], "clause": row["clause"], "case_ids": row["case_ids"],
                       "independent_expected": row["expected_path"], "coverage_status": row["coverage_status"],
                       "actual_material_evidence": f"artifacts/TASK-001/{args.run_id}/checks.json",
                       "material_result": "passed" if checks and all(c["result"] == "passed" for c in checks) else "failed",
                       "engine_evidence": None, "engine_result": "not_run", "deferred_to": row["deferred_to"]} for row in coverage]})
        for source in load(root / "artifacts/TASK-001/references/sources.json")["assets"]:
            check("Q06.source." + source["path"], sha(root / "artifacts/TASK-001/references" / source["path"]), source["sha256"])
        paths = [s["path"] for s in load(root / "artifacts/TASK-001/references/sources.json")["assets"]]
        check("Q06.unique_source_paths", len(set(paths)), len(paths))
        save(out / "case-readiness.json", {"expected_sha256": sha(expected_path), "cases": [
            {"case_id": c["id"], "requirements": c["requirements"], "independent_expected": "expectations/task001/v0.1/expected.json#/cases/" + str(i),
             "material_registration_status": "registered", "independent_manual_review": "see docs/tasks/task001-review/",
             "engine_behavior_result": "not_run", "engine_evidence": None} for i, c in enumerate(cases)],
             "scope": "material readiness fields only; engine behavior not tested"})

    try:
        audit()
    except Exception as exc:
        checks.append({"check_id": "EXECUTION", "result": "failed", "exception_type": type(exc).__name__, "message": str(exc)})
    failed = [c for c in checks if c["result"] != "passed"]
    result = "passed" if checks and not failed else "failed"
    save(out / "checks.json", {"result": result, "check_count": len(checks), "failed_count": len(failed),
                               "checks": checks, "engine_behavior": "not_run", "gate1": "pending_chris"})
    save(out / "run.json", {"task_id": "TASK-001", "run_id": args.run_id, "command": sys.argv,
                            "started_at": started, "finished_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
                            "python": sys.version, "platform": platform.platform(), "packages": {n: importlib.metadata.version(n) for n in ["pandas", "pyreadstat", "numpy", "narwhals"]},
                            "script_sha256": sha(Path(__file__)), "fixture_manifest_sha256": sha(fixture / "input-manifest.json"),
                            "expected_sha256": sha(expected_path), "contract_sha256": sha(root / "docs/contracts/TASK-001-contract-v0.1.md"),
                            "collected_checks": len(checks), "executed_checks": len(checks), "skipped_checks": 0,
                            "selected_case_ids": selected_case_ids, "case_count": len(selected_case_ids),
                            "engine_cases_executed": 0, "result": result, "exit_code": 0 if result == "passed" else 1})
    input_paths = list(fixture.glob("*")) + list((root / "expectations/task001/v0.1").glob("*.json")) + list((root / "docs/contracts").glob("*.md")) + [Path(__file__), root / "tools/task001/requirements-fixtures.lock.txt", root / "artifacts/TASK-001/references/sources.json"]
    save(out / "inputs-manifest.json", {"files": [{"path": str(p.relative_to(root)).replace("\\", "/"), "sha256": sha(p)} for p in input_paths if p.is_file()]})
    save(out / "outputs-manifest.json", {"files": [{"path": p.name, "sha256": sha(p)} for p in out.glob("*.json") if p.name != "outputs-manifest.json"], "excludes_self": True})
    print(json.dumps({"run": str(out), "result": result, "checks": len(checks), "failures": failed}, ensure_ascii=False))
    return 0 if result == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
