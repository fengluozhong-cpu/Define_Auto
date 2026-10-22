"""24 approved baseline cases. Assertions consume frozen expected values."""
from copy import deepcopy
import unittest

from define_auto.common import ContractError, canonical, load, object_id
from define_auto.decisions import apply_decision, compare_dependencies
from define_auto.model import business_digest
from tests.support import BASE, PACKAGE, baseline, obj, issue, patch_context

EXPECTED = {c["id"]: c for c in load(PACKAGE / "expectations/task001/v0.1/expected.json")["cases"]}
ACTUAL = {}


class BaselineTests(unittest.TestCase):
    CASE_IDS = list(EXPECTED)

    @classmethod
    def setUpClass(cls):
        cls.model = baseline()

    def check_case(self, number):
        case_id = f"T001-C{number:02}"
        e = EXPECTED[case_id]["expected"]
        m = deepcopy(self.model)
        if number == 1:
            v = obj(m, "DM", "STUDYID"); o = v["observed"]
            a = dict(object="DM.STUDYID", row_count=obj(m, "DM")["observed"]["row_count"], storage_length=o["storage_length"],
                max_content_length=o["max_content_bytes"], field_conflicts=[i for i in m["issues"] if i["object_id"] == v["object_id"]], approved=v["approved"].get("label"))
        elif number == 2:
            o = obj(m, "AE")["observed"]
            a = {k: o[k] for k in ["provision_status", "row_count", "no_data_reason", "has_no_data"]}
            a.update(object="AE", category=issue(m, "AE", None)["category"])
        elif number == 3:
            o = obj(m, "CM")["observed"]
            a = {k: o[k] for k in ["provision_status", "read_status", "row_count", "variables", "no_data_reason"]}; a["object"] = "CM"
        elif number == 4:
            o = obj(m, "VS")["observed"]; vs = [v["observed"] for v in m["objects"] if v["dataset"] == "VS" and v["kind"] == "variable"]
            self.assertEqual(len(vs), 5)
            self.assertTrue(all(v["observed_status"] == "unknown" and v["missing_count"] == v["nonmissing_count"] == 0 for v in vs))
            a = dict(object="VS", observed_status=o["observed_status"], row_count=o["row_count"], variable_status=vs[0]["observed_status"],
                per_variable_missing_count=vs[0]["missing_count"], per_variable_nonmissing_count=vs[0]["nonmissing_count"], no_data_reason=o["no_data_reason"])
        elif number == 5:
            v = obj(m, "DM", "ARM")["observed"]
            a = dict(object="DM.ARM", category=issue(m, "DM", "ARM")["category"], **{k: v[k] for k in ["observed_status", "missing_count", "has_no_data"]})
        elif number in (6, 7):
            vn = "SEX" if number == 6 else "AGE"; v = obj(m, "DM", vn)["observed"]
            keys = ["observed_status", "missing_count", "nonmissing_count"] + (["observed_values", "no_data_reason"] if number == 6 else [])
            a = {k: v[k] for k in keys}; a["object"] = "DM." + vn
            if number == 7:
                a["missing_code_counts"] = {k if k == "." else k[1:]: value for k, value in v["missing_code_counts"].items()}
        elif number in (8, 9, 10, 11):
            vn = "SEX" if number in (8, 9) else "ARMCD"
            field = {8: "label", 9: "storage_vs_declared_length", 10: "type", 11: "label"}[number]
            i = issue(m, "DM", vn, field)
            a = dict(object="DM." + vn, field=field, category=i["category"], expected=i["candidates"][0]["value"], observed=i["candidates"][1]["value"])
            if "status" in e: a["status"] = i["status"]
            if "approved" in e: a["approved"] = obj(m, "DM", vn)["approved"].get(field)
            if number == 9: a["observed_content_length"] = obj(m, "DM", vn)["observed"]["max_content_bytes"]
        elif number == 12:
            i = issue(m, "DM", "EXTRA")
            a = dict(object="DM.EXTRA", category=i["category"], status=i["status"], approved=obj(m, "DM", "EXTRA")["approved"].get("label"))
        elif number == 13:
            m, p, auth = patch_context(m); dep = deepcopy(m["dependency_snapshot"])
            first, r1 = apply_decision(m, p, dep, auth, test_mode=True)
            second, r2 = apply_decision(first, p, dep, auth, test_mode=True)
            self.assertEqual(r1["business_changes"], 1); self.assertEqual(business_digest(first), business_digest(second))
            a = dict(simulation_unique_decisions=len(second["decisions"]), second_application_business_changes=r2["business_changes"],
                     real_approved_assertion=any(x["assertion_kind"] == "approved" for x in second["assertions"]))
        elif 14 <= number <= 20:
            scenario = load(BASE / "dependency-changes.json")["changes"][number - 14]
            m, p, auth = patch_context(m); dep = deepcopy(m["dependency_snapshot"])
            prior, _ = apply_decision(m, p, dep, auth, test_mode=True)
            prior["downstream_records"] = [{"record_id": "TEST-VALIDATION", "status": "passed"}, {"record_id": "TEST-APPROVAL", "status": "test_simulated", "test_only": True}]
            before = canonical(prior["decisions"])
            changed = deepcopy(prior)
            changed["dependency_snapshot"][scenario["component"]] = scenario["replacement"]
            stale, result = apply_decision(changed, p, dep, auth, test_mode=True)
            self.assertEqual(result["business_changes"], 0)
            self.assertTrue(all(r["status"] == "needs_review" for r in stale["downstream_applicability"]))
            self.assertEqual(canonical(stale["decisions"]), before)
            a = dict(scenario=scenario["id"], patch=result["status"], downstream_validation_and_approval=stale["impact_records"][-1]["downstream_validation_and_approval"])
            if number == 14: a["old_records_retained"] = stale["impact_records"][-1]["old_records_retained"]
        elif number == 21:
            d = deepcopy(m["dependency_snapshot"]); d["audit"] = {"run_started_at": "2000-01-02T00:00:00Z"}
            impact = compare_dependencies(m["dependency_snapshot"], d)
            m2 = deepcopy(m); m2["audit"] = {"time": "different"}
            a = dict(scenario="P-AUDIT", business_identity_changed=business_digest(m) != business_digest(m2),
                     requires_business_rereview=impact["requires_business_rereview"], impact_record_required=bool(impact["basis"]))
        elif number == 22:
            m, p, auth = patch_context(m); dep = deepcopy(m["dependency_snapshot"])
            prior, _ = apply_decision(m, p, dep, auth, test_mode=True); before = canonical(prior)
            changed = deepcopy(p); changed.update(e["mutate"])
            with self.assertRaises(ContractError) as caught:
                apply_decision(prior, changed, dep, auth, test_mode=True)
            a = dict(mutate=e["mutate"], result=caught.exception.code, old_record_retained=canonical(prior) == before)
        elif number == 23:
            a = dict(reference_state=m["reference_state"], submission_readiness=m["submission_readiness"],
                     invented_nci_codes=any("nci_code" in a for a in m["assertions"]))
        else:
            k = object_id("SYN001", "SDTM", "DM", "SEX")
            rerun = baseline()
            a = dict(same_name_cross_family_equal=k == object_id("SYN001", "ADAM", "DM", "SEX"),
                     same_name_cross_study_equal=k == object_id("OTHER", "SDTM", "DM", "SEX"),
                     input_order_changes_identity={o["object_id"] for o in m["objects"]} != {o["object_id"] for o in rerun["objects"]})
        ACTUAL[case_id] = a
        self.assertEqual(a, e)


for _number in range(1, 25):
    setattr(BaselineTests, f"test_T001_C{_number:02}", lambda self, n=_number: self.check_case(n))
