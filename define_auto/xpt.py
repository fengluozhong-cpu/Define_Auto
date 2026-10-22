"""Single-member XPORT v5, 140-byte NAMESTR; strict declared encoding.

Layout: SAS transport paper, pp.3-7. Unsupported variants fail explicitly.
No row data is returned: only field metadata and aggregates.
"""
import codecs
import math
import struct

from .common import digest_value, integer, name, pointer, require, sha, text


def validate_context(context, study, family, registry, *, test_mode=False):
    require(isinstance(context, dict), "invalid_context")
    require(set(context) == {"schema_version", "study_id", "family", "test_only", "declarations"},
            "unsupported_context_field")
    require(context["schema_version"] == "mvp01-read-context-0.1", "unsupported_context_schema")
    require(context["study_id"] == study and context["family"] == family, "context_identity_mismatch")
    require(type(context["test_only"]) is bool, "invalid_test_flag")
    require(test_mode or not context["test_only"], "test_context_forbidden")
    require(isinstance(context["declarations"], list), "invalid_declarations")
    ids, targets = set(), set()
    for d in context["declarations"]:
        require(isinstance(d, dict) and set(d) == {"declaration_id", "source_sha256", "member", "encoding",
                "record_count", "provided_by", "provenance"}, "invalid_declaration")
        identifier = text(d["declaration_id"])
        require(identifier not in ids, "duplicate_declaration_id"); ids.add(identifier)
        digest_value(d["source_sha256"]); name(d["member"])
        target = (d["source_sha256"], d["member"])
        require(target not in targets, "duplicate_declaration_target"); targets.add(target)
        text(d["provided_by"])
        require(context["test_only"] or not d["provided_by"].startswith("TEST"), "test_context_forbidden")
        require(any(s["sha256"] == d["source_sha256"] and s.get("source_type") == "xpt"
                    for s in registry.values()), "declaration_target_missing")
        text(d["encoding"])
        try:
            codecs.lookup(d["encoding"])
        except LookupError as exc:
            from .common import ContractError
            raise ContractError("unsupported_encoding") from exc
        if d["record_count"] is not None:
            integer(d["record_count"])
        p = d["provenance"]
        require(isinstance(p, dict) and set(p) == {"source_id", "source_sha256", "locator"}, "invalid_provenance")
        digest_value(p["source_sha256"])
        require(p["source_id"] in registry, "provenance_source_missing")
        source = registry[p["source_id"]]
        require(source["sha256"] == p["source_sha256"] and sha(source["bytes"]) == p["source_sha256"],
                "provenance_hash_mismatch")
        # Resolve a location, never treat its contents as parser answers.
        from .common import strict_json
        located = pointer(strict_json(source["bytes"].decode("utf-8-sig")), p["locator"])
        require(isinstance(located, dict), "unsupported_provenance_content")
        require(located.get("member") == d["member"] and
                located.get("source_sha256", located.get("sha256")) == d["source_sha256"],
                "provenance_target_mismatch")
        stated_count = located.get("record_count", located.get("manufactured_record_count"))
        require(d["record_count"] is None or (type(stated_count) is int and stated_count == d["record_count"]),
                "provenance_count_mismatch")
        require("encoding" not in located or located["encoding"] == d["encoding"], "provenance_encoding_mismatch")
    return context


def _header(raw, offset, token):
    require(len(raw) >= offset + 80 and raw[offset:offset + 48].startswith(
            b"HEADER RECORD*******" + token.ljust(8, b" ") + b"HEADER RECORD!!!!!!!"), "invalid_xpt_header", str(offset))


def _number(raw):
    b = raw.ljust(8, b"\0")
    if b[1:] == b"\0" * 7 and (b[0] in (46, 95) or 65 <= b[0] <= 90):
        return None, "._" if b[0] == 95 else "." if b[0] == 46 else "." + chr(b[0])
    if b == b"\0" * 8:
        return 0, None
    fraction = int.from_bytes(b[1:], "big") / (1 << 56)
    require(fraction >= 1 / 16, "invalid_ibm_float")
    value = (-1 if b[0] & 128 else 1) * fraction * 16 ** ((b[0] & 127) - 64)
    require(math.isfinite(value), "invalid_ibm_float")
    return value, None


