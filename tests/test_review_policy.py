"""Forty independently frozen CARD-01..06 scenarios, through actual runtime paths."""
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest

from define_auto.common import ContractError, canonical, load, sha, write
from define_auto.decisions import apply_decision, resume_model, compare_dependencies
from define_auto.engine import reconcile
from define_auto.model import business_digest, dependency_digest, validate_model
from define_auto.reporting import markdown, html_report
from define_auto.review import apply_review_action, project_review, reuse_offer
from tests.support import ROOT, BASE, CONTEXT, PROVENANCE, baseline, obj, issue, patch_context, workspace

EXPECTED_PATH = ROOT / "expectations/mvp01/v0.3/review-policy-cases.json"
EXPECTED_HASH = "0e36a52f457072f624f094ffd426e8a7357bcf9fb22df75c3299043fd418fdf0"
FIXED = load(EXPECTED_PATH)
ACTUAL = {}


def delivery(folder, *, test=True, extra=False, change=None, rules=None):
    """Construct fresh synthetic delivery declarations, never promote test approvals."""
    folder.mkdir(parents=True, exist_ok=False)
    manifest = load(BASE / "input-manifest.json")
    context = {"schema_version": "mvp01-read-context-0.1", "study_id": "SYN001", "family": "SDTM",
               "test_only": test, "declarations": []}
    stated = []
    for source in manifest["sources"]:
        if source["provision_status"] != "provided":
            continue
        raw = (BASE / source["relative_path"]).read_bytes()
        ds = source["completeness_scope"].get("datasets", [None])[0] if source["source_type"] == "xpt" else None
        if ds == "DM" and change in {"timestamp", "candidate", "partial", "zero"}:
            b = bytearray(raw)
            if change == "timestamp":
                b[160:176] = b"22OCT26:00:00:00"
            elif change == "candidate":
                b[640 + 3 * 140 + 16:640 + 3 * 140 + 56] = b"Gender".ljust(40)
            else:
                # Literal independently known 34-byte DM rows; AGE at byte 17.
                b[1760 + 17:1760 + 25] = bytes(8)  # SAS numeric zero is nonmissing.
                b[640 + 4 * 140 + 8:640 + 4 * 140 + 16] = b"TEST".ljust(8)
                if change == "zero":
                    b = b[:1760] + b[1760:1760 + 34] + b" " * 46
            raw = bytes(b)
        if ds == "VS" and change == "vs_data":
            from define_auto.xpt import read_xpt
            parsed = read_xpt(raw, encoding="ascii", declaration={**load(CONTEXT)["declarations"][1]})
            row = b"".join(b"A".ljust(v["storage_length"]) if v["type"] == "character" else bytes(v["storage_length"])
                           for v in parsed["variables"])
            raw += row.ljust(((len(row) + 79) // 80) * 80, b" ")
        if ds == "DM" and change == "flag":
            header = bytearray(raw[:640]); header[614:618] = b"0001"
            descriptor = bytearray(raw[640 + 3 * 140:640 + 4 * 140])
            descriptor[4:8] = b"\x00\x02\x00\x01"  # storage=2, ordinal=1
            descriptor[8:16] = b"TESTFL  "; descriptor[16:56] = b"Synthetic Flag".ljust(40)
            descriptor[84:88] = bytes(4)
            raw = bytes(header) + bytes(descriptor) + b" " * 20 + raw[1680:1760] + b"Y " + b" " * 78
        if source["source_type"] == "structured_spec" and (extra or change in {"partial", "zero", "flag"}):
            from define_auto.common import strict_json
            spec = strict_json(raw.decode("utf-8"))
            dm = next(d for d in spec["datasets"] if d["name"] == "DM")
            if extra:
                dm["variables"].append({"name": "EXTRA", "label": "Synthetic Extra", "type": "character", "declared_length": 1})
            if change in {"partial", "zero"}:
                next(v for v in dm["variables"] if v["name"] == "AGE")["name"] = "TEST"
            if change == "flag":
                dm["variables"] = [{"name": "TESTFL", "label": "Synthetic Flag", "type": "character", "declared_length": 2}]
            raw = canonical(spec)
        (folder / source["relative_path"]).write_bytes(raw)
        source["sha256"] = sha(raw)
        if ds in {"DM", "VS"}:
            stated.append({"member": ds, "source_sha256": sha(raw), "record_count": (1 if change in {"zero", "flag"} else 3) if ds == "DM" else int(change == "vs_data"), "encoding": "ascii"})
    document = {"synthetic_boundary_fixture": True, "identity_authenticity": "not_independently_verified", "declarations": stated}
    provenance = folder / "delivery.json"; write(provenance, document)
    for index, row in enumerate(stated):
        context["declarations"].append({**row, "declaration_id": "SYN-BOUNDARY-" + row["member"],
             "provided_by": "synthetic_boundary_delivery_constructor", "provenance": {
                 "source_id": "SYN-DELIVERY", "source_sha256": sha(provenance.read_bytes()), "locator": "/declarations/" + str(index)}})
    write(folder / "manifest.json", manifest); write(folder / "context.json", context)
    flags = ["--manifest", str(folder / "manifest.json"), "--read-context", str(folder / "context.json"),
             "--provenance", "SYN-DELIVERY=" + str(provenance)] + (["--isolated-test"] if test else [])
    if rules:
        write(folder / "rules.json", rules); flags += ["--review-rules", str(folder / "rules.json")]
    model = reconcile(folder / "manifest.json", context_path=folder / "context.json", provenance_paths={"SYN-DELIVERY": provenance},
                      test_mode=test, review_rules_path=folder / "rules.json" if rules else None)
    return model, flags


def action_for(model, kind="confirm_no_data", target="VS", value="合成原因", identifier="SYN-ACTION-1", supersedes=None):
    parts = target.split(".")
    return {"action_id": identifier, "kind": kind, "object_id": obj(model, *parts)["object_id"],
            "reviewer": "synthetic_boundary_reviewer", "decided_at": "2026-10-22T10:00:00+08:00",
            "rationale": "独立合成场景，明确人工审阅范围", "dependency_snapshot_id": model["dependency_snapshot"]["dependency_snapshot_id"],
            "supersedes": supersedes, "value": value}


def authorize(model, action, *, test=None):
    model = deepcopy(model)
    record = {"authorization_id": "SYN-AUTH-" + action["action_id"], "reviewer": action["reviewer"],
              "test_only": model["test_only"] if test is None else test, "scope": deepcopy(action)}
    raw = canonical(record); sid = "SYN-AUTH-SOURCE-" + sha(raw)
    if not any(s["source_id"] == sid for s in model["sources"]):
        model["sources"].append({"source_id": sid, "relative_path": "synthetic-authorization.json", "sha256": sha(raw),
            "source_type": "authorization", "version": "sha256:" + sha(raw), "acquired_at": "synthetic",
            "confidentiality": "fully_synthetic", "completeness_scope": {"synthetic_boundary_fixture": True},
            "provision_status": "provided", "read_status": "readable"})
    record.update(source_id=sid, source_sha256=sha(raw))
    return model, record


def nd(model, target):
    oid = obj(model, *target.split("."))["object_id"]
    return next((e for e in model["review_policy"]["no_data"] if e["object_id"] == oid), {})


def rulebook(model, kind="type", target="DM.ARMCD", value="character", ig="TEST-IG-1"):
    return {"schema_version": "mvp01-review-rules-0.1", "version": "TEST-LOCAL-1", "ig_version": ig,
            "ct_version": "TEST-CT-1", "test_only": True, "source_id": "SYN-LOCAL-RULES",
            "rules": [{"rule_id": "TEST-" + kind, "object_id": obj(model, *target.split("."))["object_id"],
                       "kind": kind, "value": value, "locator": "/rules/0; synthetic independent rule declaration"}]}


class ReviewPolicyCases(unittest.TestCase):
    def setUp(self):
        self.assertEqual(sha(EXPECTED_PATH.read_bytes()), EXPECTED_HASH)
        self.tmp = workspace(); self.addCleanup(self.tmp.cleanup); self.folder = Path(self.tmp.name)

    def confirm(self, model, action):
        model, auth = authorize(model, action)
        return apply_review_action(model, action, auth, test_mode=model["test_only"])

    def rejected(self, model, action, auth=None, mode=None):
        before = canonical(model)
        with self.assertRaises(ContractError):
            apply_review_action(model, action, auth, test_mode=model["test_only"] if mode is None else mode)
        self.assertEqual(canonical(model), before)
        return {"accepted": False, "business_state_unchanged": canonical(model) == before}

    def prior_current(self, *, test=True, change="timestamp"):
        prior, _ = delivery(self.folder / "old", test=test)
        prior, patch, auth = patch_context(prior)
        patch["selected_value"] = "Sex"
        auth["scope"]["selected_value"] = "Sex"
        if not test:
            patch["authorization_status"] = "authorized"; auth["test_only"] = False
        prior, _ = apply_decision(prior, patch, prior["dependency_snapshot"], auth, test_mode=test)
        prior["downstream_records"] = [{"record_id": "SYN-VALIDATION", "status": "passed"},
                                       {"record_id": "SYN-APPROVAL", "status": "test_simulated" if test else "draft"}]
        prior["model_snapshot_id"] = business_digest(prior)
        current, _ = delivery(self.folder / "current", test=test, change=change)
        current = resume_model(current, prior)
        return prior, current, patch

    def run_case(self, number):
        c = FIXED["cases"][number - 1]; expected = c["expected"]
        m = baseline()
        if number in (1, 2, 6):
            target = c["scenario"]["object"]; o = obj(m, *target.split(".")); p = nd(m, target)
            state = o["observed"].get("provision_status") if number == 1 else o["observed"].get("read_status") if number == 2 else issue(m, "DM", "ARM")["category"]
            actual = {"observed_state": state, "has_no_data": p.get("has_no_data"),
                      "manual_confirmation_required": any(e["object_id"] == o["object_id"] for e in m["review_policy"]["manual_confirmation"]),
                      "approved": bool(o["approved"])}
            if number != 6: actual["reason"] = p.get("reason")
        elif number in (3, 4, 5):
            target = c["scenario"]["object"]; p = nd(m, target); o = obj(m, *target.split("."))
            actual = {k: p[k] for k in ("has_no_data", "confirmation", "reason")}; actual["approved"] = bool(o["approved"])
            if number == 3:
                actual.update(row_count=o["observed"]["row_count"], human_confirmation_required=p["confirmation"] == "pending", xml_comment_required=p["xml_comment_required"])
            else:
                actual.update(parent_row_count=obj(m, "DM")["observed"]["row_count"], missing_count=o["observed"]["missing_count"])
                if number == 5: actual["special_missing_counts"] = o["observed"]["missing_code_counts"]
        elif number == 7:
            vs = [o for o in m["objects"] if o["dataset"] == "VS" and o["kind"] == "variable"]
            self.assertEqual(len(vs), 5)
            self.assertTrue(all(not nd(m, "VS." + o["variable"]) for o in vs))
            self.assertTrue(all(o["observed"]["observed_status"] == "unknown" for o in vs))
            actual = {"each_variable_has_no_data": None, "each_variable_observed_state": "unknown", "dataset_has_no_data": nd(m, "VS")["has_no_data"]}
        elif number in (8, 9):
            m, _ = delivery(self.folder / "variant", change="partial" if number == 8 else "zero")
            observed = obj(m, "DM", "TEST")["observed"]
            self.assertEqual((observed["missing_count"], observed["nonmissing_count"]), (2, 1) if number == 8 else (0, 1))
            self.assertEqual(obj(m, "DM")["observed"]["row_count"], 3 if number == 8 else 1)
            self.assertEqual(observed["observed_values"], [0])
            actual = {"has_no_data": nd(m, "DM.TEST").get("has_no_data"), "reason": nd(m, "DM.TEST").get("reason")}
        elif number == 10:
            again = project_review(project_review(m)); entries = again["review_policy"]["no_data"]
            actual = {"old_observed_has_no_data": obj(again, "VS")["observed"]["has_no_data"],
                      "old_observed_no_data_reason": obj(again, "VS")["observed"]["no_data_reason"],
                      "old_approved_unchanged": [o["approved"] for o in m["objects"]] == [o["approved"] for o in again["objects"]],
                      "policy_equal": m["review_policy"] == again["review_policy"],
                      "duplicate_entries": len(entries) - len({e["object_id"] for e in entries})}
        elif number in (11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21):
            test = number in (17, 18, 19, 20)
            m, _ = delivery(self.folder / "action-input", test=test)
            scenario = c["scenario"]; target = scenario.get("object", "VS")
            a = action_for(m, target=target, value=scenario.get("reason", scenario.get("old_reason", "合成原因")))
            m, auth = authorize(m, a)
            if number == 14: auth = None
            if number == 15: auth["scope"]["object_id"] = obj(m, "DM", "AGE")["object_id"]
            if number == 16: a["dependency_snapshot_id"] = "dep-previous"; m, auth = authorize(m, a)
            if number in (13, 14, 15, 16, 18):
                actual = self.rejected(m, a, auth, mode=False if number == 18 else None)
            else:
                first, result = apply_review_action(m, a, auth, test_mode=test)
                if number in (11, 12):
                    p = nd(first, target); actual = {"accepted": result["business_changes"] == 1, "confirmation": p["confirmation"],
                        "reason": p["reason"], "xml_target": p["xml_target"], "final_delivery_approved": first["review_policy"]["final_delivery_approved"]}
                    if number == 11: actual["new_decision_count"] = len(first["review_actions"])
                elif number == 17:
                    actual = {"accepted": True, "confirmation": nd(first, "VS")["confirmation"],
                        "real_approved_count": sum(bool(o["approved"]) for o in first["objects"]), "final_delivery_approved": first["review_policy"]["final_delivery_approved"]}
                elif number == 19:
                    again, result = apply_review_action(first, a, auth, test_mode=test)
                    self.assertEqual(canonical(again), canonical(first))
                    actual = {"second_business_changes": result["business_changes"], "new_decision_count_total": len(again["review_actions"]),
                              "history_duplicates": len(again["review_actions"]) - len({r["action"]["action_id"] for r in again["review_actions"]})}
                elif number == 20:
                    before = canonical(first["review_actions"]); b = {**a, "value": "变更原因"}; first, other = authorize(first, b)
                    actual = self.rejected(first, b, other); actual["old_history_unchanged"] = canonical(first["review_actions"]) == before
                else:
                    b = action_for(first, value=scenario["new_reason"], identifier="SYN-ACTION-2", supersedes=a["action_id"])
                    second, _ = self.confirm(first, b)
                    actual = {"accepted": True, "current_reason": nd(second, "VS")["reason"],
                        "old_reason_preserved": second["review_actions"][0]["action"]["value"], "history_count": len(second["review_actions"]),
                        "new_links_old": second["review_actions"][1]["action"]["supersedes"] == a["action_id"]}
        elif number in (22, 23):
            raw = (BASE / "dm.xpt").read_bytes()
            if number == 23:
                a = action_for(m, kind="return_upstream", target="DM.EXTRA", value=[issue(m, "DM", "EXTRA")["issue_id"]])
                m, result = self.confirm(m, a)
            work = next(e for e in m["review_policy"]["upstream_rework"] if e["object_id"] == obj(m, "DM", "EXTRA")["object_id"])
            actual = {"workflow": work["workflow"], "blocking": work["blocking"], "source_bytes_unchanged": raw == (BASE / "dm.xpt").read_bytes()}
            if number == 22: actual["approved"] = bool(obj(m, "DM", "EXTRA")["approved"])
            else: actual.update(accepted=result["business_changes"] == 1, issue_resolved=issue(m, "DM", "EXTRA")["status"] == "resolved")
        elif number == 24:
            prior, _ = delivery(self.folder / "old")
            prior["downstream_records"] = [{"record_id": "SYN-VALIDATION", "status": "passed"}]
            current, _ = delivery(self.folder / "new", extra=True); current = resume_model(current, prior)
            actual = {"extra_object_issue_present": any(i["object_id"] == obj(current, "DM", "EXTRA")["object_id"] and i["category"] == "unexpected_object" for i in current["issues"]),
                "old_run_extra_issue_preserved": issue(prior, "DM", "EXTRA")["category"] == "unexpected_object",
                "new_dependency_snapshot": current["dependency_snapshot"] != prior["dependency_snapshot"],
                "old_validation_reused": current["downstream_applicability"][0]["status"] == "passed"}
        elif number == 25:
            p = m["review_policy"]; actual = {"standard_check": p["standard_check"], "standard_conformance_claim": p["standard_conformance"] != "not_assessed", "p21_check": p["p21_check"]}
        elif number in (26, 27, 28, 29):
            if number == 27:
                m, _ = delivery(self.folder / "flag-baseline", change="flag")
            kind = {26: "type", 27: "flag_length", 28: "label_semantic", 29: "type"}[number]
            target = "DM.ARMCD" if number in (26, 29) else "DM.TESTFL" if number == 27 else "DM.SEX"
            book = rulebook(m, kind, target, 1 if number == 27 else "Biological Sex" if number == 28 else "character")
            if number == 29:
                results = []
                for index, field in enumerate(("version", "locator")):
                    with self.subTest(variant=field):
                        broken = deepcopy(book)
                        if field == "version": broken.pop(field)
                        else: broken["rules"][0].pop(field)
                        with self.assertRaises(ContractError): delivery(self.folder / ("bad-rule-" + str(index)), rules=broken)
                        results.append({"standard_conformance_claim": False, "false_standard_pass": False})
                self.assertEqual(len(results), 2); actual = results[0]
            else:
                m, _ = delivery(self.folder / "rules", rules=book, change="flag" if number == 27 else None)
                findings = m["review_policy"]["rule_findings"]
                if number == 28:
                    actual = {"exact_text_mismatch_is_standard_error": any(f["result"] == "failed" for f in findings),
                        "project_conflict_retained": issue(m, "DM", "SEX", "label")["category"] == "field_conflict",
                        "semantic_equivalence_not_auto_approved": not obj(m, "DM", "SEX")["approved"]}
                else:
                    work = next(e for e in m["review_policy"]["upstream_rework"] if e.get("rule_id") == book["rules"][0]["rule_id"])
                    actual = {"workflow": work["workflow"], "blocking": work["blocking"], "rule_evidence_present": bool(findings[0]["source_sha256"] and findings[0]["locator"])}
                    if number == 26:
                        bm, patch, auth = patch_context(m); patch["object_id"] = obj(m, "DM", "ARMCD")["object_id"]; patch["field_path"] = "type"
                        patch["issue_ids"] = [issue(m, "DM", "ARMCD", "type")["issue_id"]]; patch["selected_value"] = "character"
                        auth["scope"] = {k: patch[k] for k in ["object_id", "field_path", "selected_value", "dependency_snapshot_id"]}
                        with self.assertRaises(ContractError): apply_decision(bm, patch, bm["dependency_snapshot"], auth, test_mode=True)
                        actual.update(selected_define_value_can_close=False, real_standard_conformance_claim=m["review_policy"]["standard_conformance"] != "not_assessed")
                    else:
                        self.assertEqual(obj(m, "DM", "TESTFL")["observed"]["storage_length"], 2)
                        actual["observed_max_length_cannot_override"] = findings[0]["result"] == "failed" and obj(m, "DM", "TESTFL")["observed"]["max_content_bytes"] == 1
        elif number in (30, 31, 32, 33, 35, 36, 37, 38):
            prior, current, patch = self.prior_current(test=number != 31, change="candidate" if number == 33 else "timestamp")
            before = canonical(prior["decisions"]); offer = reuse_offer(current, prior["decisions"][0])
            if number == 30:
                actual = {"decision_applicability": current["impact_records"][-1]["downstream_validation_and_approval"],
                    "old_decision_unchanged": canonical(current["decisions"]) == before,
                    "downstream_validation_applicability": current["downstream_applicability"][0]["status"],
                    "downstream_approval_applicability": current["downstream_applicability"][1]["status"], "unattended_reuse": bool(obj(current, "DM", "SEX")["approved"] or obj(current, "DM", "SEX").get("simulated_selection"))}
            elif number in (31, 32, 33, 38):
                a = action_for(current, kind="confirm_reuse", target="DM.SEX", value=patch["decision_id"])
                current, auth = authorize(current, a)
                if number in (32, 33):
                    if number == 32: auth = None
                    self.rejected(current, a, auth)
                    actual = {"accepted": False, "old_history_unchanged": canonical(current["decisions"]) == before}
                    if number == 32: actual["decision_applicability"] = current["downstream_applicability"][0]["status"]
                    else: actual["current_approved_value_absent"] = not obj(current, "DM", "SEX")["approved"]
                else:
                    current, _ = apply_review_action(current, a, auth, test_mode=current["test_only"])
                    actual = {"accepted": True, "old_validation_reused": any(r["status"] == "passed" for r in current["downstream_applicability"]),
                              "final_delivery_approved": current["review_policy"]["final_delivery_approved"]}
                    if number == 31:
                        latest = current["decisions"][-1]["patch"]
                        actual.update(new_decision_links_old=latest["supersedes"] == patch["decision_id"],
                            new_decision_uses_current_dependency=latest["dependency_snapshot_id"] == current["dependency_snapshot"]["dependency_snapshot_id"],
                            old_decision_unchanged=canonical(current["decisions"][:1]) == before)
                    else: actual["real_approved_count"] = sum(bool(o["approved"]) for o in current["objects"])
            elif number == 35:
                for variant in ("spec_hash_changed", "derivation_rules_changed"):
                    with self.subTest(variant=variant):
                        changed = deepcopy(current)
                        if variant == "spec_hash_changed":
                            sid = next(s["source_id"] for s in changed["sources"] if s["source_type"] == "structured_spec")
                            changed["dependency_snapshot"]["inputs"][sid]["sha256"] = "0" * 64
                        else: changed["dependency_snapshot"]["rules"]["version"] = "changed"
                        p = reuse_offer(changed, prior["decisions"][0]); self.assertFalse(p["eligible"])
                        self.assertTrue(p["changed_components"])
                actual = {"eligible_for_xpt_only_reuse": p["eligible"], "needs_review": bool(p["changed_components"]), "unattended_reuse": p["unattended_reuse"]}
            elif number == 36:
                current["dependency_snapshot"]["standards"]["ct"] = "changed-CT"
                p = reuse_offer(current, prior["decisions"][0])
                actual = {"other_change_displayed": "standards" in p["other_changed_dependencies"], "unattended_reuse": p["unattended_reuse"],
                    "old_validation_reused": any(r["status"] == "passed" for r in current["downstream_applicability"])}
            else:
                again = deepcopy(prior); again["dependency_snapshot"]["audit"] = {"time": "new"}; again["audit"] = {"time": "new"}
                same = resume_model(again, prior)
                actual = {"business_digest_unchanged": business_digest(prior) == business_digest(same),
                    "dependency_changes": compare_dependencies(prior["dependency_snapshot"], same["dependency_snapshot"])["changed_components"],
                    "new_business_review_required": compare_dependencies(prior["dependency_snapshot"], same["dependency_snapshot"])["requires_business_rereview"]}
        elif number == 34:
            prior, _ = delivery(self.folder / "old")
            a = action_for(prior); prior, _ = self.confirm(prior, a)
            current, _ = delivery(self.folder / "current", change="vs_data"); current = resume_model(current, prior)
            b = action_for(current, identifier="new", supersedes=a["action_id"]); current, auth = authorize(current, b)
            self.rejected(current, b, auth)
            actual = {"accepted": False, "current_has_no_data": nd(current, "VS").get("has_no_data"),
                "current_confirmed_reason": nd(current, "VS").get("reason"), "old_reason_preserved_in_history": current["review_actions"][0]["action"]["value"] == a["value"]}
        elif number == 39:
            reports = [markdown(m), html_report(m)]
            actual = {"both_show_pending_no_data_reason": all("待人工确认并补充无数据原因" in r for r in reports),
                "both_show_AE_CM_human_confirmation": all(all(t in r for t in ("AE", "CM", "人工确认输入")) for r in reports),
                "both_show_EXTRA_upstream_rework": all("EXTRA" in r and "返回上游返工" in r for r in reports),
                "both_show_standard_not_completed": all("未完成标准核查" in r for r in reports),
                "same_model_snapshot": all(m["model_snapshot_id"] in r for r in reports),
                "source_bytes_unchanged": sha((BASE / "dm.xpt").read_bytes()) == load(BASE / "input-manifest.json")["sources"][0]["sha256"]}
        else:
            m, flags = delivery(self.folder / "input")
            def run(name, extras):
                result = subprocess.run([sys.executable, "-m", "define_auto", *flags, *extras, "--out", str(self.folder / name)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return load(self.folder / name / "model.json")
            first = run("base", []); a = action_for(first); _, auth = authorize(first, a)
            auth = {k: v for k, v in auth.items() if k not in {"source_id", "source_sha256"}}
            write(self.folder / "action.json", a); write(self.folder / "authorization.json", auth)
            extras = ["--review-action", str(self.folder / "action.json"), "--authorization", str(self.folder / "authorization.json")]
            second = run("confirm", extras); third = run("resume", extras + ["--prior-model", str(self.folder / "confirm/model.json")])
            validate_model(third, sealed=True)
            self.assertEqual(canonical(second), canonical(third), "Identical resumed action must preserve the complete business snapshot.")
            result = subprocess.run([sys.executable, "-m", "define_auto", *flags, "--out", str(self.folder / "base")], cwd=ROOT, capture_output=True)
            actual = {"persisted_policy_matches_report": load(self.folder / "resume/review-policy.json") == third["review_policy"] and "测试模拟" in (self.folder / "resume/review.html").read_text("utf-8"),
                "reload_validates": True, "history_preserved": third["review_actions"] == second["review_actions"],
                "existing_output_rejected": result.returncode != 0, "final_delivery_approved": third["review_policy"]["final_delivery_approved"]}
        ACTUAL[c["case_id"]] = actual
        self.assertEqual(actual, expected)


for _number in range(1, 41):
    def execute(self, number=_number):
        self.run_case(number)
    setattr(ReviewPolicyCases, f"test_M01_RP{_number:02}", execute)
