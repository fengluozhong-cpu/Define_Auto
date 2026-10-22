"""Deterministic review policy, human actions, and explicitly bounded rule checks."""
from copy import deepcopy
import datetime as dt
import re

from .common import canonical, require, stable, text


ACTION_FIELDS = {"action_id", "kind", "object_id", "reviewer", "decided_at", "rationale",
                 "dependency_snapshot_id", "supersedes", "value"}


def _authorized(model, action, auth, test_mode):
    require(isinstance(auth, dict) and type(auth.get("test_only")) is bool, "review_authorization_required")
    for key in ("authorization_id", "reviewer", "source_id", "source_sha256"):
        text(auth.get(key), key)
    require(auth["reviewer"] == action["reviewer"] and canonical(auth.get("scope")) == canonical(action),
            "review_authorization_scope_mismatch")
    require((test_mode and model["test_only"] and auth["test_only"]) or
            (not model["test_only"] and not auth["test_only"]), "review_test_isolation")
    source = next((s for s in model["sources"] if s["source_id"] == auth["source_id"]), None)
    require(source and source["source_type"] == "authorization" and source["read_status"] == "readable"
            and source["sha256"] == auth["source_sha256"], "review_authorization_source_missing")


def _action_shape(action):
    require(isinstance(action, dict) and set(action) == ACTION_FIELDS, "invalid_review_action")
    for key in ACTION_FIELDS - {"supersedes", "value"}:
        text(action[key], key)
    require(action["kind"] in {"confirm_no_data", "return_upstream", "confirm_reuse"}, "unsupported_review_action")
    if action["supersedes"] is not None:
        text(action["supersedes"])
    try:
        moment = dt.datetime.fromisoformat(action["decided_at"])
        require(moment.tzinfo is not None, "review_time_timezone_required")
    except ValueError as exc:
        from .common import ContractError
        raise ContractError("invalid_review_time") from exc


def _no_data(model, obj):
    obs = obj["observed"]
    if obj["expected"] is None:
        return None
    if obj["kind"] == "dataset":
        if obs.get("read_status") == "readable" and obs.get("row_count") == 0:
            return "readable_zero_rows"
    else:
        parent = next(o for o in model["objects"] if o["dataset"] == obj["dataset"] and o["kind"] == "dataset")
        n = parent["observed"].get("row_count")
        if (parent["observed"].get("read_status") == "readable" and type(n) is int and n > 0
                and obs.get("observed_status") == "present_all_missing" and
                obs.get("nonmissing_count") == 0 and obs.get("missing_count") == n):
            return "present_variable_all_missing"
    return None


def rule_findings(model):
    book = model.get("review_rulebook")
    if book is None:
        return []
    require(isinstance(book, dict) and set(book) == {"schema_version", "version", "ig_version", "ct_version",
            "test_only", "source_id", "rules"}, "invalid_review_rulebook")
    require(book["schema_version"] == "mvp01-review-rules-0.1", "unsupported_review_rulebook")
    for k in ("version", "ig_version", "ct_version", "source_id"):
        text(book[k], k)
    require(type(book["test_only"]) is bool and (not book["test_only"] or model["test_only"]), "test_rules_forbidden")
    source = next((s for s in model["sources"] if s["source_id"] == book["source_id"]), None)
    require(source and source["source_type"] == "review_rules" and source["read_status"] == "readable", "rule_source_missing")
    require(model["dependency_snapshot"].get("review_rulebook") == book, "rule_dependency_mismatch")
    require(model["dependency_snapshot"]["inputs"].get(source["source_id"], {}).get("sha256") == source["sha256"],
            "rule_source_dependency_mismatch")
    require(isinstance(book["rules"], list) and book["rules"], "empty_review_rules")
    objects = {o["object_id"]: o for o in model["objects"]}
    seen, findings = set(), []
    for rule in book["rules"]:
        require(isinstance(rule, dict) and set(rule) == {"rule_id", "object_id", "kind", "value", "locator"}, "invalid_review_rule")
        for k in ("rule_id", "object_id", "kind", "locator"):
            text(rule[k], k)
        require(rule["rule_id"] not in seen, "duplicate_review_rule"); seen.add(rule["rule_id"])
        require(rule["object_id"] in objects, "rule_object_missing")
        obj = objects[rule["object_id"]]
        require(obj["kind"] == "variable", "unsupported_rule_object")
        kind, value = rule["kind"], rule["value"]
        require(kind in {"type", "flag_length", "label_exact", "label_semantic"}, "unsupported_review_rule")
        if kind == "type":
            require(isinstance(value, str) and value in {"character", "numeric"}, "invalid_rule_value")
            fields = [("expected", "type"), ("observed", "type")]
        elif kind == "flag_length":
            require(type(value) is int and value == 1, "invalid_flag_length_rule")
            fields = [("expected", "declared_length"), ("observed", "storage_length")]
        elif kind == "label_exact":
            text(value)
            version = re.fullmatch(r"(?:SDTMIG[ -])?(3\.[0-2])", book["ig_version"])
            require(version is not None, "label_exact_not_applicable")
            fields = [("expected", "label"), ("observed", "label")]
        else:
            text(value)
            fields = []  # Meaning equivalence is explicitly a human review, never a string verdict.
        unavailable = [{"view": view, "field": field} for view, field in fields if not obj[view] or field not in obj[view]]
        violations = [{"view": view, "field": field, "actual": obj[view][field]}
                      for view, field in fields if obj[view] and field in obj[view]
                      and canonical(obj[view][field]) != canonical(value)]
        findings.append({"rule_id": rule["rule_id"], "object_id": obj["object_id"],
                         "result": "failed" if violations else "not_completed" if unavailable else "needs_human_review" if kind == "label_semantic" else "passed_local_rule",
                         "violations": violations, "not_evaluable": unavailable, "required_value": value,
                         "source_id": source["source_id"], "source_sha256": source["sha256"],
                         "locator": rule["locator"], "ig_version": book["ig_version"], "ct_version": book["ct_version"]})
    return findings


