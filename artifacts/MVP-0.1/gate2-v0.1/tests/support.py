from copy import deepcopy
from pathlib import Path
import tempfile

from define_auto.common import load, sha, write
from define_auto.engine import reconcile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "artifacts/TASK-001/gate1-v0.1"
BASE = PACKAGE / "fixtures/task001/v0.1"
CONTEXT = ROOT / "fixtures/mvp01/baseline-context-v0.1/read-context.json"
PROVENANCE = {"TEST-BASELINE-MANUFACTURE-001": ROOT / "fixtures/mvp01/baseline-context-v0.1/delivery-record.json"}


def baseline():
    return reconcile(BASE / "input-manifest.json", context_path=CONTEXT, provenance_paths=PROVENANCE, test_mode=True)


def obj(model, ds, var=None):
    return next(o for o in model["objects"] if o["dataset"] == ds and o.get("variable") == var)


def issue(model, ds, var, field=None):
    identifier = obj(model, ds, var)["object_id"]
    return next(i for i in model["issues"] if i["object_id"] == identifier and (field is None or i["field_path"] == field))


def patch_context(model):
    """Isolated derivative binding original fixture decision to the actual run.

    This is explicitly TEST authorization, never a human approval record.
    """
    model = deepcopy(model)
    patch = load(BASE / "patch.json")
    patch["dependency_snapshot_id"] = model["dependency_snapshot"]["dependency_snapshot_id"]
    record = dict(authorization_id="TEST-AUTH-001", reviewer=patch["reviewer"], test_only=True,
                  scope={k: patch[k] for k in ["object_id", "field_path", "selected_value", "dependency_snapshot_id"]})
    from define_auto.common import canonical
    raw = canonical(record)
    model["sources"].append(dict(source_id="TEST-AUTH-SOURCE", relative_path="test-authorization.json", sha256=sha(raw),
        source_type="authorization", version="test-1", acquired_at="test-run", confidentiality="fully_synthetic",
        completeness_scope={"test_only": True}, provision_status="provided", read_status="readable"))
    record.update(source_id="TEST-AUTH-SOURCE", source_sha256=sha(raw))
    return model, patch, record


def workspace():
    (ROOT / "work").mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="mvp01-tests-", dir=ROOT / "work")
