"""Strict JSON, stable identities, and local input boundaries."""
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath
from urllib.parse import quote


class ContractError(ValueError):
    def __init__(self, code, locator=""):
        self.code, self.locator = code, locator
        super().__init__(code + (": " + locator if locator else ""))


def require(condition, code, locator=""):
    if not condition:
        raise ContractError(code, locator)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("invalid_json_value") from exc


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stable(prefix, value):
    return prefix + "-" + sha(canonical(value))


def strict_json(data):
    def pairs(items):
        obj = {}
        for k, v in items:
            require(k not in obj, "duplicate_json_key", k)
            obj[k] = v
        return obj

    def bad_constant(value):
        raise ContractError("invalid_json_value", value)

    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("invalid_json") from exc


def load(path):
    return strict_json(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).write_bytes(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False).encode("utf-8") + b"\n")


def text(value, locator=""):
    require(isinstance(value, str) and bool(value.strip()) and
            value.strip().lower() not in {"unknown", "tbd", "todo", "placeholder"},
            "invalid_required_text", locator)
    return value


def integer(value, minimum=0, locator=""):
    require(type(value) is int and value >= minimum, "invalid_integer", locator)
    return value


def digest_value(value):
    require(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value), "invalid_sha256")
    return value


def name(value):
    require(isinstance(value, str) and re.fullmatch("[A-Z][A-Z0-9_]{0,7}", value),
            "invalid_object_name")
    return value


def object_id(study, family, dataset=None, variable=None):
    text(study); require(family in {"SDTM", "ADAM"}, "invalid_family")
    parts = ["study", study, "family", family]
    if dataset is not None:
        parts += ["dataset", name(dataset)]
    if variable is not None:
        require(dataset is not None, "parent_missing")
        parts += ["variable", name(variable)]
    return "/".join(quote(p, safe="-._~") for p in parts)


def local_path(root, relative):
    text(relative)
    p = Path(relative)
    require(not p.is_absolute() and not PureWindowsPath(relative).drive and
            not relative.startswith(("/", "\\")) and ".." not in p.parts,
            "unsafe_input_path")
    target = (Path(root) / p).resolve()
    require(target.is_relative_to(Path(root).resolve()), "unsafe_input_path")
    return target


def pointer(value, locator):
    require(isinstance(locator, str) and locator.startswith("/"), "invalid_locator")
    try:
        for part in locator[1:].split("/"):
            require(not re.search(r"~(?![01])", part), "invalid_locator", locator)
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                require(re.fullmatch(r"0|[1-9][0-9]*", part), "invalid_locator", locator)
                value = value[int(part)]
            else:
                value = value[part]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ContractError("missing_provenance_locator", locator) from exc
    return value
