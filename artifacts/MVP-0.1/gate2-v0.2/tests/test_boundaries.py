"""Additional fixed preimplementation expectations plus failure regressions."""
from copy import deepcopy
from pathlib import Path
import json
import struct
import subprocess
import sys
import time
import unittest

from define_auto.common import ContractError, canonical, load, pointer, sha, strict_json, write
from define_auto.decisions import apply_decision
from define_auto.engine import read_spec, reconcile
from define_auto.model import validate_model
from define_auto.reporting import html_report, markdown
from define_auto.xpt import read_xpt, validate_context
from tests.support import BASE, ROOT, baseline, obj, patch_context, workspace

PREP = load(ROOT / "expectations/mvp01/v0.1/additional-cases.json")
FIXTURES = ROOT / "fixtures/mvp01/v0.1"
ACTUAL = {}


def physical(fixture, encoding=None, declaration=True):
    raw = (FIXTURES / (fixture + ".xpt")).read_bytes()
    ctx = load(FIXTURES / "read-context.json")
    d = next(d for d in ctx["declarations"] if d["source_sha256"] == sha(raw))
    return read_xpt(raw, encoding=encoding or d["encoding"], declaration=d if declaration else None, allow_values=True)


class AdditionalTests(unittest.TestCase):
    CASE_IDS = [f"M01-A{i:02}" for i in range(1, 22)]

    def check_additional(self, n):
        expected = PREP["cases"][n - 1]["expected"]
        actual = {}
        if n in (1, 4, 5, 6, 7, 8, 20):
            fixture = PREP["cases"][n - 1]["input"]["fixture"]
            start = time.perf_counter(); p = physical(fixture); elapsed = time.perf_counter() - start
            v = p["variables"][0]
            self.assertEqual(p["row_count"], expected.get("rows", 1))
            if n in (1, 4, 20):
                e = expected["VALUE"]
                for k in ["max_content_bytes", "max_content_characters"]:
                    self.assertEqual(v[k], e[k])
                self.assertEqual(v["missing_count"], e["missing"])
                self.assertEqual(v["nonmissing_count"], e["nonmissing"])
                if n == 1: self.assertEqual(v["storage_length"], e["storage_bytes"])
                if n == 20: self.assertEqual(v["distinct_nonmissing"], e["distinct_nonmissing"])
            elif n == 5:
                self.assertEqual(v["missing_code_counts"], expected["VALUE"]["missing_codes"])
                self.assertEqual(v["missing_count"], 28); self.assertEqual(v["nonmissing_count"], 3)
                self.assertCountEqual(v["observed_values"], expected["VALUE"]["nonmissing_values"])
            elif n == 6:
                for k in ["format_name", "format_width", "format_decimals"]:
                    self.assertEqual(v[k], expected["VALUE"][k])
                self.assertCountEqual(v["observed_values"], expected["VALUE"]["raw_numeric_values"])
                self.assertTrue(all(isinstance(x, (int, float)) for x in v["observed_values"]))
            elif n == 7:
                self.assertEqual(v["observed_values"], [expected["VALUE"]["preserved_text"]])
                self.assertEqual(v["max_content_bytes"], 7); self.assertEqual(v["max_content_characters"], 7)
            elif n == 8:
                self.assertEqual(v["observed_values"], [expected["raw_value"]])
                self.assertEqual(v["format_name"], expected["format_name"])
                self.assertEqual(v["format_width"], expected["format_width"])
                self.assertEqual(v["format_interpretation"], "gap")
            actual = {"row_count": p["row_count"], "aggregate": v, "elapsed_seconds": elapsed}
        elif n == 2:
            with self.assertRaises(ContractError) as c: physical("invalid_utf8")
            self.assertEqual(c.exception.code, "decode_error"); self.assertTrue(c.exception.locator)
            actual = {"result": "unreadable", "code": c.exception.code}
        elif n == 3:
            with self.assertRaises(ContractError) as c:
                read_xpt((FIXTURES / "utf8.xpt").read_bytes(), encoding=None)
            self.assertEqual(c.exception.code, "encoding_required"); actual = {"code": c.exception.code}
        elif n in (9, 10, 11, 12, 13, 14):
            spec = load(BASE / "spec.json")
            if n == 9: spec["datasets"].append(deepcopy(spec["datasets"][0]))
            if n == 10: spec["datasets"][0]["variables"].append(deepcopy(spec["datasets"][0]["variables"][0]))
            if n == 14: spec["datasets"][0]["name"] = "dm"
            if n in (9, 10, 14):
                with self.assertRaises(ContractError) as c: read_spec(spec)
                self.assertEqual(c.exception.code, "invalid_object_name" if n == 14 else "ambiguous_identity")
                actual = {"code": c.exception.code}
            elif n == 11:
                raw = (BASE / "spec.json").read_text(encoding="utf-8").replace('"family": "SDTM"', '"family": "SDTM", "family": "ADAM"')
                with self.assertRaises(ContractError) as c: strict_json(raw)
                self.assertEqual(c.exception.code, "duplicate_json_key"); actual = {"code": c.exception.code}
            else:
                if n == 12: spec["datasets"][0]["variables"][0]["mystery"] = "KEEP-ME"
                else: spec["extension_slots"]["methods"] = [{"method_id": "TEST-M1", "text": "Synthetic candidate"}]
                uns = read_spec(spec)
                locator = "/datasets/0/variables/0/mystery" if n == 12 else "/extension_slots/methods"
                self.assertIn(locator, [k for k, _ in uns]); actual = {"unsupported": uns}
                # Exercise registry -> Spec -> model issues, beyond adapter alone.
                with workspace() as tmp:
                    folder = Path(tmp)
                    manifest = load(BASE / "input-manifest.json")
                    for source in manifest["sources"]:
                        if source["provision_status"] == "provided":
                            data = canonical(spec) if source["source_type"] == "structured_spec" else (BASE / source["relative_path"]).read_bytes()
                            (folder / source["relative_path"]).write_bytes(data); source["sha256"] = sha(data)
                    write(folder / "input-manifest.json", manifest)
                    from tests.support import CONTEXT, PROVENANCE
                    m = reconcile(folder / "input-manifest.json", context_path=CONTEXT, provenance_paths=PROVENANCE, test_mode=True)
                    self.assertTrue(any(i["category"] == "unsupported_metadata" and i["field_path"] == locator for i in m["issues"]))
                    self.assertTrue(any(e["locator"] == locator for e in m["evidence"]))
        elif n == 15:
            base = baseline()
            mutations = []
            x = deepcopy(base); x["assertions"][0]["assertion_kind"] = "guessed"; mutations.append(x)
            x = deepcopy(base); x["assertions"][0]["evidence_ids"] = ["NO-SUCH-EVIDENCE"]; mutations.append(x)
            x = deepcopy(base); x["objects"] = [o for o in x["objects"] if not (o["kind"] == "dataset" and o["dataset"] == "DM")]; mutations.append(x)
            x = deepcopy(base); x["evidence"].append(deepcopy(x["evidence"][0])); x["evidence"][-1]["raw_value"] = "different"; mutations.append(x)
            x = deepcopy(base); x["assertions"][0]["value"] = float("nan"); mutations.append(x)
            for x in mutations:
                with self.subTest(variant=len(x["objects"])):
                    with self.assertRaises(ContractError): validate_model(x)
            actual = {"rejected_variants": len(mutations)}
        elif n == 16:
            m, p, a = patch_context(baseline()); dep = m["dependency_snapshot"]
            with self.assertRaises(ContractError): apply_decision(m, p, dep, a, test_mode=False)
            real = deepcopy(p); real["authorization_status"] = "authorized"
            with self.assertRaises(ContractError): apply_decision(m, real, dep, None)
            simulated, result = apply_decision(m, p, dep, a, test_mode=True)
            self.assertEqual(result["status"], "test_simulated")
            self.assertFalse(any(o["approved"] for o in simulated["objects"]))
            self.assertFalse(any(i["status"] == "resolved" for i in simulated["issues"]))
            with self.assertRaises(ContractError): apply_decision(simulated, p, dep, a, test_mode=False)
            actual = result
        elif n == 17:
            m, p, a = patch_context(baseline()); dep = m["dependency_snapshot"]
            for change in PREP["cases"][n - 1]["input"]["independent_variants"]:
                change = {k: v for k, v in change.items() if k != "selection_basis"}
                q = {**p, **change}
                with self.subTest(change=change):
                    with self.assertRaises(ContractError): apply_decision(m, q, dep, a, test_mode=True)
            actual = {"all_variants_rejected": True}
        elif n == 18:
            m, p, a = patch_context(baseline()); dep = m["dependency_snapshot"]
            first, _ = apply_decision(m, p, dep, a, test_mode=True); old = canonical(first["decisions"][0])
            q = {**p, "decision_id": "TEST-DEC-002", "supersedes": p["decision_id"], "selected_value": "Sex"}
            a = deepcopy(a); a["scope"]["selected_value"] = "Sex"
            second, r = apply_decision(first, q, dep, a, test_mode=True)
            third, repeat = apply_decision(second, q, dep, a, test_mode=True)
            self.assertEqual(canonical(second["decisions"][0]), old)
            self.assertEqual(second["decisions"][1]["patch"]["supersedes"], p["decision_id"])
            self.assertEqual(repeat["business_changes"], 0); self.assertFalse(any(o["approved"] for o in third["objects"]))
            actual = {"first": r, "repeat": repeat}
        elif n == 19:
            m, p, a = patch_context(baseline()); dep = deepcopy(m["dependency_snapshot"])
            m, _ = apply_decision(m, p, dep, a, test_mode=True)
            m["downstream_records"] = [{"record_id": "TEST-VAL", "status": "passed"}, {"record_id": "TEST-APR", "status": "test_simulated", "test_only": True}]
            history = canonical(m["decisions"]); old_records = canonical(m["downstream_records"])
            m["dependency_snapshot"]["rules"]["version"] = "SYN-RULE-2"
            result, info = apply_decision(m, p, dep, a, test_mode=True)
            self.assertEqual(info["status"], "needs_review"); self.assertEqual(info["business_changes"], 0)
            self.assertEqual(history, canonical(result["decisions"])); self.assertEqual(old_records, canonical(result["downstream_records"]))
            self.assertTrue(all(x["status"] == "needs_review" for x in result["downstream_applicability"]))
            actual = info
        elif n == 21:
            raw = (FIXTURES / "utf8.xpt").read_bytes()
            overlap = bytearray(raw); overlap[780 + 84:780 + 88] = struct.pack(">i", 0)
            badsize = bytearray(raw); badsize[314:318] = b"0136"
            for variant in [raw[:-1], bytes(overlap), bytes(badsize)]:
                with self.assertRaises(ContractError): read_xpt(variant, encoding="utf-8", allow_values=True)
            actual = {"rejected_variants": 3}
        ACTUAL[f"M01-A{n:02}"] = actual


