"""Independent-review failures and boundary regressions beyond frozen RP cases."""
from copy import deepcopy
from pathlib import Path
import unittest

from define_auto.common import ContractError, canonical
from define_auto.decisions import apply_decision
from define_auto.model import validate_model
from define_auto.reporting import markdown, html_report
from define_auto.review import apply_review_action
from tests.support import baseline, issue, obj, patch_context, workspace
from tests.test_review_policy import delivery, rulebook, action_for, authorize


class ReviewRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = workspace(); self.addCleanup(self.tmp.cleanup); self.folder = Path(self.tmp.name)

    def test_unavailable_rule_is_not_pass(self):
        b = rulebook(baseline(), target="DM.ARM")
        m, _ = delivery(self.folder / "input", rules=b)
        finding = m["review_policy"]["rule_findings"][0]
        self.assertEqual(finding["result"], "not_completed")
        self.assertEqual(finding["not_evaluable"], [{"view": "observed", "field": "type"}])
        self.assertEqual(m["review_policy"]["standard_check"], "not_completed")

    def test_manual_return_routes_and_blocks_selection(self):
        m = baseline(); i = issue(m, "DM", "SEX", "label")
        a = action_for(m, kind="return_upstream", target="DM.SEX", value=[i["issue_id"]])
        m, auth = authorize(m, a)
        out, _ = apply_review_action(m, a, auth, test_mode=True)
        self.assertTrue(any(e.get("issue_id") == i["issue_id"] for e in out["review_policy"]["upstream_rework"]))
        for report in (markdown(out), html_report(out)):
            self.assertIn("返回上游返工", report)
        out, patch, patch_auth = patch_context(out)
        with self.assertRaisesRegex(ContractError, "returned_issue_requires_upstream_rework"):
            apply_decision(out, patch, out["dependency_snapshot"], patch_auth, test_mode=True)
        bad = {**a, "value": [[]]}; m, auth = authorize(m, bad)
        before = canonical(m)
        with self.assertRaises(ContractError): apply_review_action(m, bad, auth, test_mode=True)
        self.assertEqual(canonical(m), before)

    def test_rule_label_versions_and_invalid_values(self):
        for index, (ig, accepted) in enumerate((("3.2", True), ("3.3", False))):
            book = rulebook(baseline(), "label_exact", "DM.SEX", "Sex", ig)
            if accepted:
                m, _ = delivery(self.folder / str(index), rules=book)
                self.assertEqual(m["review_policy"]["rule_findings"][0]["result"], "failed")
            else:
                with self.assertRaisesRegex(ContractError, "label_exact_not_applicable"):
                    delivery(self.folder / str(index), rules=book)
        for index, value in enumerate(([], {}, None, True)):
            with self.subTest(value=value):
                book = rulebook(baseline(), value=value)
                with self.assertRaises(ContractError): delivery(self.folder / ("invalid-" + str(index)), rules=book)

    def test_persisted_policy_and_review_history_constraints(self):
        m = baseline(); a = action_for(m); m, auth = authorize(m, a)
        out, _ = apply_review_action(m, a, auth, test_mode=True)
        validate_model(out, sealed=True)
        for mutate in ("reason", "source", "snapshot", "duplicate", "policy"):
            with self.subTest(mutation=mutate):
                bad = deepcopy(out)
                if mutate == "reason": bad["review_actions"][0]["action"]["value"] = "未授权更改"
                if mutate == "source": bad["review_actions"][0]["authorization"]["source_sha256"] = "0" * 64
                if mutate == "snapshot": bad["review_actions"][0]["dependency_snapshot"]["rules"] = {}
                if mutate == "duplicate": bad["review_actions"].append(deepcopy(bad["review_actions"][0]))
                if mutate == "policy": bad["review_policy"]["no_data"][0]["reason"] = "伪造"
                with self.assertRaises(ContractError): validate_model(bad)

    def test_review_time_and_supersedes(self):
        m = baseline()
        for time in ("tomorrow", "2026-10-22T10:00:00"):
            a = action_for(m); a["decided_at"] = time; m, auth = authorize(m, a)
            with self.assertRaises(ContractError): apply_review_action(m, a, auth, test_mode=True)
        a = action_for(m); m, auth = authorize(m, a); first, _ = apply_review_action(m, a, auth, test_mode=True)
        b = action_for(first, identifier="new", value="新原因")
        first, auth = authorize(first, b)
        with self.assertRaisesRegex(ContractError, "review_revision_requires_supersedes"):
            apply_review_action(first, b, auth, test_mode=True)


if __name__ == "__main__":
    unittest.main()