def reuse_offer(model, entry):
    from .decisions import compare_dependencies
    old, new = entry["dependency_snapshot"], model["dependency_snapshot"]
    changes = compare_dependencies(old, new)
    source_types = {s["source_id"]: s["source_type"] for s in model["sources"]}
    inputs = sorted(k for k in set(old["inputs"]) | set(new["inputs"])
                    if canonical(old["inputs"].get(k)) != canonical(new["inputs"].get(k)))
    xpt = [k for k in inputs if source_types.get(k) == "xpt"]
    other_inputs = [k for k in inputs if source_types.get(k) not in {"xpt", "read_context", "delivery_evidence"}]
    other = sorted(set(changes["changed_components"]) - {"inputs", "read_context"})
    patch = entry["patch"]
    target = next((o for o in model["objects"] if o["object_id"] == patch["object_id"]), None)
    current_issues = [i for i in model["issues"] if i["issue_id"] in patch["issue_ids"]]
    candidate_valid = (len(current_issues) == len(patch["issue_ids"]) and all(
        any(canonical(c["value"]) == canonical(patch["selected_value"]) for c in i["candidates"])
        for i in current_issues))
    standard_block = any(f["result"] == "failed" and f["object_id"] == patch["object_id"] for f in rule_findings(model))
    return {"decision_id": patch["decision_id"], "object_id": patch["object_id"],
            "eligible": bool(xpt and not other_inputs and not other and target and candidate_valid and not standard_block),
            "changed_components": changes["changed_components"], "changed_inputs": inputs,
            "input_changes": [{"source_id": k, "previous": old["inputs"].get(k), "current": new["inputs"].get(k)} for k in inputs],
            "other_changed_dependencies": other + other_inputs, "current_candidate_valid": candidate_valid,
            "current_observation": ({k: v for k, v in target["observed"].items() if k not in {"observed_values", "raw_values"}} if target else None),
            "current_candidates": [i["candidates"] for i in current_issues],
            "previous_observation": deepcopy(entry.get("reviewed_observation")),
            "previous_candidates": deepcopy(entry.get("reviewed_candidates")),
            "human_confirmation_required": True, "downstream_validation_and_approval": "needs_review",
            "unattended_reuse": False}