for _n in range(1, 22):
    setattr(AdditionalTests, f"test_M01_A{_n:02}", lambda self, n=_n: self.check_additional(n))


class RuntimeBoundaryTests(unittest.TestCase):
    def test_model_review_regressions(self):
        m = baseline()
        cases = []
        for field, value in [("kind", "dataset"), ("approved", {"label": "TBD"})]:
            x = deepcopy(m); obj(x, "DM", "SEX")[field] = value; cases.append(x)
        x = deepcopy(m); obj(x, "DM", "SEX")["observed"]["missing_count"] = 999; cases.append(x)
        x = deepcopy(m); next(a for a in x["assertions"] if a["field_path"] == "label")["value"] = "TBD"; cases.append(x)
        for x in cases:
            with self.assertRaises(ContractError): validate_model(x)

    def test_manifest_failures(self):
        with workspace() as tmp:
            folder = Path(tmp); original = load(BASE / "input-manifest.json")
            for source in original["sources"]:
                if source["provision_status"] == "provided":
                    (folder / source["relative_path"]).write_bytes((BASE / source["relative_path"]).read_bytes())
            for relative in ["../outside", str(BASE / "dm.xpt"), "C:\\outside.xpt"]:
                m = deepcopy(original); m["sources"][0]["relative_path"] = relative
                write(folder / "input-manifest.json", m)
                with self.assertRaises(ContractError) as c: reconcile(folder / "input-manifest.json")
                self.assertEqual(c.exception.code, "unsafe_input_path")
            for mutate in ["hash", "supply", "duplicate"]:
                m = deepcopy(original)
                if mutate == "hash": m["sources"][0]["sha256"] = "0" * 64
                if mutate == "supply": m["sources"][0]["provision_status"] = "not_provided"; m["sources"][0]["sha256"] = None
                if mutate == "duplicate": m["sources"].append(deepcopy(m["sources"][0]))
                write(folder / "input-manifest.json", m)
                with self.assertRaises(ContractError): reconcile(folder / "input-manifest.json")

    def test_provenance_wrong_target_and_pointer(self):
        raw = (BASE / "dm.xpt").read_bytes()
        from tests.support import CONTEXT, PROVENANCE
        context = load(CONTEXT); context["declarations"] = context["declarations"][:1]
        sid, p = next(iter(PROVENANCE.items()))
        registry = {sid: {"sha256": sha(p.read_bytes()), "bytes": p.read_bytes()},
                    "DM": {"sha256": sha(raw), "bytes": raw, "source_type": "xpt"}}
        for loc in ["/declarations/1", "/declarations/-1", "/declarations/01"]:
            context["declarations"][0]["provenance"]["locator"] = loc
            with self.assertRaises(ContractError): validate_context(context, "SYN001", "SDTM", registry, test_mode=True)

    def test_raw_label_and_privacy(self):
        m = baseline()
        matches = [e for e in m["evidence"] if e["extraction_method"] == "xpt_ascii_trim_v1"]
        self.assertTrue(any(e["raw_value"] != e["normalized_value"] for e in matches))
        self.assertTrue(all(e["raw_value"].strip(" ") == e["normalized_value"] for e in matches))
        v = obj(m, "DM", "USUBJID")["observed"]
        self.assertIsNone(v["observed_values"]); self.assertEqual(v["distinct_nonmissing"], 3)
        ordinary = read_xpt((BASE / "dm.xpt").read_bytes(), encoding="ascii",
                           declaration=load(ROOT / "fixtures/mvp01/baseline-context-v0.1/read-context.json")["declarations"][0])
        self.assertIsNone(next(v for v in ordinary["variables"] if v["name"] == "EXTRA")["observed_values"])

    def test_html_and_markdown_escape(self):
        m = baseline(); obj(m, "DM", "SEX")["expected"]["label"] = '<script>alert(1)</script>|bad\nline'
        self.assertNotIn("<script>", html_report(m)); self.assertIn("&lt;script&gt;", html_report(m))
        self.assertIn("&#124;", markdown(m)); self.assertNotIn("<script>", markdown(m))

    def test_stability_and_reordered_input(self):
        from tests.support import CONTEXT, PROVENANCE
        a = baseline()
        with workspace() as tmp:
            folder = Path(tmp); m = load(BASE / "input-manifest.json")
            m["sources"].reverse()
            for source in m["sources"]:
                if source["provision_status"] == "provided":
                    (folder / source["relative_path"]).write_bytes((BASE / source["relative_path"]).read_bytes())
            write(folder / "input-manifest.json", m)
            b = reconcile(folder / "input-manifest.json", context_path=CONTEXT, provenance_paths=PROVENANCE, test_mode=True)
        self.assertEqual(canonical(a), canonical(b))

    def test_cli_recovery_and_no_overwrite(self):
        from tests.support import CONTEXT, PROVENANCE
        with workspace() as tmp:
            out = Path(tmp) / "delivery"
            command = [sys.executable, "-m", "define_auto", "--manifest", str(BASE / "input-manifest.json"),
                "--read-context", str(CONTEXT), "--provenance", "TEST-BASELINE-MANUFACTURE-001=" + str(next(iter(PROVENANCE.values()))),
                "--isolated-test", "--out", str(out)]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            model = load(out / "model.json"); validate_model(model)
            manifest = load(out / "outputs-manifest.json")
            for f in manifest["files"]: self.assertEqual(sha((out / f["path"]).read_bytes()), f["sha256"])
            before = {p.name: sha(p.read_bytes()) for p in out.iterdir()}
            again = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(before, {p.name: sha(p.read_bytes()) for p in out.iterdir()})

    def test_cli_decision_history(self):
        from tests.support import CONTEXT, PROVENANCE
        with workspace() as tmp:
            folder = Path(tmp)
            common = [sys.executable, "-m", "define_auto", "--manifest", str(BASE / "input-manifest.json"),
                "--read-context", str(CONTEXT), "--provenance", "TEST-BASELINE-MANUFACTURE-001=" + str(next(iter(PROVENANCE.values()))), "--isolated-test"]
            def run(name, extra):
                out = folder / name
                result = subprocess.run(common + extra + ["--out", str(out)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return out, load(out / "model.json")
            baseout, base = run("base", [])
            p = load(BASE / "patch.json"); p["dependency_snapshot_id"] = base["dependency_snapshot"]["dependency_snapshot_id"]
            auth = dict(authorization_id="TEST-CLI-AUTH", reviewer=p["reviewer"], test_only=True,
                        scope={k: p[k] for k in ["object_id", "field_path", "selected_value", "dependency_snapshot_id"]})
            pp, ap = folder / "patch.json", folder / "auth.json"
            write(pp, p); write(ap, auth)
            flags = ["--patch", str(pp), "--authorization", str(ap), "--previous-dependency", str(baseout / "dependencies.json")]
            firstout, first = run("first", flags)
            secondout, second = run("second", flags + ["--prior-model", str(firstout / "model.json")])
            self.assertEqual(canonical(first), canonical(second))
            self.assertEqual(load(secondout / "patch-applicability.json")["business_changes"], 0)
            q = {**p, "decision_id": "TEST-CLI-REVISION", "supersedes": p["decision_id"], "selected_value": "Sex"}
            write(pp, q); auth["scope"]["selected_value"] = "Sex"; auth["authorization_id"] = "TEST-CLI-AUTH-2"; write(ap, auth)
            _, third = run("third", flags + ["--prior-model", str(secondout / "model.json")])
            self.assertEqual(third["decisions"][0], first["decisions"][0]); self.assertEqual(len(third["decisions"]), 2)
            self.assertEqual(obj(third, "DM", "SEX")["simulated_selection"]["label"], "Sex")
            self.assertFalse(any(o["approved"] for o in third["objects"]))

    def test_persisted_model_integrity(self):
        m = baseline(); validate_model(m, sealed=True)
        for field in ["model_snapshot_id", "dependency_snapshot_id"]:
            x = deepcopy(m)
            if field == "model_snapshot_id": x[field] = "model-" + "0" * 64
            else: x["dependency_snapshot"][field] = "dep-" + "0" * 64
            with self.assertRaises(ContractError): validate_model(x, sealed=True)
        for mutate in ["type", "expected", "downstream", "resolved"]:
            x = deepcopy(m)
            if mutate == "type": obj(x, "DM", "SEX")["observed"]["type"] = ["arbitrary"]
            if mutate == "expected": obj(x, "DM", "SEX")["expected"]["label"] = "Different label"
            if mutate == "downstream": x["downstream_records"] = [{"record_id": None, "status": "APPROVED"}]
            if mutate == "resolved": x["issues"][0].update(status="resolved", decision_id="NO-SUCH-DECISION")
            with self.assertRaises(ContractError): validate_model(x)

    def test_report_field_provenance_and_length(self):
        from define_auto.reporting import review_rows
        m = baseline()
        self.assertTrue(all(row[8] for row in review_rows(m)))
        # Rendering-only isolated fixture: does not create approved assertions.
        obj(m, "DM", "SEX")["approved"]["storage_vs_declared_length"] = 3
        row = next(row for row in review_rows(m) if row[0] == obj(m, "DM", "SEX")["object_id"] and row[1] == "declared_length")
        self.assertEqual(row[5], 3)
        arm_length = next(row for row in review_rows(m) if row[0] == obj(m, "DM", "ARMCD")["object_id"] and row[1] == "declared_length")
        self.assertEqual(arm_length[7], "")

    def test_cli_contract_errors(self):
        from tests.support import CONTEXT, PROVENANCE
        with workspace() as tmp:
            folder = Path(tmp)
            common = [sys.executable, "-m", "define_auto", "--manifest", str(BASE / "input-manifest.json"),
                "--read-context", str(CONTEXT), "--provenance", "TEST-BASELINE-MANUFACTURE-001=" + str(next(iter(PROVENANCE.values()))), "--isolated-test"]
            initial = folder / "initial"
            result = subprocess.run(common + ["--out", str(initial)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            m = load(initial / "model.json")
            p = load(BASE / "patch.json"); p["dependency_snapshot_id"] = m["dependency_snapshot"]["dependency_snapshot_id"]
            auth = dict(authorization_id="TEST-CLI-ERRORS", reviewer=p["reviewer"], test_only=True,
                scope={k: p[k] for k in ["object_id", "field_path", "selected_value", "dependency_snapshot_id"]})
            for i, (pv, av, dv, error) in enumerate([
                (p, [], m["dependency_snapshot"], "invalid_authorization_record"),
                (p, auth, [], "invalid_dependency_snapshot"),
                ({**p, "issue_ids": [{}]}, auth, m["dependency_snapshot"], "invalid_issue_references")]):
                pp, ap, dp = folder / "p.json", folder / "a.json", folder / "d.json"
                write(pp, pv); write(ap, av); write(dp, dv)
                run = subprocess.run(common + ["--patch", str(pp), "--authorization", str(ap), "--previous-dependency", str(dp),
                        "--out", str(folder / ("bad" + str(i)))], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 1); self.assertNotIn("Traceback", run.stderr)
                self.assertEqual(json.loads(run.stdout)["error"], error)
