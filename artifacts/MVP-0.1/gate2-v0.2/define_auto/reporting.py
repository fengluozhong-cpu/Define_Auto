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
                         "返回上游返工，重新交付输入并复核" if any(i["category"] == "unexpected_object" or
                             any(e.get("issue_id") == i["issue_id"] for e in model.get("review_policy", {}).get("upstream_rework", [])) for i in field_issues) else
                         "人工确认输入／读取失败／缺变量，补齐后复核" if any(i["category"] == "expected_missing" for i in field_issues) else
                         "请审阅来源与差异，必要时提供有授权的决定" if field_issues else "保留当前证据；尚非业务批准"])
    policy = model.get("review_policy", {})
    for item in policy.get("no_data", []):
        rows.append([item["object_id"], "HasNoData／无数据原因", None, item["has_no_data"],
                     item["xml_target"], item["reason"], item["confirmation"], "自动标志与人工原因分别管理",
                     ", ".join(item["evidence_ids"]),
                     "待人工确认并补充无数据原因；后续 XML 须关联 Comment" if item["confirmation"] == "pending" else
                     "测试模拟，不能作为真实批准" if item["confirmation"] == "simulated" else "原因已人工确认；XML 未生成，最终批准仍待审阅"])
    rows.append(["标准核查", "standard_check", None, policy.get("standard_check", "not_completed"), None, None,
                 "未完成标准核查" if policy.get("standard_check") == "not_completed" else "仅执行列明的局部规则",
                 "完整标准符合性未评估；P21 未运行", "review-policy.json", "锁定适用版本和规则；不得宣称合规"])
    for item in policy.get("rule_findings", []):
        rows.append([item["object_id"], item["rule_id"], item["required_value"], item["violations"],
                     {"ig_version": item["ig_version"], "ct_version": item["ct_version"]}, None, item["result"],
                     "标准明确问题，返回上游返工" if item["result"] == "failed" else "局部规则结果", item["source_sha256"] + ":" + item["locator"],
                     "修复 Spec／数据并重新核对；选 Define 值不能关闭" if item["result"] == "failed" else "仍非完整标准符合性结论"])
    for offer in policy.get("reuse_offers", []):
        rows.append([offer["object_id"], "人工确认沿用：" + offer["decision_id"], None,
                     {k: offer[k] for k in ["input_changes", "previous_observation", "previous_candidates", "current_observation", "current_candidates", "other_changed_dependencies"]},
                     None, None, "needs_review", "旧验证及最终批准须重审", "历史决定及依赖快照保留",
                     "可由业务人员确认沿用／重新裁决／返回上游" if offer["eligible"] else "不满足沿用条件，请重新审阅并处理变更"])
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