def build_policy(model):
    dep = model["dependency_snapshot"]["dependency_snapshot_id"]
    entries, manual = [], []
    for obj in model["objects"]:
        basis = _no_data(model, obj)
        if basis:
            evidence = sorted({e for a in model["assertions"] if a["object_id"] == obj["object_id"]
                               and a["assertion_kind"] == "observed" for e in a["evidence_ids"]})
            entry = {"object_id": obj["object_id"], "has_no_data": "Yes", "basis": basis,
                     "dependency_snapshot_id": dep, "evidence_ids": evidence,
                     "confirmation": "pending", "reason": None, "action_id": None,
                     "xml_comment_required": True,
                     "xml_target": "ItemGroupDef/@CommentOID -> CommentDef/Description" if obj["kind"] == "dataset" else
                     "ItemRef/@def:HasNoData; ItemDef/@CommentOID -> CommentDef/Description",
                     "xml_generation": "not_run"}
            for record in model.get("review_actions", []):
                action = record["action"]
                if action["object_id"] == obj["object_id"] and action["kind"] == "confirm_no_data" and action["dependency_snapshot_id"] == dep:
                    entry.update(confirmation=record["status"], reason=action["value"], action_id=action["action_id"])
            entries.append(entry)
        obs = obj["observed"]
        if obj["expected"] and ((obj["kind"] == "dataset" and obs.get("read_status") != "readable") or
                                 obs.get("observed_status") == "variable_absent"):
            manual.append({"object_id": obj["object_id"], "reason": "缺少输入／读取失败／缺少变量，须人工确认；不能推断无数据"})
    findings = rule_findings(model)
    upstream = [{"issue_id": i["issue_id"], "object_id": i["object_id"], "basis": "unexpected_object",
                 "workflow": "upstream_rework", "blocking": True}
                for i in model["issues"] if i["category"] == "unexpected_object"]
    upstream += [{"rule_id": f["rule_id"], "object_id": f["object_id"], "basis": "locked_rule_violation",
                  "workflow": "upstream_rework", "blocking": True} for f in findings if f["result"] == "failed"]
    for record in model.get("review_actions", []):
        action = record["action"]
        if action["kind"] == "return_upstream" and action["dependency_snapshot_id"] == dep:
            for identifier in action["value"]:
                if any(i["issue_id"] == identifier and i["status"] != "resolved" for i in model["issues"]):
                    if not any(e.get("issue_id") == identifier for e in upstream):
                        upstream.append({"issue_id": identifier, "object_id": action["object_id"], "basis": "human_return",
                                         "action_id": action["action_id"], "workflow": "upstream_rework", "blocking": True})
    return {"schema_version": "mvp01-review-0.1", "no_data": entries, "manual_confirmation": manual,
            "upstream_rework": upstream, "rule_findings": findings,
            "standard_check": "local_rules_checked" if findings and all(f["result"] != "not_completed" for f in findings) else "not_completed",
            "standard_conformance": "not_assessed", "p21_check": "not_run", "final_delivery_approved": False,
            "reuse_offers": [reuse_offer(model, d) for d in model.get("decisions", [])
                            if d["dependency_snapshot"]["dependency_snapshot_id"] != dep]}


def project_review(model):
    out = deepcopy(model)
    for key, identifier in (("sources", "source_id"), ("assertions", "assertion_id"), ("evidence", "evidence_id")):
        out[key].sort(key=lambda item: item[identifier])
    out.setdefault("review_actions", [])
    out["review_policy"] = build_policy(out)
    from .model import business_digest
    out["model_snapshot_id"] = business_digest(out)
    return out


def validate_review(model):
    if "review_policy" not in model:
        require(not model.get("review_actions") and not model.get("review_rulebook"), "review_policy_missing")
        return
    seen = {}
    for record in model.get("review_actions", []):
        action = record["action"]
        _action_shape(action)
        require(action["action_id"] not in seen, "duplicate_review_action")
        _authorized(model, action, record["authorization"], model["test_only"])
        from .model import dependency_digest
        snapshot = record["dependency_snapshot"]
        require(snapshot["dependency_snapshot_id"] == action["dependency_snapshot_id"] == dependency_digest(snapshot), "review_history_dependency_mismatch")
        require(record["status"] == ("simulated" if model["test_only"] else "confirmed"), "invalid_review_action_status")
        prior = action["supersedes"]
        if prior is not None:
            require(prior in seen and seen[prior]["kind"] == action["kind"] and
                    seen[prior]["object_id"] == action["object_id"], "invalid_review_predecessor")
            require(not any(a["supersedes"] == prior for a in seen.values()), "review_predecessor_not_current")
        elif action["kind"] != "confirm_reuse":
            require(not any(a["kind"] == action["kind"] and a["object_id"] == action["object_id"] for a in seen.values()),
                    "review_revision_requires_supersedes")
        if action["kind"] == "confirm_no_data":
            text(action["value"], "no_data_reason")
            if action["dependency_snapshot_id"] == model["dependency_snapshot"]["dependency_snapshot_id"]:
                require(any(o["object_id"] == action["object_id"] and _no_data(model, o) for o in model["objects"]), "no_data_fact_no_longer_true")
        elif action["kind"] == "return_upstream":
            require(isinstance(action["value"], list) and action["value"] and all(isinstance(i, str) for i in action["value"]), "invalid_return_scope")
        else:
            matches = [d for d in model["decisions"] if d["patch"]["decision_id"] == action["action_id"] + ":decision"]
            require(len(matches) == 1, "reuse_history_decision_missing")
            patch = matches[0]["patch"]
            require(patch["supersedes"] == action["value"] and patch["object_id"] == action["object_id"] and
                    patch["dependency_snapshot_id"] == action["dependency_snapshot_id"] and
                    patch["reviewer"] == action["reviewer"] and patch["decided_at"] == action["decided_at"] and
                    patch["rationale"] == action["rationale"], "reuse_history_scope_mismatch")
        seen[action["action_id"]] = action
    require(canonical(model["review_policy"]) == canonical(build_policy(model)), "review_policy_fact_mismatch")


