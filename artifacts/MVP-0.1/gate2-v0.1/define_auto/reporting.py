"""Chinese review tables rendered from one canonical model snapshot."""
import html
import json


def review_rows(model):
    rows = []
    issue_map = {}
    for i in model["issues"]:
        issue_map.setdefault(i["object_id"], []).append(i)
    for obj in model["objects"]:
        expected, observed = obj["expected"], obj["observed"]
        issues = issue_map.get(obj["object_id"], [])
        fields = ["label", "type", "declared_length"] if obj["kind"] == "variable" else ["label", "row_count"]
        for field in fields:
            ofield = "storage_length" if field == "declared_length" else field
            decision_field = "storage_vs_declared_length" if field == "declared_length" else field
            field_issues = [i for i in issues if i["field_path"] in {field, decision_field, "definition", "availability"}]
            evidence = {e for i in field_issues for e in i["evidence_ids"]}
            evidence.update(e for a in model["assertions"] if a["object_id"] == obj["object_id"] and
                            a["field_path"] in {field, ofield, "definition", "availability"} for e in a["evidence_ids"])
            rows.append([obj["object_id"], field, (expected or {}).get(field), observed.get(ofield),
                         obj["reference"], obj["approved"].get(decision_field), observed["observed_status"],
                         ", ".join(sorted({i["category"] for i in field_issues})),
                         ", ".join(sorted(evidence)),
                         "请审阅来源与差异，必要时提供有授权的决定" if field_issues else "保留当前证据；尚非业务批准"])
    return rows


HEADERS = ["对象", "字段", "设计值", "实际值", "标准参考", "批准选值", "观察状态", "差异", "证据", "下一步"]


def _display(value):
    if value is None:
        return "未知／未批准"
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)


def markdown(model):
    def esc(v):
        return html.escape(_display(v), quote=True).replace("|", "&#124;").replace("\n", "<br>").replace("\r", "")
    lines = ["# 元数据核对审阅表", "", "模型快照：`" + model["model_snapshot_id"] + "`", "",
             "状态：草稿；GATE-2 待批准。标准符合性及递交就绪未评估。", "",
             "记录数可能依据外部交付声明；相容性通过不代表已独立证明声明真实。", "",
             "| " + " | ".join(HEADERS) + " |", "| " + " | ".join(["---"] * len(HEADERS)) + " |"]
    lines += ["| " + " | ".join(esc(v) for v in row) + " |" for row in review_rows(model)]
    lines += ["", "## 输入与读取状态", ""]
    for obj in model["objects"]:
        if obj["kind"] == "dataset":
            o = obj["observed"]
            lines.append("- " + esc(obj["dataset"]) + "：" + esc({k: o.get(k) for k in ["provision_status", "read_status", "row_count", "row_count_basis", "declaration_id", "error"]}))
    return "\n".join(lines) + "\n"


def html_report(model):
    esc = lambda v: html.escape(_display(v), quote=True)
    head = "".join("<th>" + esc(h) + "</th>" for h in HEADERS)
    rows = "".join("<tr>" + "".join("<td>" + esc(v) + "</td>" for v in row) + "</tr>" for row in review_rows(model))
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>元数据核对审阅表</title>'
            '<style>body{font:15px sans-serif;margin:24px}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:8px;overflow-wrap:anywhere;max-width:360px}</style>'
            '<h1>元数据核对审阅表</h1><p>草稿；GATE-2 待批准。标准符合性及递交就绪未评估。</p><p>模型快照：' +
            esc(model["model_snapshot_id"]) + '</p><p>记录数可能依据外部交付声明；字节相容性不能独立证明声明真实。</p><table><thead><tr>' + head +
            '</tr></thead><tbody>' + rows + '</tbody></table></html>')
