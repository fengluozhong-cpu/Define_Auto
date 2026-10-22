"""Input registry, structured Spec adapter, and field-level reconciliation."""
from copy import deepcopy
from pathlib import Path
import platform
import sys

from . import __version__
from .common import (ContractError, canonical, digest_value, integer, load, local_path,
                     name, object_id, require, sha, stable, text)
from .model import business_digest, validate_model
from .xpt import read_xpt, validate_context


def read_spec(spec):
    require(isinstance(spec, dict), "invalid_spec")
    require(spec.get("schema_version") == "task001-spec-0.1", "unsupported_spec_schema")
    text(spec.get("study_id")); text(spec.get("spec_id")); text(spec.get("version"))
    object_id(spec["study_id"], spec.get("family"))
    require(isinstance(spec.get("standards"), dict) and isinstance(spec.get("datasets"), list), "invalid_spec")
    unsupported = []

    def unknown(obj, allowed, loc):
        for key in sorted(set(obj) - set(allowed)):
            unsupported.append((loc + "/" + key, obj[key]))

    unknown(spec, ["schema_version", "spec_id", "version", "study_id", "family", "status", "standards", "datasets", "extension_slots"], "")
    datasets = set()
    for di, d in enumerate(spec["datasets"]):
        require(isinstance(d, dict), "invalid_dataset")
        n = name(d.get("name")); text(d.get("label"))
        require(n not in datasets, "ambiguous_identity", "/datasets/" + str(di)); datasets.add(n)
        unknown(d, ["name", "label", "variables", "value_levels"], f"/datasets/{di}")
        if d.get("value_levels"):
            unsupported.append((f"/datasets/{di}/value_levels", d["value_levels"]))
        require(isinstance(d.get("variables"), list), "invalid_variables")
        variables = set()
        for vi, v in enumerate(d["variables"]):
            require(isinstance(v, dict), "invalid_variable")
            vn = name(v.get("name")); text(v.get("label"))
            require(vn not in variables, "ambiguous_identity", f"/datasets/{di}/variables/{vi}"); variables.add(vn)
            require(v.get("type") in {"character", "numeric"}, "invalid_variable_type")
            integer(v.get("declared_length"), 1)
            require(v["declared_length"] <= (200 if v["type"] == "character" else 8), "unsupported_variable_width")
            unknown(v, ["name", "label", "type", "declared_length", "origin", "method_id", "codelist_id"], f"/datasets/{di}/variables/{vi}")
    ext = spec.get("extension_slots", {})
    require(isinstance(ext, dict), "invalid_extensions")
    for key, value in ext.items():
        if value not in (None, [], {}):
            unsupported.append(("/extension_slots/" + key, value))
    return unsupported