def read_xpt(raw, *, encoding, declaration=None, allow_values=False):
    require(isinstance(raw, bytes) and len(raw) % 80 == 0, "truncated_xpt")
    require(isinstance(encoding, str) and bool(encoding), "encoding_required")
    try:
        codecs.lookup(encoding)
    except LookupError as exc:
        from .common import ContractError
        raise ContractError("unsupported_encoding") from exc

    def decode(b, loc):
        try:
            return b.decode(encoding, errors="strict").strip(" ")
        except UnicodeError as exc:
            from .common import ContractError
            raise ContractError("decode_error", loc) from exc

    _header(raw, 0, b"LIBRARY")
    require(raw[80:104] == b"SAS     SAS     SASLIB  ", "invalid_library_metadata")
    _header(raw, 240, b"MEMBER")
    require(raw[314:318] == b"0140", "unsupported_namestr_size")
    _header(raw, 320, b"DSCRPTR")
    require(raw[400:408] == b"SAS     " and raw[416:424] == b"SASDATA ", "invalid_member_metadata")
    member = name(decode(raw[408:416], "member"))
    _header(raw, 560, b"NAMESTR")
    require(raw[614:618].isdigit(), "invalid_variable_count")
    count = int(raw[614:618]); require(count > 0, "empty_descriptor")
    end = 640 + 140 * count
    obs_header = ((end + 79) // 80) * 80
    require(raw[end:obs_header] == b" " * (obs_header - end), "invalid_descriptor_padding")
    _header(raw, obs_header, b"OBS")
    start = obs_header + 80
    variables, names, positions = [], set(), set()
    width = 0
    for i in range(count):
        offset = 640 + i * 140
        b = raw[offset:offset + 140]
        require(len(b) == 140, "truncated_descriptor")
        kind, _, length, number = struct.unpack(">hhhh", b[:8])
        n = name(decode(b[8:16], str(offset + 8)))
        require(n not in names and number not in positions, "duplicate_xpt_variable")
        names.add(n); positions.add(number)
        require(kind in {1, 2} and ((2 <= length <= 8) if kind == 1 else (1 <= length <= 200)),
                "unsupported_variable_width")
        position = struct.unpack(">i", b[84:88])[0]
        require(position == width, "invalid_variable_layout")
        width += length
        fw, fd = struct.unpack(">hh", b[64:68])
        fmt = decode(b[56:64], str(offset + 56))
        require(fw >= 0 and fd >= 0, "invalid_format")
        variables.append(dict(name=n, label=decode(b[16:56], str(offset + 16)),
            raw_label=b[16:56].decode(encoding, errors="strict"),
            type="numeric" if kind == 1 else "character", storage_length=length, position=position,
            descriptor_offset=offset, format_name=fmt, format_width=fw, format_decimals=fd,
            format_interpretation="raw_preserved" if fmt in {"", "DATE", "DATETIME", "TIME"} else "gap",
            missing_count=0, nonmissing_count=0, missing_code_counts={}, max_content_bytes=0,
            max_content_characters=0))
    payload = raw[start:]
    # This implementation deliberately accepts a single member only.
    require(not any(payload[i:i + 48].startswith(b"HEADER RECORD*******MEMBER  HEADER RECORD")
                    for i in range(0, len(payload), 80)), "multiple_members_unsupported")
    candidates = [n for n in range(max(0, (len(payload) - 79 + width - 1) // width), len(payload) // width + 1)
                  if payload[n * width:] == b" " * (len(payload) - n * width)]
    if declaration is not None:
        require(declaration["source_sha256"] == sha(raw), "declaration_hash_mismatch")
        require(declaration["member"] == member, "declaration_member_mismatch")
        require(declaration["encoding"] == encoding, "declaration_encoding_mismatch")
    nrows = declaration.get("record_count") if declaration else None
    if nrows is None:
        require(len(candidates) == 1, "ambiguous_record_count")
        nrows = candidates[0]; basis = "unambiguous_layout"
    else:
        integer(nrows)
        require(nrows in candidates, "record_count_incompatible")
        basis = "delivery_declaration"
    values = {v["name"]: set() for v in variables}
    for row in range(nrows):
        for v in variables:
            pos = row * width + v["position"]
            cell = payload[pos:pos + v["storage_length"]]
            if v["type"] == "character":
                value = decode(cell, member + "/" + v["name"] + "/aggregate")
                missing = not value
                v["max_content_bytes"] = max(v["max_content_bytes"], len(cell.strip(b" ")))
                v["max_content_characters"] = max(v["max_content_characters"], len(value))
            else:
                value, code = _number(cell); missing = code is not None
                if code:
                    codes = v["missing_code_counts"]
                    codes[code] = codes.get(code, 0) + 1
            v["missing_count" if missing else "nonmissing_count"] += 1
            # Privacy: identity fields expose counts, never observed identifiers.
            if not missing:
                values[v["name"]].add(value)
    for v in variables:
        v["distinct_nonmissing"] = len(values[v["name"]])
        v["observed_status"] = "unknown" if not nrows else "present_with_data" if v["nonmissing_count"] else "present_all_missing"
        v["observed_values"] = None if (not allow_values and values[v["name"]]) or v["name"] in {"USUBJID", "SUBJID", "STUDYID"} else sorted(values[v["name"]], key=repr)
    return dict(member=member, label=decode(raw[512:552], "dataset/label"), raw_label=raw[512:552].decode(encoding, errors="strict"), row_count=nrows,
                observed_status="present_empty" if nrows == 0 else "present_with_data", variables=variables,
                row_count_basis=basis, declaration_id=declaration["declaration_id"] if declaration else None,
                padding_bytes=len(payload) - nrows * width, observation_offset=start,
                declaration_provenance=declaration["provenance"] if declaration else None,
                count_limitation="trusted_delivery_declaration_not_independently_verified" if basis == "delivery_declaration" else None)