def apply_review_action(model, action, authorization, *, test_mode=False):
    from .decisions import apply_decision
    from .model import validate_model
    validate_model(model)
    _action_shape(action)
    _authorized(model, action, authorization, test_mode)
    require(action["dependency_snapshot_id"] == model["dependency_snapshot"]["dependency_snapshot_id"], "stale_review_action")
    require(any(o["object_id"] == action["object_id"] for o in model["objects"]), "review_object_missing")
    records = model.get("review_actions", [])
    old = next((r for r in records if r["action"]["action_id"] == action["action_id"]), None)
    if old:
        require(canonical(old["action"]) == canonical(action) and canonical(old["authorization"]) == canonical(authorization),
                "review_same_id_different_content")
        return deepcopy(model), {"business_changes": 0, "status": old["status"]}
    out = deepcopy(model)
    if action["kind"] == "confirm_no_data":
        text(action["value"], "no_data_reason")
        require(any(o["object_id"] == action["object_id"] and _no_data(out, o) for o in out["objects"]), "no_data_fact_required")
    elif action["kind"] == "return_upstream":
        ids = action["value"]
        require(isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids), "invalid_return_scope")
        require(all(any(i["issue_id"] == key and i["object_id"] == action["object_id"] and i["status"] != "resolved"
                        for i in out["issues"]) for key in ids), "return_issue_missing")
    else:
        text(action["value"], "previous_decision_id")
        prior = next((d for d in out["decisions"] if d["patch"]["decision_id"] == action["value"]), None)
        require(prior and prior["patch"]["object_id"] == action["object_id"], "reuse_decision_missing")
        require(reuse_offer(out, prior)["eligible"], "reuse_ineligible")
        require(prior["status"] in {"valid", "test_simulated"}, "reuse_prior_not_effective")
        patch = {**deepcopy(prior["patch"]), "decision_id": action["action_id"] + ":decision",
                 "reviewer": action["reviewer"], "decided_at": action["decided_at"], "rationale": action["rationale"],
                 "dependency_snapshot_id": action["dependency_snapshot_id"], "supersedes": prior["patch"]["decision_id"],
                 "validity_status": "valid", "authorization_status": "synthetic_only" if model["test_only"] else "authorized"}
        auth = {**deepcopy(authorization), "scope": {k: patch[k] for k in ("object_id", "field_path", "selected_value", "dependency_snapshot_id")},
                "review_action_id": action["action_id"]}
        out, _ = apply_decision(out, patch, out["dependency_snapshot"], auth, test_mode=test_mode)
        out["downstream_applicability"] = [{"record_id": r["record_id"], "status": "needs_review"} for r in out["downstream_records"]]
    target = next(o for o in model["objects"] if o["object_id"] == action["object_id"])
    observation = {k: v for k, v in target["observed"].items() if k not in {"observed_values", "raw_values"}}
    out.setdefault("review_actions", []).append({"action": deepcopy(action), "authorization": deepcopy(authorization),
                                                "dependency_snapshot": deepcopy(model["dependency_snapshot"]),
                                                "reviewed_observation": deepcopy(observation),
                                                "status": "simulated" if model["test_only"] else "confirmed"})
    out = project_review(out)
    validate_model(out)
    return out, {"business_changes": 1, "status": "simulated" if model["test_only"] else "confirmed"}