def reconcile(manifest_path, *, context_path=None, provenance_paths=None, test_mode=False,
              config=None, review_rules_path=None):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = load(manifest_path)
    require(isinstance(manifest, dict), "invalid_manifest")
    study, family = manifest.get("study_id"), manifest.get("family")
    object_id(study, family)
    require(type(manifest.get("provided_scope_complete")) is bool, "invalid_completeness")
    require(isinstance(manifest.get("sources"), list), "invalid_sources")
    registry, sources = {}, []
    xpt_sources, spec_sources = {}, []
    for original in manifest["sources"]:
        require(isinstance(original, dict), "invalid_source")
        source = deepcopy(original)
        sid = text(source.get("source_id"))
        require(sid not in registry, "duplicate_source_id")
        for key in ["version", "source_type", "acquired_at", "confidentiality"]:
            text(source.get(key), key)
        require(isinstance(source.get("completeness_scope"), dict), "missing_completeness")
        provision = source.get("provision_status")
        require(provision in {"provided", "not_provided"}, "invalid_provision")
        path = local_path(root, source.get("relative_path"))
        data = b""
        if provision == "provided":
            digest_value(source.get("sha256"))
            require(path.is_file(), "provided_file_missing", sid)
            data = path.read_bytes()
            require(sha(data) == source["sha256"], "source_hash_mismatch", sid)
        else:
            require(source.get("sha256") is None and not path.exists(), "supply_contradiction", sid)
        source["read_status"] = "not_attempted"
        registry[sid] = {**source, "bytes": data}
        sources.append(source)
        if source["source_type"] == "xpt":
            names = source["completeness_scope"].get("datasets")
            require(isinstance(names, list) and len(names) == 1, "ambiguous_xpt_scope")
            ds = name(names[0]); require(ds not in xpt_sources, "ambiguous_identity")
            xpt_sources[ds] = source
        elif source["source_type"] == "structured_spec":
            require(provision == "provided", "spec_not_provided")
            spec_sources.append(source)
        else:
            raise ContractError("unsupported_source_type", sid)
    require(len(spec_sources) == 1, "ambiguous_spec_source")
    spec_source = spec_sources[0]
    from .common import strict_json
    spec = strict_json(registry[spec_source["source_id"]]["bytes"].decode("utf-8-sig"))
    unsupported = read_spec(spec)
    require(spec["study_id"] == study and spec["family"] == family, "spec_identity_mismatch")
    require(isinstance(manifest.get("planned_datasets"), list) and
            all(isinstance(d, str) for d in manifest["planned_datasets"]) and
            len(set(manifest["planned_datasets"])) == len(manifest["planned_datasets"]) and
            set(manifest["planned_datasets"]) == {d["name"] for d in spec["datasets"]}, "planned_scope_mismatch")
    spec_source["read_status"] = "readable"
    context = None
    for sid, path in sorted((provenance_paths or {}).items()):
        text(sid); require(sid not in registry, "duplicate_source_id")
        require(Path(path).is_file(), "provenance_source_missing", sid)
        data = Path(path).read_bytes()
        source = dict(source_id=sid, relative_path=Path(path).name, sha256=sha(data), source_type="delivery_evidence",
                      version="sha256:" + sha(data), acquired_at="recorded_in_run_manifest", confidentiality="local",
                      completeness_scope={"declaration": "external_delivery_evidence"}, provision_status="provided", read_status="readable")
        registry[sid] = {**source, "bytes": data}; sources.append(source)
    if context_path is not None:
        context = load(context_path)
        validate_context(context, study, family, registry, test_mode=test_mode)
        data = Path(context_path).read_bytes()
        sid = "READ-CONTEXT"
        require(sid not in registry, "duplicate_source_id")
        source = dict(source_id=sid, relative_path=Path(context_path).name, sha256=sha(data), source_type="read_context",
                      version=context["schema_version"], acquired_at="recorded_in_run_manifest", confidentiality="local",
                      completeness_scope={"declaration": "read_context"}, provision_status="provided", read_status="readable")
        sources.append(source)
    effective_config = {"trim_ascii_spaces": True, **(config or {})}
    require(set(effective_config) <= {"trim_ascii_spaces", "encoding"} and
            effective_config["trim_ascii_spaces"] is True, "unsupported_effective_config")
    physical = {}
    used_declarations = set()
    for ds, source in sorted(xpt_sources.items()):
        result = dict(provision_status=source["provision_status"], read_status="not_attempted", row_count=None,
                      variables=None, observed_status="unknown", no_data_reason=None, has_no_data=None)
        if source["provision_status"] == "provided":
            declarations = [d for d in (context or {}).get("declarations", []) if d["source_sha256"] == source["sha256"]]
            require(len(declarations) <= 1, "ambiguous_declaration")
            declaration = declarations[0] if declarations else None
            if declaration:
                used_declarations.add(declaration["declaration_id"])
            encoding = declaration["encoding"] if declaration else effective_config.get("encoding")
            try:
                parsed = read_xpt(registry[source["source_id"]]["bytes"], encoding=encoding, declaration=declaration,
                                  allow_values=test_mode and source["confidentiality"] == "fully_synthetic")
                require(parsed["member"] == ds, "manifest_member_mismatch")
                result.update(parsed); result["read_status"] = "readable"
            except ContractError as exc:
                result.update(read_status="unreadable", error={"code": exc.code, "locator": exc.locator})
        source["read_status"] = result["read_status"]
        physical[ds] = result
    require(used_declarations == {d["declaration_id"] for d in (context or {}).get("declarations", [])},
            "unused_declaration_target")
    model = dict(schema_version="mvp01-model-0.1", study_id=study, family=family, test_only=bool(test_mode),
                 sources=sorted(sources, key=lambda s: s["source_id"]), objects=[], evidence=[], assertions=[], issues=[],
                 decisions=[], authorization_records={}, downstream_records=[], impact_records=[],
                 reference_state="gap", submission_readiness="not_assessed", unsupported_metadata=[],
                 input_scope=deepcopy({k: v for k, v in manifest.items() if k != "sources"}),
                 extensions=deepcopy(spec.get("extension_slots", {})))
    package = Path(__file__).parent
    dependencies = dict(inputs={s["source_id"]: {"sha256": s["sha256"], "version": s["version"],
                        "provision_status": s["provision_status"], "completeness_scope": s["completeness_scope"]} for s in model["sources"]},
        study_id=study, family=family, standards=deepcopy(spec["standards"]),
        input_scope=deepcopy(model["input_scope"]), rules={"version": "mvp01-rule-0.2", "review_policy": "mvp01-review-0.1"},
        config=effective_config, model_schema="mvp01-model-0.1", upstream_decisions=[],
        read_context=deepcopy(context),
        effective_encodings={ds: (next((d["encoding"] for d in (context or {}).get("declarations", [])
            if d["source_sha256"] == source["sha256"]), effective_config.get("encoding"))) for ds, source in sorted(xpt_sources.items())},
        tools={"define_auto": __version__, "python_implementation": platform.python_implementation(),
               "python_version": list(sys.version_info[:3]),
               "source_hashes": {p.name: sha(p.read_bytes()) for p in sorted(package.glob("*.py"))}})
    dependencies["dependency_snapshot_id"] = stable("dep", dependencies)
    model["dependency_snapshot"] = dependencies
    if review_rules_path is not None:
        book = load(review_rules_path)
        require(isinstance(book, dict), "invalid_review_rulebook")
        raw = Path(review_rules_path).read_bytes()
        sid = book.get("source_id")
        text(sid)
        require(not any(s["source_id"] == sid for s in sources), "duplicate_source_id")
        rule_source = dict(source_id=sid, relative_path=Path(review_rules_path).name, sha256=sha(raw),
            source_type="review_rules", version=book.get("version"), acquired_at="recorded_in_run_manifest",
            confidentiality="local", completeness_scope={"declaration": "explicit_local_rules"},
            provision_status="provided", read_status="readable")
        model["sources"].append(rule_source)
        dependencies["inputs"][sid] = {k: rule_source[k] for k in ["sha256", "version", "provision_status", "completeness_scope"]}
        model["review_rulebook"] = deepcopy(book)
        dependencies["review_rulebook"] = deepcopy(book)
        from .model import dependency_digest
        dependencies["dependency_snapshot_id"] = dependency_digest(dependencies)

    def evidence(source, locator, value, method, raw=None):
        e = dict(source_id=source["source_id"], source_version=source["version"], source_sha256=source["sha256"],
                 locator=locator, raw_value=deepcopy(value if raw is None else raw), normalized_value=deepcopy(value),
                 extraction_method=method, tool_version=__version__)
        e["evidence_id"] = stable("ev", e)
        if not any(x["evidence_id"] == e["evidence_id"] for x in model["evidence"]):
            model["evidence"].append(e)
        return e["evidence_id"]

    def assertion(obj, kind, field, value, ev):
        a = dict(object_id=obj["object_id"], field_path=field, value=deepcopy(value), assertion_kind=kind,
                 evidence_ids=[ev], rule_id="R-EXTRACT-1", review_state="draft")
        a["assertion_id"] = stable("assertion", a)
        model["assertions"].append(a)

    def issue(obj, field, category, expected, observed, evs):
        rule = "R-LABEL-1" if field == "label" else "R-COMPARE-1"
        identifier = obj["object_id"] + ":" + field + ":" + category + ":" + rule
        i = dict(issue_id=identifier, object_id=obj["object_id"], field_path=field, category=category,
                 candidates=[{"kind": "expected", "value": expected}, {"kind": "observed", "value": observed}],
                 evidence_ids=list(dict.fromkeys(evs)), severity="blocking", status="open", rule_id=rule)
        i["revision_id"] = stable("issue-revision", i)
        model["issues"].append(i)

    plans = {d["name"]: (i, d) for i, d in enumerate(spec["datasets"])}
    for ds in sorted(set(plans) | set(physical)):
        di, plan = plans.get(ds, (None, None))
        source = xpt_sources.get(ds, spec_source)
        obs = physical.get(ds, dict(provision_status="not_provided", read_status="not_attempted", row_count=None,
            variables=None, observed_status="unknown", no_data_reason=None, has_no_data=None))
        dataset = dict(object_id=object_id(study, family, ds), kind="dataset", dataset=ds,
                       expected=deepcopy(plan), observed=deepcopy(obs), reference={"state": "gap"}, approved={})
        # Variable facts live on variable objects, not duplicated in dataset views.
        dataset["observed"]["variables"] = [v["name"] for v in obs["variables"]] if obs["variables"] is not None else None
        model["objects"].append(dataset)
        de = evidence(spec_source, f"/datasets/{di}" if plan else "/datasets", plan, "json_pointer")
        if plan:
            assertion(dataset, "expected", "definition", plan, de)
        oe = evidence(source, ds + "/aggregate", dataset["observed"], "xpt_physical_aggregate_or_input_status")
        assertion(dataset, "observed", "availability", dataset["observed"], oe)
        if obs["read_status"] == "readable":
            label_ev = evidence(source, ds + "/label/descriptor", obs["label"], "xpt_ascii_trim_v1", raw=obs["raw_label"])
            assertion(dataset, "observed", "label", obs["label"], label_ev)
        if not plan:
            issue(dataset, "definition", "unexpected_object", None, obs.get("label"), [de, oe])
        elif obs["read_status"] != "readable":
            issue(dataset, "availability", "expected_missing", "provided_readable", obs["read_status"], [de, oe])
        if plan and obs["read_status"] == "readable" and plan["label"].strip(" ") != obs["label"].strip(" "):
            issue(dataset, "label", "field_conflict", plan["label"], obs["label"], [de, oe])
        pv = {v["name"]: (vi, v) for vi, v in enumerate(plan["variables"])} if plan else {}
        ov = {v["name"]: v for v in (obs["variables"] or [])}
        for vn in sorted(set(pv) | set(ov)):
            vi, vp = pv.get(vn, (None, None)); vo = ov.get(vn)
            empty = dict(observed_status="variable_absent" if obs["read_status"] == "readable" else "unknown",
                         missing_count=None, nonmissing_count=None, no_data_reason=None, has_no_data=None)
            var = dict(object_id=object_id(study, family, ds, vn), kind="variable", dataset=ds, variable=vn,
                       expected=deepcopy(vp), observed={**deepcopy(vo or empty), "no_data_reason": None, "has_no_data": None},
                       reference={"state": "gap"}, approved={})
            model["objects"].append(var)
            ve = evidence(spec_source, f"/datasets/{di}/variables/{vi}" if vp else f"/datasets/{di}/variables", vp, "json_pointer")
            voe = evidence(source, ds + "/" + vn + "/aggregate", var["observed"], "xpt_descriptor_and_aggregate_or_input_status")
            if vp:
                for field, value in vp.items():
                    normalized = value.strip(" ") if field == "label" else value
                    field_ev = evidence(spec_source, f"/datasets/{di}/variables/{vi}/{field}", normalized,
                                        "json_pointer_ascii_trim_v1" if field == "label" else "json_pointer", raw=value)
                    assertion(var, "expected", field, normalized, field_ev)
            if vo:
                for field, value in vo.items():
                    field_ev = evidence(source, ds + "/" + vn + "/" + field + "/aggregate", value,
                                        "xpt_ascii_trim_v1" if field == "label" else "xpt_descriptor_and_aggregate",
                                        raw=vo["raw_label"] if field == "label" else None)
                    assertion(var, "observed", field, value, field_ev)
            if not vp:
                issue(var, "definition", "unexpected_object", None, vn, [ve, voe])
            elif not vo:
                issue(var, "availability", "expected_missing", vn, empty["observed_status"], [ve, voe])
            else:
                for field, pf, of in [("label", "label", "label"), ("type", "type", "type"),
                                      ("storage_vs_declared_length", "declared_length", "storage_length")]:
                    a, b = vp[pf], vo[of]
                    if (a.strip(" ") if isinstance(a, str) else a) != (b.strip(" ") if isinstance(b, str) else b):
                        issue(var, field, "field_conflict", a, b, [ve, voe])
                if vo["format_interpretation"] == "gap":
                    issue(var, "format", "unsupported_metadata", None, vo["format_name"], [voe])
    for locator, value in unsupported:
        target = model["objects"][0]
        ev = evidence(spec_source, locator, value, "unsupported_spec_field_preserved")
        issue(target, locator, "unsupported_metadata", value, None, [ev])
        model["unsupported_metadata"].append({"locator": locator, "value": value, "evidence_id": ev})
    for key in ["objects", "evidence", "assertions", "issues"]:
        model[key].sort(key=lambda item: item[{"objects": "object_id", "evidence": "evidence_id", "assertions": "assertion_id", "issues": "issue_id"}[key]])
    from .review import project_review
    model = project_review(model)
    validate_model(model)
    model["model_snapshot_id"] = business_digest(model)
    return model
