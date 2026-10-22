"""Independent M01-D01 cases fixed before first reader execution.

All RC expectations come from the frozen v0.2 JSON, never actual outputs.
Real XPT bytes, source registration, reconciliation and patch application are used.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from define_auto.common import ContractError, canonical, load, sha, write
from define_auto.decisions import apply_decision, compare_dependencies
from define_auto.engine import reconcile
from define_auto.model import business_digest
from define_auto.xpt import read_xpt, validate_context


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = ROOT / "expectations/mvp01/v0.2/read-context-cases.json"
EXPECTED_HASH = "486069d14f3d8b22a88c6b25eeb1eb8485effbd96d846b01322de6e512c44f6a"
FIXED = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
BASELINE = ROOT / "artifacts/TASK-001/gate1-v0.1/fixtures/task001/v0.1"
BASE_CONTEXT = ROOT / "fixtures/mvp01/baseline-context-v0.1/read-context.json"
BASE_SOURCE = ROOT / "fixtures/mvp01/baseline-context-v0.1/delivery-record.json"


def put(obj, path, value=None, *, delete=False):
    parts = path.strip("/").split("/")
    for part in parts[:-1]:
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    key = int(parts[-1]) if isinstance(obj, list) else parts[-1]
    if delete:
        del obj[key]
    else:
        obj[key] = deepcopy(value)


class ReadContextCases(unittest.TestCase):
    CASE_IDS = tuple(c["case_id"] for c in FIXED["cases"])

    def setUp(self):
        self.assertEqual(sha(EXPECTED_PATH.read_bytes()), EXPECTED_HASH,
                         "Independent expectations changed: review a new version, do not rebaseline.")
        (ROOT / "work").mkdir(exist_ok=True)
        self.sandbox = tempfile.TemporaryDirectory(prefix="rc-cases-", dir=ROOT / "work")
        self.addCleanup(self.sandbox.cleanup)
        self.temp = Path(self.sandbox.name)

    def delivery(self, raw, member, count, encoding, suffix="fresh"):
        source_id = "TEST-RC-SOURCE-" + suffix
        doc = {"source_id": source_id, "test_only": True,
               "provided_by": "TEST_INDEPENDENT_FIXTURE_CONSTRUCTOR",
               "declarations": [{"member": member, "source_sha256": sha(raw),
                                  "record_count": count, "encoding": encoding}],
               "derivation": "isolated explicit synthetic delivery; no product outputs or expected answers used"}
        source_bytes = canonical(doc)
        d = {"declaration_id": "TEST-RC-DECL-" + suffix,
             "source_sha256": sha(raw), "member": member, "encoding": encoding,
             "record_count": count, "provided_by": doc["provided_by"],
             "provenance": {"source_id": source_id,
                            "source_sha256": sha(source_bytes), "locator": "/declarations/0"}}
        return d, {source_id: {"source_id": source_id, "source_type": "delivery_evidence",
                              "sha256": sha(source_bytes), "bytes": source_bytes,
                              "provision_status": "provided", "read_status": "readable"}}

    def setup_base(self, name):
        b = FIXED["baselines"][name]
        if name == "vs_blank_tail":
            raw = (BASELINE / "vs.xpt").read_bytes() + b" " * 80
            self.assertEqual(sha(raw), b["derived_xpt_sha256"])
            d, registry = self.delivery(raw, "VS", 1, "ascii", "blank-tail")
            context = {"schema_version": "mvp01-read-context-0.1", "study_id": "SYN001",
                       "family": "SDTM", "test_only": True, "declarations": [d]}
        else:
            raw = (ROOT / b["xpt_path"]).read_bytes()
            self.assertEqual(sha(raw), b["xpt_sha256"])
            context = load(ROOT / b["context_path"])
            context["declarations"] = [deepcopy(next(d for d in context["declarations"]
                if d["declaration_id"] == b["declaration_select"]))]
            p = ROOT / b["provenance_path"]
            data = p.read_bytes()
            self.assertEqual(sha(data), b["provenance_sha256"])
            sid = context["declarations"][0]["provenance"]["source_id"]
            registry = {sid: {"source_id": sid, "source_type": "delivery_evidence",
                             "sha256": sha(data), "bytes": data,
                             "provision_status": "provided", "read_status": "readable"}}
        registry["TEST-XPT"] = {"source_id": "TEST-XPT", "source_type": "xpt",
                                "sha256": sha(raw), "bytes": raw,
                                "provision_status": "provided", "read_status": "readable"}
        return {"raw": raw, "context": context, "registry": registry,
                "explicit_encoding": "ascii", "missing_source_file": False}

    def mutate(self, state, mutation):
        op = mutation["op"]
        ctx = state["context"]
        if op == "set":
            put(ctx, mutation["path"], mutation["value"])
        elif op == "delete":
            put(ctx, mutation["path"], delete=True)
        elif op == "omit_context":
            state["context"] = None
            state["explicit_encoding"] = mutation["explicit_encoding"]
        elif op == "omit_registry_source":
            del state["registry"][mutation["source_id"]]
        elif op == "registry_source_path":
            state["missing_source_file"] = True
        elif op == "source_document_append_hex":
            sid = ctx["declarations"][0]["provenance"]["source_id"]
            entry = state["registry"][sid]
            entry["bytes"] += bytes.fromhex(mutation["hex"])
            entry["sha256"] = sha(entry["bytes"])
        elif op == "append_copy":
            d = deepcopy(ctx["declarations"][0])
            d.update(mutation.get("override", {}))
            ctx["declarations"].append(d)
        elif op == "new_synthetic_delivery":
            old = ctx["declarations"][0]
            d, new = self.delivery(state["raw"], old["member"], mutation["record_count"],
                                   old["encoding"], "changed-count")
            ctx["declarations"] = [d]
            state["registry"].update(new)
        elif op == "xpt_set_byte":
            b = bytearray(state["raw"])
            b[mutation["offset"]] = int(mutation["hex"], 16)
            state["raw"] = bytes(b)
        elif op == "rebind_context_and_provenance_to_modified_xpt":
            old = ctx["declarations"][0]
            d, new = self.delivery(state["raw"], old["member"], old["record_count"],
                                   old["encoding"], "rebound-xpt")
            ctx["declarations"] = [d]
            state["registry"].update(new)
            state["registry"]["TEST-XPT"].update(sha256=sha(state["raw"]), bytes=state["raw"])
        else:
            self.fail("Unimplemented frozen mutation: " + op)

    def execute_read(self, state, case):
        context = state["context"]
        if state["missing_source_file"]:
            # Exercise actual file registration; a fake in-memory absence would
            # repeat RC14 instead of the registered-but-missing RC15 boundary.
            path = self.temp / "context.json"
            write(path, context)
            return reconcile(BASELINE / "input-manifest.json", context_path=path,
                             provenance_paths={context["declarations"][0]["provenance"]["source_id"]:
                                               self.temp / "missing-delivery-record.json"},
                             test_mode=True, config={"encoding": "ascii"})
        if context is not None:
            validate_context(context, "SYN001", "SDTM", state["registry"],
                             test_mode=case.get("mode", "isolated_test") == "isolated_test")
            declaration = context["declarations"][0]
            encoding = declaration["encoding"]
        else:
            declaration = None
            encoding = state["explicit_encoding"]
        return read_xpt(state["raw"], encoding=encoding, declaration=declaration, allow_values=True)

    def assert_success(self, parsed, case, raw):
        exp = case["expected"]
        self.assertEqual(parsed["row_count"], exp["row_count"])
        self.assertEqual(parsed["row_count_basis"], exp["row_count_basis"])
        self.assertEqual(parsed["padding_bytes"], exp["padding_bytes"])
        self.assertNotIn("approved", parsed)
        if exp["row_count_basis"] == "delivery_declaration":
            self.assertTrue(parsed["declaration_id"])
            self.assertEqual(parsed["count_limitation"],
                             "trusted_delivery_declaration_not_independently_verified")
            self.assertTrue(parsed["declaration_provenance"]["source_id"])
            self.assertTrue(parsed["declaration_provenance"]["source_sha256"])
            self.assertTrue(parsed["declaration_provenance"]["locator"])
        if "each_of_5_variables" in exp:
            self.assertEqual(len(parsed["variables"]), 5)
            for v in parsed["variables"]:
                e = exp["each_of_5_variables"]
                wanted = "present_all_missing" if e["observation_state"] == "all_missing" else e["observation_state"]
                self.assertEqual(v["observed_status"], wanted)
                self.assertEqual(v["missing_count"], e["missing_count"])
                self.assertEqual(v["nonmissing_count"], e["nonmissing_count"])
        if "VALUE" in exp:
            v = next(v for v in parsed["variables"] if v["name"] == "VALUE")
            for k, value in exp["VALUE"].items():
                self.assertEqual(v["storage_length" if k == "storage_bytes" else k], value)
        if "last_numeric_cell_hex" in exp:
            self.assertEqual(raw[1760 + 3 * 34 + 17:1760 + 3 * 34 + 25].hex(),
                             exp["last_numeric_cell_hex"])
            age = next(v for v in parsed["variables"] if v["name"] == "AGE")
            self.assertEqual(age["nonmissing_count"], 1)
            self.assertEqual(age["missing_count"], 3)
            self.assertTrue(any(v != 0 for v in age["observed_values"]))
            old = load(ROOT / "artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/expected.json")
            self.assertEqual(old["facts"]["DM"]["row_count"], exp["original_C01_expected_row_count"])

    def build_model(self, context=None, extra_sources=None):
        path = BASE_CONTEXT
        provenance = {"TEST-BASELINE-MANUFACTURE-001": BASE_SOURCE}
        if context is not None:
            path = self.temp / ("context-" + str(len(list(self.temp.glob("context-*.json")))) + ".json")
            write(path, context)
        for sid, source_bytes in (extra_sources or {}).items():
            source_path = self.temp / (sid + ".json")
            source_path.write_bytes(source_bytes)
            provenance[sid] = source_path
        return reconcile(BASELINE / "input-manifest.json", context_path=path,
                         provenance_paths=provenance, test_mode=True, config={"encoding": "ascii"})

    def patch_setup(self, model):
        issue = next(i for i in model["issues"] if i["object_id"].endswith("/DM/variable/SEX")
                     and i["field_path"] == "label")
        dep = model["dependency_snapshot"]
        patch = {"decision_id": "TEST-RC-DECISION", "issue_ids": [issue["issue_id"]],
                 "object_id": issue["object_id"], "field_path": "label",
                 "selected_value": "Biological Sex", "rationale": "isolated test only",
                 "reviewer": "TEST_INDEPENDENT_REVIEWER", "decided_at": "2026-10-21T00:00:00+08:00",
                 "dependency_snapshot_id": dep["dependency_snapshot_id"], "validity_status": "candidate",
                 "supersedes": None, "authorization_status": "synthetic_only"}
        registered = next(s for s in model["sources"] if s["source_id"] == "TEST-BASELINE-MANUFACTURE-001")
        authorization = {"authorization_id": "TEST-RC-AUTH", "reviewer": patch["reviewer"],
                         "source_id": registered["source_id"], "source_sha256": registered["sha256"],
                         "test_only": True,
                         "scope": {k: patch[k] for k in ["object_id", "field_path", "selected_value", "dependency_snapshot_id"]}}
        model["downstream_records"] = [
            {"record_id": "TEST-VALIDATION-RC", "test_only": True, "kind": "validation", "status": "passed"},
            {"record_id": "TEST-APPROVAL-RC", "test_only": True, "kind": "approval", "status": "test_simulated"}]
        applied, result = apply_decision(model, patch, dep, authorization, test_mode=True)
        self.assertEqual(result["status"], "test_simulated")
        return applied, patch, authorization

    def execute_dependency(self, case):
        cid = case["case_id"]
        original = self.build_model()
        applied, patch, authorization = self.patch_setup(original)
        old_history = deepcopy(applied["decisions"])
        old_downstream = deepcopy(applied["downstream_records"])
        ctx = load(BASE_CONTEXT)
        raw = (BASELINE / "dm.xpt").read_bytes()
        count = 4 if cid == "M01-RC29" else 3
        encoding = "utf-8" if cid == "M01-RC31" else "ascii"
        d, registry = self.delivery(raw, "DM", count, encoding, cid)
        ctx["declarations"][0] = d
        extra = {sid: entry["bytes"] for sid, entry in registry.items()}
        current = self.build_model(ctx, extra)
        prev_dep, new_dep = original["dependency_snapshot"], current["dependency_snapshot"]
        self.assertEqual(prev_dep["inputs"]["SRC-DM"]["sha256"], new_dep["inputs"]["SRC-DM"]["sha256"])
        self.assertNotEqual(prev_dep["dependency_snapshot_id"], new_dep["dependency_snapshot_id"])
        self.assertNotEqual(prev_dep["inputs"]["READ-CONTEXT"]["sha256"], new_dep["inputs"]["READ-CONTEXT"]["sha256"])
        self.assertIn(d["provenance"]["source_id"], new_dep["inputs"])
        self.assertEqual(new_dep["inputs"][d["provenance"]["source_id"]]["sha256"], d["provenance"]["source_sha256"])
        if cid == "M01-RC31":
            self.assertIn("utf-8", json.dumps(new_dep), "Effective encoding must be recoverably recorded, not merely hashed.")
        current["decisions"] = deepcopy(old_history)
        current["downstream_records"] = deepcopy(old_downstream)
        changed, result = apply_decision(current, patch, prev_dep, authorization, test_mode=True)
        self.assertEqual(result["status"], case["expected"]["decision_validity"])
        self.assertEqual(result["business_changes"], 0)
        self.assertTrue(result["impact"]["requires_business_rereview"])
        self.assertEqual(changed["decisions"], old_history)
        self.assertEqual(changed["downstream_records"], old_downstream)
        self.assertEqual({r["record_id"]: r["status"] for r in changed["downstream_applicability"]},
                         {r["record_id"]: "needs_review" for r in old_downstream})
        obj = next(o for o in changed["objects"] if o["object_id"] == patch["object_id"])
        self.assertFalse(obj["approved"])
        self.assertFalse(any(a["assertion_kind"] == "approved" for a in changed["assertions"]))
        impact = changed["impact_records"][-1]
        self.assertEqual(impact["downstream_validation_and_approval"], "needs_review")

    def execute_stable(self, case):
        first, second = self.build_model(), self.build_model()
        self.assertEqual(first["model_snapshot_id"], second["model_snapshot_id"])
        for kind, key in [("objects", "object_id"), ("evidence", "evidence_id")]:
            self.assertEqual([x[key] for x in first[kind]], [x[key] for x in second[kind]])
        self.assertEqual(first["dependency_snapshot"], second["dependency_snapshot"])
        first["audit"], second["audit"] = {"started_at": "first"}, {"started_at": "second"}
        self.assertEqual(business_digest(first), business_digest(second))
        applied, patch, auth = self.patch_setup(first)
        altered_dep = deepcopy(first["dependency_snapshot"])
        altered_dep["audit"] = {"started_at": "third"}
        self.assertFalse(compare_dependencies(first["dependency_snapshot"], altered_dep)["requires_business_rereview"])
        rerun, result = apply_decision(applied, patch, altered_dep, auth, test_mode=True)
        self.assertEqual(result["business_changes"], 0)
        self.assertEqual(result["status"], "test_simulated")
        self.assertEqual(applied["decisions"], rerun["decisions"])
        self.assertEqual(next(o for o in first["objects"] if o["kind"] == "dataset" and o["dataset"] == "DM")["observed"]["row_count"], case["expected"]["row_count"])

    def run_case(self, case):
        cid = case["case_id"]
        if cid in {"M01-RC29", "M01-RC30", "M01-RC31"}:
            return self.execute_dependency(case)
        if cid == "M01-RC32":
            return self.execute_stable(case)
        variants = case.get("independent_mutations", [None])
        for index, variant in enumerate(variants):
            with self.subTest(case_id=cid, branch=index + 1):
                state = self.setup_base(case["base"])
                for mutation in ([variant] if variant is not None else case.get("mutation", [])):
                    self.mutate(state, mutation)
                if case["expected"]["outcome"] == "reject":
                    with self.assertRaises(ContractError) as error:
                        self.execute_read(state, case)
                    codes = {
                        "ambiguous_record_count": {"ambiguous_record_count"},
                        "count_payload_incompatible": {"record_count_incompatible", "provenance_count_mismatch"},
                        "declaration_target_hash_mismatch": {"declaration_target_missing", "declaration_hash_mismatch"},
                        "declaration_target_absent_or_member_mismatch": {"provenance_target_mismatch", "declaration_member_mismatch", "declaration_target_missing"},
                        "provenance_source_unavailable": {"provenance_source_missing", "provenance_file_missing", "provided_file_missing"},
                        "provenance_hash_mismatch": {"provenance_hash_mismatch"},
                        "test_context_in_ordinary_mode": {"test_context_forbidden"},
                        "invalid_record_count_type": {"invalid_integer"},
                        "invalid_record_count_type_or_range": {"invalid_integer"},
                        "duplicate_declaration_id_or_target": {"duplicate_declaration_id", "duplicate_declaration_target"},
                        "duplicate_declaration_target": {"duplicate_declaration_target"},
                        "conflicting_declaration_target": {"duplicate_declaration_target"},
                        "read_context_scope_mismatch": {"context_identity_mismatch"},
                        "missing_encoding": {"invalid_declaration", "encoding_required"},
                        "unsupported_codec_or_decode_error": {"unsupported_encoding", "decode_error", "provenance_encoding_mismatch"},
                        "invalid_padding": {"record_count_incompatible", "invalid_padding"},
                    }
                    self.assertIn(error.exception.code, codes[case["expected"]["reason"]],
                                  "An unrelated ContractError must not make a rejection test pass.")
                    if cid in {"M01-RC05", "M01-RC06", "M01-RC10"}:
                        # A provenance contradiction is independently invalid;
                        # additionally prove actual bytes reject this count.
                        with self.assertRaises(ContractError) as physical_error:
                            read_xpt(state["raw"], encoding="ascii",
                                     declaration=state["context"]["declarations"][0], allow_values=True)
                        self.assertEqual(physical_error.exception.code, "record_count_incompatible")
                    if cid == "M01-RC26" and variant["value"] == "ascii":
                        with self.assertRaises(ContractError) as decode_error:
                            read_xpt(state["raw"], encoding="ascii", allow_values=True)
                        self.assertEqual(decode_error.exception.code, "decode_error")
                else:
                    self.assert_success(self.execute_read(state, case), case, state["raw"])


def _test_case(case):
    def execute(self):
        self.run_case(case)
    execute.__name__ = "test_" + case["case_id"].replace("-", "_")
    execute.__doc__ = case["title"]
    execute.case_id = case["case_id"]
    return execute


for _case in FIXED["cases"]:
    setattr(ReadContextCases, "test_" + _case["case_id"].replace("-", "_"), _test_case(_case))


if __name__ == "__main__":
    unittest.main()
