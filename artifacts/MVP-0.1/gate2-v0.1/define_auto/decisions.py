"""Immutable decision history with explicit authorization and invalidation."""
from copy import deepcopy

from .common import canonical, require, sha, stable, text
from .model import business_digest, validate_model


def resume_model(current, prior):
    """Restore immutable decision history; reuse selections only on equal dependencies."""
    validate_model(current); validate_model(prior)
    require((current["study_id"], current["family"], current["test_only"]) ==
            (prior["study_id"], prior["family"], prior["test_only"]), "history_identity_mismatch")
    out = deepcopy(current)
    impact = compare_dependencies(prior["dependency_snapshot"], current["dependency_snapshot"])
    for key in ["decisions", "authorization_records", "downstream_records", "impact_records"]:
        out[key] = deepcopy(prior.get(key, {} if key == "authorization_records" else []))
    ids = {s["source_id"] for s in out["sources"]}
    for source in prior["sources"]:
        if source["source_type"] == "authorization" and source["source_id"] not in ids:
            out["sources"].append(deepcopy(source)); ids.add(source["source_id"])
    if not impact["requires_business_rereview"]:
        old_objects = {o["object_id"]: o for o in prior["objects"]}
        for obj in out["objects"]:
            old = old_objects.get(obj["object_id"], {})
            obj["approved"] = deepcopy(old.get("approved", {}))
            if "simulated_selection" in old:
                obj["simulated_selection"] = deepcopy(old["simulated_selection"])
        # Approved assertions cite original source evidence; retain that evidence.
        current_evs = {e["evidence_id"] for e in out["evidence"]}
        out["assertions"] += deepcopy([a for a in prior["assertions"] if a["assertion_kind"] == "approved"])
        for ev in prior["evidence"]:
            if ev["evidence_id"] not in current_evs:
                out["evidence"].append(deepcopy(ev)); current_evs.add(ev["evidence_id"])
        old_issues = {i["issue_id"]: i for i in prior["issues"]}
        for issue in out["issues"]:
            old = old_issues.get(issue["issue_id"], {})
            if old.get("status") in {"resolved", "in_review"}:
                issue["status"] = old["status"]
                if "decision_id" in old:
                    issue["decision_id"] = old["decision_id"]
    else:
        out["downstream_applicability"] = [{"record_id": r["record_id"], "status": "needs_review"} for r in out["downstream_records"]]
        out["impact_records"].append({"scope": "restored_history", **impact, "downstream_validation_and_approval": "needs_review"})
        for issue in out["issues"]:
            if any(issue["issue_id"] in d["patch"]["issue_ids"] for d in out["decisions"]):
                issue["status"] = "needs_review"
    for key, idkey in [("sources", "source_id"), ("assertions", "assertion_id"), ("evidence", "evidence_id")]:
        out[key].sort(key=lambda item: item[idkey])
    validate_model(out); out["model_snapshot_id"] = business_digest(out)
    return out


def compare_dependencies(previous, current):
    """Audit-only timestamps are excluded; unknown business changes invalidate."""
    def business(value):
        return {k: v for k, v in value.items() if k not in {"audit", "dependency_snapshot_id"}}
    a, b = business(previous), business(current)
    changed = sorted(k for k in set(a) | set(b) if canonical(a.get(k)) != canonical(b.get(k)))
    return {"changed_components": changed, "requires_business_rereview": bool(changed),
            "basis": "conservative_entire_associated_chain" if changed else "business_dependencies_equal_audit_only_or_identical"}


