"""Independent, fixed-fixture byte audit; no Spec reconciliation or patch engine.

Reads no implementation/checker code and does not import the fixture writer/reader.
SAS V5 NAMESTR layout and IBM base-16 numeric storage are inspected directly.
Run from project root with --out pointing to a new JSON evidence file.
"""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import struct


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_xpt(path):
    content = path.read_bytes()
    namestr_header = content.index(b"HEADER RECORD*******NAMESTR HEADER RECORD!!!!!!!")
    obs_header = content.index(b"HEADER RECORD*******OBS     HEADER RECORD!!!!!!!")
    variable_count = int(content[namestr_header + 54:namestr_header + 58])
    descriptors = []
    for position in range(variable_count):
        start = namestr_header + 80 + 140 * position
        descriptor = content[start:start + 140]
        descriptors.append({
            "name": descriptor[8:16].decode("ascii").strip(),
            "type": int.from_bytes(descriptor[0:2], "big"),
            "width": int.from_bytes(descriptor[4:6], "big"),
            "label": descriptor[16:56].decode("ascii").rstrip(),
            "position": int.from_bytes(descriptor[84:88], "big"),
        })
    stride = max(d["position"] + d["width"] for d in descriptors)
    data = content[obs_header + 80:].rstrip(b" ")
    assert len(data) % stride == 0, "Fixed fixture must have whole nonblank-terminal records"
    rows = len(data) // stride
    aggregates = {}
    for variable in descriptors:
        cells = [data[r * stride + variable["position"]:r * stride + variable["position"] + variable["width"]]
                 for r in range(rows)]
        if variable["type"] == 2:
            values = [cell.decode("ascii").strip(" ") for cell in cells]
            nonmissing = [value for value in values if value]
            aggregate = {"missing": len(values) - len(nonmissing), "distinct_nonmissing": len(set(nonmissing)),
                         "max_content_bytes": max(map(len, nonmissing), default=0)}
        else:
            missing_codes = collections.Counter()
            nonmissing = []
            for cell in cells:
                if cell[0] in b"._ABCDEFGHIJKLMNOPQRSTUVWXYZ" and cell[1:] == bytes(len(cell) - 1):
                    missing_codes[chr(cell[0])] += 1
                else:
                    sign = -1 if cell[0] & 0x80 else 1
                    exponent = (cell[0] & 0x7f) - 64
                    fraction = int.from_bytes(cell[1:], "big") / 2 ** (8 * (len(cell) - 1))
                    nonmissing.append(sign * fraction * 16 ** exponent)
            aggregate = {"missing": sum(missing_codes.values()), "missing_codes": dict(missing_codes),
                         "distinct_nonmissing": len(set(nonmissing))}
            if variable["name"] == "ARMCD":
                aggregate["synthetic_values"] = nonmissing
        aggregates[variable["name"]] = aggregate
    return {"sha256": fingerprint(path), "rows": rows, "descriptors": descriptors,
            "aggregates": aggregates, "namestr_header_offset": namestr_header,
            "observation_header_offset": obs_header, "stride": stride,
            "row_count_limit": "Fixed DM ends in nonblank EXTRA; VS has no payload. Not a general XPT row-count algorithm."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = root / args.out
    assert not output.exists(), "Evidence must not overwrite an earlier run"
    fixture = root / "fixtures/task001/v0.1"
    findings = {name: inspect_xpt(fixture / (name.lower() + ".xpt")) for name in ["DM", "VS"]}
    assert findings["DM"]["rows"] == 3
    assert findings["DM"]["aggregates"]["AGE"]["missing_codes"] == {".": 1, "A": 1, "Z": 1}
    assert findings["DM"]["aggregates"]["SEX"]["missing"] == 3
    assert findings["DM"]["aggregates"]["ARMCD"]["synthetic_values"] == [1.0, 2.0, 1.0]
    assert findings["VS"]["rows"] == 0
    assert all(a["missing"] == 0 and a["distinct_nonmissing"] == 0 for a in findings["VS"]["aggregates"].values())
    assert not (fixture / "ae.xpt").exists()
    assert not (fixture / "cm.xpt").read_bytes().startswith(b"HEADER RECORD*******LIBRARY")
    evidence = {"reviewer": "/root/review_contract", "recorded_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
                "script_sha256": fingerprint(Path(__file__)), "method": "stdlib raw bytes only, separate from fixture writer/reader/checker",
                "result": "passed", "assertions_executed": 8, "engine_behavior": "not_run", "findings": findings}
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(output), "result": "passed", "assertions_executed": 8}))


if __name__ == "__main__":
    main()
