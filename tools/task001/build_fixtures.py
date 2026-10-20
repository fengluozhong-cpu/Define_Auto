"""Make fixed synthetic XPT only. Never reads or writes independent expectations.

Use a NEW --out directory to rebuild. Existing files are never overwritten.
SAS transport layout: vendor paper pp. 3-7. This is not an input adapter/engine.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import pandas as pd
import pyreadstat


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    seed = root / "fixtures/task001/v0.1"
    out = Path(args.out).resolve()
    generated = ["dm.xpt", "vs.xpt", "cm.xpt", "spec-changed.json", "input-manifest.json", "dependencies.json", "build-record.json"]
    if any((out / name).exists() for name in generated):
        parser.error("Refusing to overwrite existing generated files; use a new --out directory")
    out.mkdir(parents=True, exist_ok=True)
    for name in ["source-data.json", "spec.json", "patch.json", "dependency-changes.json"]:
        if out != seed:
            shutil.copy2(seed / name, out / name)
    source = json.loads((out / "source-data.json").read_text("utf-8"))
    fixed_date = b"01JAN00:00:00:00"
    byte_edits = []
    for dataset in source["datasets"]:
        columns = dataset["columns"]
        frame = {}
        for index, col in enumerate(columns):
            values = [row[index] for row in dataset["rows"]]
            if col["type"] == "numeric":
                values = [float("nan") if isinstance(v, dict) else float(v) for v in values]
                frame[col["name"]] = pd.Series(values, dtype="float64")
            else:
                frame[col["name"]] = pd.Series([v.ljust(col["length"]) for v in values], dtype="object")
        path = out / (dataset["name"].lower() + ".xpt")
        pyreadstat.write_xport(pd.DataFrame(frame), str(path), file_format_version=5,
                              table_name=dataset["name"], file_label=dataset["label"],
                              column_labels={c["name"]: c["label"] for c in columns})
        content = bytearray(path.read_bytes())
        # Remove volatile writer dates; these are fixture constants, not audit claims.
        for match in list(re.finditer(rb"\d{2}[A-Z]{3}\d{2}:\d{2}:\d{2}:\d{2}", content)):
            content[match.start():match.end()] = fixed_date
        obs_header = content.index(b"HEADER RECORD*******OBS     HEADER RECORD!!!!!!!")
        data_start = obs_header + 80
        stride = sum(c["length"] for c in columns)
        for row_index, row in enumerate(dataset["rows"]):
            offset = 0
            for col, value in zip(columns, row):
                if isinstance(value, dict):
                    code = value["sas_missing"]
                    position = data_start + row_index * stride + offset
                    replacement = code.encode("ascii") + bytes(col["length"] - 1)
                    content[position:position + col["length"]] = replacement
                    byte_edits.append({"file": path.name, "variable": col["name"], "row_1based": row_index + 1,
                                       "offset_0based": position, "hex": replacement.hex(), "missing_code": code})
                offset += col["length"]
        path.write_bytes(content)
    (out / "cm.xpt").write_bytes(b"SYNTHETIC CORRUPT XPT - INTENTIONAL READ FAILURE\n")
    changed = json.loads((out / "spec.json").read_text("utf-8"))
    changed["version"] = "0.2-synthetic-change"
    changed["datasets"][0]["variables"][3]["label"] = "Revised Synthetic Sex"
    write_json(out / "spec-changed.json", changed)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
    sources = []
    for sid, name, kind, scope in [
        ("SRC-DM", "dm.xpt", "xpt", ["DM"]), ("SRC-VS", "vs.xpt", "xpt", ["VS"]),
        ("SRC-AE", "ae.xpt", "xpt", ["AE"]), ("SRC-CM", "cm.xpt", "xpt", ["CM"]),
        ("SRC-SPEC", "spec.json", "structured_spec", ["DM", "VS", "AE", "CM"])]:
        exists = (out / name).is_file()
        sources.append({"source_id": sid, "relative_path": name, "sha256": digest(out / name) if exists else None,
                        "source_type": kind, "version": "0.1", "acquired_at": now,
                        "confidentiality": "fully_synthetic", "provision_status": "provided" if exists else "not_provided",
                        "completeness_scope": {"datasets": scope, "declaration": "closed_for_synthetic_scenario"},
                        "reason": None if exists else "Intentionally not supplied; business No Data reason unknown"})
    write_json(out / "input-manifest.json", {"version": "0.1", "study_id": "SYN001", "family": "SDTM",
               "planned_datasets": ["DM", "VS", "AE", "CM"], "provided_scope_complete": False,
               "other_sources": {k: "not_provided" for k in ["acrf", "ct", "protocol", "sap"]}, "sources": sources})
    write_json(out / "dependencies.json", {"dependency_snapshot_id": "SYN-DEP-001",
               "inputs": {s["source_id"]: {"path": s["relative_path"], "sha256": s["sha256"]} for s in sources},
               "study_id": "SYN001", "object_id": "study/SYN001/family/SDTM/dataset/DM/variable/SEX", "field_path": "label",
               "standards": {"sdtmig": {"status": "not_selected"}, "ct": {"status": "not_selected"}, "define_target": "2.1"},
               "rules": {"version": "SYN-RULE-1", "label_comparison": "trim_ascii_spaces_then_exact"},
               "config": {"version": "SYN-CONFIG-1", "trim_ascii_spaces": True},
               "model_schema": {"version": "task001-contract-0.1", "path": "docs/contracts/TASK-001-contract-v0.1.md"},
               "upstream_decisions": [], "tools": {"pyreadstat": pyreadstat.__version__, "pandas": pd.__version__},
               "audit": {"run_started_at": now}, "scope": "synthetic_test_dependency_context_not_business_approval"})
    write_json(out / "build-record.json", {"executed_at": now, "python": sys.version, "script_sha256": digest(Path(__file__)),
               "pyreadstat": pyreadstat.__version__, "pandas": pd.__version__, "byte_edits": byte_edits,
               "purpose": "fixture manufacturing only; no expectations generated", "output_hashes": {p.name: digest(p) for p in out.glob("*.xpt")}})
    print(json.dumps({"out": str(out), "xpt_count": 3, "special_missing_edits": len(byte_edits)}))


if __name__ == "__main__":
    main()