def apply_decision(model, patch, previous_dependency, authorization, *, test_mode=False):
    """Return a fresh model. Caller supplies a registered human authorization record.

    Authenticity of the human declaration is a delivery-process responsibility,
    not a claim of this CLI. Test records never authorize ordinary execution.
    """
    validate_model(model)
    require(isinstance(patch, dict), "invalid_patch")
    required = {"decision_id", "issue_ids", "object_id", "field_path", "selected_value", "rationale",
                "reviewer", "decided_at", "dependency_snapshot_id", "validity_status", "supersedes", "authorization_status"}
    require(set(patch) == required, "unsupported_patch_fields")
    for field in ["decision_id", "object_id", "field_path", "rationale", "reviewer", "decided_at", "dependency_snapshot_id"]:
        text(patch.get(field), field)
    canonical(patch)
    require(patch["validity_status"] in {"candidate", "valid", "needs_review"}, "invalid_patch_status")
    require(patch["authorization_status"] in {"synthetic_only", "authorized"}, "invalid_authorization_status")
    require(isinstance(patch["issue_ids"], list) and patch["issue_ids"] and
            all(isinstance(i, str) and bool(i) for i in patch["issue_ids"]) and
            len(set(patch["issue_ids"])) == len(patch["issue_ids"]), "invalid_issue_references")
    out = deepcopy(model)
    previous = {d["patch"]["decision_id"]: d for d in out["decisions"]}
    old = previous.get(patch["decision_id"])
    if old:
        require(canonical(old["patch"]) == canonical(patch), "reject_same_id_different_content")
    require(isinstance(previous_dependency, dict), "invalid_dependency_snapshot")
    require(patch["dependency_snapshot_id"] == previous_dependency.get("dependency_snapshot_id"), "patch_dependency_mismatch")
    objects = {o["object_id"]: o for o in out["objects"]}
    require(patch["object_id"] in objects, "patch_object_missing")
    issues = {i["issue_id"]: i for i in out["issues"]}
    require(all(i in issues for i in patch["issue_ids"]), "patch_issue_missing")
    for identifier in patch["issue_ids"]:
        issue = issues[identifier]
        require(issue["object_id"] == patch["object_id"] and issue["field_path"] == patch["field_path"], "patch_scope_mismatch")
        require(issue["category"] == "field_conflict", "unsupported_patch_category")
        require(any(canonical(c["value"]) == canonical(patch["selected_value"]) for c in issue["candidates"]), "patch_value_not_candidate")
    value = patch["selected_value"]
    require(value is not None, "unknown_approved_value")
    if patch["field_path"] in {"label", "type"}:
        text(value)
    require(isinstance(authorization, dict) and type(authorization.get("test_only")) is bool, "missing_authorization_record")
    for key in ["authorization_id", "reviewer", "source_id", "source_sha256"]:
        text(authorization.get(key), key)
    require(test_mode or not authorization["test_only"], "test_authorization_forbidden")
    is_test = patch["authorization_status"] == "synthetic_only" or authorization["test_only"]
    require(not is_test or (test_mode and model.get("test_only") and authorization["test_only"]), "synthetic_patch_forbidden")
    require(is_test or (not model.get("test_only") and patch["authorization_status"] == "authorized"), "test_approval_forbidden")
    expected_scope = {"object_id": patch["object_id"], "field_path": patch["field_path"],
                      "selected_value": value, "dependency_snapshot_id": patch["dependency_snapshot_id"]}
    require(canonical(authorization.get("scope")) == canonical(expected_scope) and authorization["reviewer"] == patch["reviewer"], "authorization_scope_mismatch")
    source = next((s for s in model["sources"] if s["source_id"] == authorization["source_id"]), None)
    require(source and source["sha256"] == authorization["source_sha256"] and source["read_status"] == "readable", "authorization_source_missing")
    if patch["supersedes"] is not None:
        require(patch["supersedes"] in previous and patch["supersedes"] != patch["decision_id"], "superseded_decision_missing")
        prior = previous[patch["supersedes"]]["patch"]
        require(prior["object_id"] == patch["object_id"] and prior["field_path"] == patch["field_path"], "supersedes_scope_mismatch")
        require(old or not any(d["patch"].get("supersedes") == patch["supersedes"] for d in out["decisions"]), "superseded_decision_not_current")
    else:
        require(old or not any(d["patch"]["object_id"] == patch["object_id"] and d["patch"]["field_path"] == patch["field_path"]
                        and d["patch"]["decision_id"] != patch["decision_id"] for d in out["decisions"]), "decision_revision_requires_supersedes")
    impact = compare_dependencies(previous_dependency, out["dependency_snapshot"])
    status = "needs_review" if impact["requires_business_rereview"] or patch["validity_status"] == "needs_review" else "test_simulated" if is_test else "valid"
    if old and not impact["requires_business_rereview"]:
        return out, {"business_changes": 0, "status": old["status"], "impact": impact}
    entry = {"patch": deepcopy(patch), "patch_sha256": sha(canonical(patch)), "status": status,
             "authorization_record": deepcopy(authorization), "dependency_snapshot": deepcopy(previous_dependency)}
    if not old:
        out["decisions"].append(entry)
    out["impact_records"].append({"decision_id": patch["decision_id"], **impact, "current_status": status,
        "downstream_validation_and_approval": "needs_review" if status == "needs_review" else "unchanged",
        "old_records_retained": True})
    target = objects[patch["object_id"]]
    if status == "needs_review":
        target["approved"].pop(patch["field_path"], None)
        out["assertions"] = [a for a in out["assertions"] if not (a["object_id"] == target["object_id"]
            and a["field_path"] == patch["field_path"] and a["assertion_kind"] == "approved")]
        for i in patch["issue_ids"]:
            issues[i]["status"] = "needs_review"
        # Keep historical validation/approval records; applicability is separate.
        out["downstream_applicability"] = [{"record_id": r["record_id"], "status": "needs_review"}
                                            for r in out["downstream_records"]]
    elif is_test:
        target.setdefault("simulated_selection", {})[patch["field_path"]] = deepcopy(value)
        for i in patch["issue_ids"]:
            issues[i]["status"] = "in_review"
    else:
        authid = authorization["authorization_id"]
        out["authorization_records"][authid] = deepcopy(authorization)
        target["approved"][patch["field_path"]] = deepcopy(value)
        out["assertions"] = [a for a in out["assertions"] if not (a["object_id"] == target["object_id"] and
            a["field_path"] == patch["field_path"] and a["assertion_kind"] == "approved")]
        evs = sorted({e for i in patch["issue_ids"] for e in issues[i]["evidence_ids"]})
        assertion = dict(object_id=target["object_id"], field_path=patch["field_path"], value=deepcopy(value),
                         assertion_kind="approved", evidence_ids=evs, rule_id="R-HUMAN-DECISION-1", review_state="approved",
                         decision_id=patch["decision_id"], authorization_record_id=authid)
        assertion["assertion_id"] = stable("assertion", assertion)
        out["assertions"].append(assertion)
        for i in patch["issue_ids"]:
            issues[i].update(status="resolved", decision_id=patch["decision_id"])
    for key, idkey in [("sources", "source_id"), ("assertions", "assertion_id")]:
        out[key].sort(key=lambda a: a[idkey])
    validate_model(out)
    out["model_snapshot_id"] = business_digest(out)
    return out, {"business_changes": 0 if status == "needs_review" else 1, "status": status, "impact": impact}
