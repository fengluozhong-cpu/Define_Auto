"""Runtime validation for the canonical model and evidence sidecar."""
from .common import canonical, digest_value, integer, object_id, require, text, stable


def validate_model(model, *, sealed=False):
    from .common import ContractError
    try:
        result = _validate_model(model)
        if sealed:
            require(model.get("model_snapshot_id") == business_digest(model), "model_snapshot_hash_mismatch")
            dep = model["dependency_snapshot"]
            require(dep["dependency_snapshot_id"] == dependency_digest(dep), "dependency_snapshot_hash_mismatch")
        return result
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ContractError("invalid_model_shape") from exc


def _validate_model(model):
    canonical(model)
    require(model.get("schema_version") == "mvp01-model-0.1", "unsupported_model_schema")
    object_id(model["study_id"], model["family"])
    indexes = {}
    for kind, key in [("sources", "source_id"), ("objects", "object_id"),
                      ("evidence", "evidence_id"), ("assertions", "assertion_id"),
                      ("issues", "issue_id")]:
        require(isinstance(model.get(kind), list), "invalid_collection", kind)
        index = {}
        for item in model[kind]:
            require(isinstance(item, dict), "invalid_record", kind)
            identifier = text(item.get(key), key)
            require(identifier not in index, "duplicate_id", kind)
            index[identifier] = item
        indexes[kind] = index
    for source in model["sources"]:
        require(all(k in source for k in ["provision_status", "read_status", "sha256", "version", "relative_path"]),
                "missing_source_field")
        require(source["provision_status"] in {"provided", "not_provided"}, "invalid_provision")
        require(source["read_status"] in {"not_attempted", "readable", "unreadable"}, "invalid_read_state")
        text(source.get("version")); text(source.get("relative_path"))
        if source["sha256"] is not None:
            digest_value(source["sha256"])
        require(source["provision_status"] != "provided" or source["sha256"] is not None, "missing_source_hash")
        require(source["provision_status"] != "not_provided" or
                (source["sha256"] is None and source["read_status"] == "not_attempted"), "invalid_supply_state")
    for obj in model["objects"]:
        require(obj.get("kind") in {"dataset", "variable"}, "invalid_object_kind")
        require((obj["kind"] == "variable") == ("variable" in obj), "invalid_object_shape")
        expected = object_id(model["study_id"], model["family"], obj["dataset"],
                             obj.get("variable"))
        require(obj["object_id"] == expected, "invalid_object_identity")
        if obj["kind"] == "variable":
            parent = object_id(model["study_id"], model["family"], obj["dataset"])
            require(parent in indexes["objects"], "parent_missing")
        for key in ("expected", "observed", "reference", "approved"):
            require(key in obj, "missing_view", key)
            require(isinstance(obj[key], dict) or (key == "expected" and obj[key] is None), "invalid_view", key)
        require(obj["reference"].get("state") == "gap", "unsupported_reference_state")
        if model.get("test_only"):
            require(not obj["approved"], "test_approval_forbidden")
        for field, value in obj["approved"].items():
            require(value is not None, "unknown_approved_value")
            if isinstance(value, str):
                text(value)
            matches = [a for a in model["assertions"] if a.get("object_id") == obj["object_id"] and
                       a.get("field_path") == field and a.get("assertion_kind") == "approved" and a.get("value") == value]
            require(len(matches) == 1, "approved_view_without_assertion")
        obs = obj["observed"]
        require(obs.get("observed_status") in {"present_empty", "variable_absent", "present_all_missing",
                "present_with_data", "unknown"}, "invalid_observation")
        for key in ["row_count", "missing_count", "nonmissing_count", "storage_length"]:
            if obs.get(key) is not None:
                integer(obs[key], locator=key)
        if "type" in obs:
            require(obs["type"] in {"character", "numeric"}, "invalid_observed_type")
        if "label" in obs:
            require(isinstance(obs["label"], str), "invalid_observed_label")
        for kind in ["expected", "observed"]:
            view = obj[kind]
            if not view:
                continue
            fields = set(view) & {"label", "type", "declared_length", "storage_length"}
            for field in fields:
                matches = [a for a in model["assertions"] if a["object_id"] == obj["object_id"] and
                    a["assertion_kind"] == kind and a["field_path"] == field]
                # Dataset expected fields are retained in a definition assertion.
                if kind == "expected" and obj["kind"] == "dataset":
                    matches = [a for a in model["assertions"] if a["object_id"] == obj["object_id"] and
                               a["assertion_kind"] == "expected" and a["field_path"] == "definition"]
                    require(len(matches) == 1 and matches[0]["value"].get(field) == view[field], "view_assertion_mismatch")
                else:
                    expected_value = view[field].strip(" ") if field == "label" else view[field]
                    require(len(matches) == 1 and canonical(matches[0]["value"]) == canonical(expected_value), "view_assertion_mismatch")
        if obj["kind"] == "variable":
            parent = indexes["objects"][object_id(model["study_id"], model["family"], obj["dataset"])]
            parent_obs = parent["observed"]
            if obs["observed_status"] in {"present_all_missing", "present_with_data"} or obs.get("storage_length") is not None:
                n = parent_obs.get("row_count")
                require(parent_obs.get("read_status") == "readable" and type(n) is int, "stats_without_readable_parent")
                require(type(obs.get("missing_count")) is int and type(obs.get("nonmissing_count")) is int and
                        obs["missing_count"] + obs["nonmissing_count"] == n, "inconsistent_missing_counts")
                require(obs["observed_status"] == ("unknown" if n == 0 else "present_all_missing" if obs["nonmissing_count"] == 0 else "present_with_data"),
                        "inconsistent_observation_status")
            elif parent_obs.get("read_status") != "readable" or obs["observed_status"] == "variable_absent":
                require(obs.get("missing_count") is None and obs.get("nonmissing_count") is None, "unreliable_statistics")
    for e in model["evidence"]:
        require(e["source_id"] in indexes["sources"], "missing_source_reference")
        source = indexes["sources"][e["source_id"]]
        require(e["source_sha256"] == source["sha256"] and e["source_version"] == source["version"],
                "evidence_source_mismatch")
        text(e.get("locator")); text(e.get("extraction_method")); text(e.get("tool_version"))
    for a in model["assertions"]:
        require(a["object_id"] in indexes["objects"], "missing_object_reference")
        require(a["assertion_kind"] in {"expected", "observed", "reference", "approved"}, "invalid_assertion_kind")
        require(a["review_state"] in {"draft", "unknown", "needs_review", "approved"}, "invalid_review_state")
        require(isinstance(a["evidence_ids"], list) and bool(a["evidence_ids"]) and
                all(e in indexes["evidence"] for e in a["evidence_ids"]), "missing_evidence_reference")
        text(a.get("field_path")); text(a.get("rule_id"))
        if a["field_path"] == "label" and a["value"] != "":
            text(a["value"])
        if a["field_path"] == "type":
            require(a["value"] in {"character", "numeric"}, "invalid_assertion_value")
        if a["field_path"] in {"storage_length", "declared_length"}:
            integer(a["value"], 1)
        if a["assertion_kind"] == "approved":
            require(a.get("authorization_record_id") in model.get("authorization_records", {}),
                    "missing_approval_authorization")
            require(not model.get("test_only"), "test_approval_forbidden")
            decisions = [d for d in model.get("decisions", []) if d.get("patch", {}).get("decision_id") == a.get("decision_id")]
            require(len(decisions) == 1 and decisions[0]["status"] == "valid", "invalid_approval_decision")
    for issue in model["issues"]:
        require(issue["object_id"] in indexes["objects"], "missing_object_reference")
        require(issue["category"] in {"expected_missing", "unexpected_object", "field_conflict",
                "reference_error", "unsupported_metadata", "ambiguous_identity"}, "invalid_issue_category")
        require(issue["status"] in {"open", "in_review", "resolved", "rejected", "needs_review"}, "invalid_issue_status")
        require(all(e in indexes["evidence"] for e in issue["evidence_ids"]), "missing_evidence_reference")
        if issue["status"] == "resolved":
            decisions = [d for d in model.get("decisions", []) if d.get("patch", {}).get("decision_id") == issue.get("decision_id")]
            require(len(decisions) == 1 and decisions[0].get("status") == "valid", "missing_resolution_decision")
            patch = decisions[0]["patch"]
            require(issue["issue_id"] in patch["issue_ids"] and patch["object_id"] == issue["object_id"] and
                    patch["field_path"] == issue["field_path"] and not model.get("test_only"), "invalid_resolution_scope")
    for record in model.get("downstream_records", []):
        text(record.get("record_id"))
        require(record.get("status") in {"draft", "passed", "failed", "not_run", "needs_review", "test_simulated", "approved"}, "invalid_downstream_status")
        require(not model.get("test_only") or record.get("status") != "approved", "test_approval_forbidden")
    from .review import validate_review
    validate_review(model)
    return model


def business_digest(model):
    business = {k: v for k, v in model.items() if k not in {"audit", "model_snapshot_id"}}
    if "dependency_snapshot" in business:
        business["dependency_snapshot"] = {k: v for k, v in business["dependency_snapshot"].items() if k != "audit"}
    return stable("model", business)


def dependency_digest(snapshot):
    return stable("dep", {k: v for k, v in snapshot.items() if k not in {"audit", "dependency_snapshot_id"}})
