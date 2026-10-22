"""Record reviewer conclusions and independently verify evidence hashes.

All case judgments below were independently reasoned from raw bytes, recipe,
Spec and the approved baseline; no reconciliation engine exists or is called.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def load(relative):
    return json.loads((ROOT / relative).read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manual_notes = [
    "DM 三条显式 recipe 记录；STUDYID 全为 6 ASCII 字节，Spec、NAMESTR 与内容长度一致；不产生批准。",
    "Spec 计划 AE；manifest 明确未提供，ae.xpt 不存在；行数、业务原因及 HasNoData 都无证据，保持 null。",
    "CM 是已提供的故意损坏文本，无 XPORT library header；与 AE 缺席不同，不能推导其变量或行数。",
    "VS 有五个 NAMESTR 描述而无 observation payload；0 行、每变量统计 0，不由零分母推出全缺失。",
    "Spec 计划 ARM；DM 七个实际列没有 ARM；缺变量统计是未知/null，不能报告已存在且全空。",
    "DM.SEX 三个单字节空格；缺失 3、非缺失 0、观察非缺失集合为空；原因未知。",
    "DM.AGE 三个 raw cell 首字节分别 2e/41/5a，尾七字节皆零；普通点、A、Z 各一次，共缺失 3。",
    "Spec label Biological Sex 与 NAMESTR Sex 不同，精确/ASCII trim 比较仍冲突；没有人工最终批准选值。",
    "Spec SEX 长度 3 与 NAMESTR 存储宽度 1 不同；观察内容长度 0 独立保存，不覆盖两者。",
    "Spec ARMCD 为 character，NAMESTR type=1 numeric；宽度均 8 不消除类型冲突。",
    "Spec Planned Arm Code 与 NAMESTR Actual Arm Code 单独形成 label 冲突，不被类型冲突吞并。",
    "NAMESTR 有 EXTRA，但 Spec 七个计划变量无 EXTRA；是额外物理对象，不自动写 approved。",
    "相同 ID/内容重入按契约应幂等；合成 patch authorization=synthetic_only，不能产生真实批准；行为留待 MVP 0.1。",
    "spec-changed 确实变更 SEX label 和版本；旧选值依据的输入依赖变化，应重审，保留旧记录；未执行 patch 引擎。",
    "CT 从 not_selected 改为明确合成参考上下文；未证明影响范围可缩小时保守重审；不是实际 CT 验证。",
    "规则从 trim_ascii_spaces_then_exact 改为 exact；规则依赖变化可影响选值/比较，输入 hash 相同不足以复用。",
    "config trim_ascii_spaces 从 true 改 false；有效配置变化，须有影响分析并重审相关链。",
    "schema 提案由 task001-contract-0.1 改为 SYN-MODEL-2，字段约束改变；旧决定不能自动适用于新模型。",
    "upstream_decisions 从空改为合成决定；上游依赖变化触发下游验证及批准适用性重审。",
    "结果相关工具依赖改为合成 extractor；不能只因输入字节未变复用旧裁决。",
    "P-AUDIT 只替换审计 run_started_at；契约排除纯审计时间，业务身份不变但须记录影响依据。",
    "SYN-DEC-001 同 ID 将 selected_value 改为 Sex 属不同内容；应拒绝覆盖，修订须新 ID + supersedes。",
    "Spec/依赖明确未选 IG/CT；reference gap 与 not_assessed 正确；不得推造最新版或 NCI 编码。",
    "永久 identity 含 study/family/dataset/variable；同名跨 study/family 分离，源顺序/审计时间不参与；执行碰撞回归延期。",
]


def main():
    for filename in ["final-review.json", "final-review.md"]:
        assert not (OUT / filename).exists(), "Do not replace independent review evidence"
    assertions = []

    def check(name, condition):
        assertions.append({"id": name, "result": "passed" if condition else "failed"})

    baseline_path = ROOT / "baselines/BL-20261020-01/manifest.json"
    check("baseline_manifest", sha(baseline_path) == "55b68829f17a489060281174c901a9de6fd2f5902831ed3b7aa717696e5e802c")
    for row in load("baselines/BL-20261020-01/manifest.json")["files"]:
        path = baseline_path.parent / row["path"]
        check("baseline." + row["path"], sha(path) == row["sha256"] and path.stat().st_size == row["bytes"])
    for row in load("artifacts/TASK-001/start/dependencies.json")["protected_files"]:
        check("protected." + row["path"], sha(ROOT / row["path"]) == row["sha256"])
    for row in load("artifacts/TASK-001/materials-04/inputs-manifest.json")["files"]:
        check("actual_input_version." + row["path"], sha(ROOT / row["path"]) == row["sha256"])
    for row in load("artifacts/TASK-001/materials-04/outputs-manifest.json")["files"]:
        check("actual_output_version." + row["path"], sha(ROOT / "artifacts/TASK-001/materials-04" / row["path"]) == row["sha256"])
    sources = load("artifacts/TASK-001/references/sources.json")["assets"]
    check("F001.unique_paths", len({s["path"] for s in sources}) == len(sources))
    for row in sources:
        path = ROOT / "artifacts/TASK-001/references" / row["path"]
        check("F001.source." + row["path"], sha(path) == row["sha256"] and path.stat().st_size == row["bytes"])
    expected = load("expectations/task001/v0.1/expected.json")
    raw = load("docs/tasks/task001-review/independent-xpt-raw-v1.json")["findings"]
    for dataset, result in raw.items():
        facts = expected["facts"][dataset]
        check("independent_raw." + dataset + ".current_bytes", sha(ROOT / "fixtures/task001/v0.1" / (dataset.lower() + ".xpt")) == result["sha256"])
        check("independent_raw." + dataset + ".rows", result["rows"] == facts["row_count"])
        for descriptor in result["descriptors"]:
            name = descriptor["name"]
            check("independent_raw." + dataset + "." + name, descriptor["width"] == facts["storage_widths"][name]
                  and descriptor["label"] == facts["labels"][name]
                  and ("string" if descriptor["type"] == 2 else "double") == facts["types"][name]
                  and result["aggregates"][name]["missing"] == facts["missing_counts"][name]
                  and result["aggregates"][name]["distinct_nonmissing"] == facts["nonmissing_distinct_counts"][name])
        for name, length in facts["observed_max_content_lengths"].items():
            check("independent_raw." + dataset + ".content_length." + name, result["aggregates"][name]["max_content_bytes"] == length)
    run = load("artifacts/TASK-001/materials-04/run.json")
    checks = load("artifacts/TASK-001/materials-04/checks.json")
    case_ids = ["T001-C" + str(i).zfill(2) for i in range(1, 25)]
    check("materials_109_actual", len(checks["checks"]) == checks["check_count"] == run["executed_checks"] == 109 and all(c["result"] == "passed" for c in checks["checks"]))
    check("selected_cases_24", run["selected_case_ids"] == [c["id"] for c in expected["cases"]] == case_ids)
    check("no_skipped_or_engine", run["skipped_checks"] == 0 and run["engine_cases_executed"] == 0)
    check("F003.registration_only", all(c.get("material_registration_status") == "registered" and c.get("engine_behavior_result") == "not_run" and "automated_material_check" not in c for c in load("artifacts/TASK-001/materials-04/case-readiness.json")["cases"]))
    coverage = load("expectations/task001/v0.1/coverage.json")["rows"]
    expected_requirements = [f"FR-{i:03}" for i in range(1, 19)] + [f"NFR-{i:03}" for i in range(1, 8)] + [f"AC-{i:02}" for i in range(1, 12)]
    check("coverage_complete_registry", sorted(r["requirement"] for r in coverage) == sorted(expected_requirements))
    check("coverage_no_behavior_claim", all(r["engine_behavior_result"] == "not_run" and r["coverage_status"] in ["partial", "not_covered"] and r["deferral_approval"].startswith("pending_chris") for r in coverage))
    check("patch_family", "/family/SDTM/" in load("fixtures/task001/v0.1/patch.json")["object_id"] and "/family/SDTM/" in load("fixtures/task001/v0.1/dependencies.json")["object_id"])
    documents = load("artifacts/TASK-001/documents-01/checks.json")
    check("documents_361_actual", documents["result"] == "passed" and documents["check_count"] == len(documents["checks"]) == 361 and all(c["result"] == "passed" for c in documents["checks"]))
    document_version_deltas = []
    for row in documents["files"]:
        if sha(ROOT / row["path"]) != row["sha256"]:
            document_version_deltas.append({"path": row["path"], "old_sha256": row["sha256"], "current_sha256": sha(ROOT / row["path"]), "reason": "Task card only: submission filename index corrected; final documents-02 rerun required after administrative closeout"})
    check("document_changes_limited_to_task_index", all(row["path"] == "docs/tasks/TASK-001.md" for row in document_version_deltas))
    rebuild = load("artifacts/TASK-001/rebuild-01/checks.json")
    check("rebuild_three", rebuild["result"] == "passed" and len(rebuild["checks"]) == 3 and all(c["fixed_sha256"] == c["rebuilt_sha256"] == sha(ROOT / "fixtures/task001/v0.1" / c["file"]) for c in rebuild["checks"]))
    gates = load("expectations/task001/v0.1/gate1-checklist.json")
    check("gate_pending", gates["gate1"] == "pending_chris" and gates["checks"][-1]["execution_result"] == "not_run" and expected["business_confirmation"]["status"] == "pending")

    paths = {ROOT / p for p in ["AGENTS.md", "GOALS.md", "REQUIREMENTS.md", "ARCHITECTURE.md", "PLANS.md", "README.md", ".gitignore", "docs/tasks/TASK-001.md", "docs/tasks/TASK-001-findings.json", "docs/approvals/APR-20261020-01.md", "baselines/BL-20261020-01/manifest.json"]}
    for folder in ["docs/contracts", "fixtures/task001/v0.1", "expectations/task001/v0.1", "tools/task001", "artifacts/TASK-001/start", "artifacts/TASK-001/materials-01", "artifacts/TASK-001/materials-02", "artifacts/TASK-001/materials-03", "artifacts/TASK-001/materials-04", "artifacts/TASK-001/rebuild-01", "artifacts/TASK-001/documents-01", "artifacts/TASK-001/references"]:
        paths.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    paths.add(OUT / "independent-xpt-raw-v1.json")
    paths.add(OUT / "independent_xpt_audit.py")
    failures = [a for a in assertions if a["result"] != "passed"]
    closures = [
        {"finding_id": "F-001", "original": "Two different DDE URLs shared dde-define.yaml and one frozen hash was unrestorable.", "retest": "All 7 distinct asset paths, sizes and hashes independently recomputed; sources-initial retained.", "technical_status": "closed_fixed"},
        {"finding_id": "F-002", "original": "Dataset serialization initially omitted family and added it only after name collision.", "retest": "Contract requires family permanently; patch/dependency identities match; cross-family identity never rekeys old objects.", "technical_status": "closed_fixed"},
        {"finding_id": "F-003", "original": "materials-01 case registration falsely assigned automated_material_check=passed unconditionally.", "retest": "materials-04 has registered only, 24 explicit selected IDs, engine results not_run; reviewed revised script.", "technical_status": "closed_fixed"},
        {"finding_id": "F-004", "original": "Contract described checker as stdlib-only despite pandas/pyreadstat imports.", "retest": "Contract now accurately distinguishes library audit from independent stdlib byte audit and imports.", "technical_status": "closed_fixed"},
    ]
    report = {
        "review_id": "T001-IR-01", "reviewer": "/root/review_contract", "reviewed_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
        "technical_result": "failed" if failures else "passed", "open_technical_blockers": failures,
        "business_confirmation": "pending_chris", "gate1": "pending_chris", "task_acceptance": "not_accepted",
        "scope": "Independent technical readiness review of Task 001 materials, not approval of business semantics or engine execution.",
        "reading_record": ["AGENTS all", "GOALS all", "PLANS current/index/stages/CTRL-01/02/03/change/latest handoff", "REQUIREMENTS all FR/NFR/AC/OQ/CTRL-05/06", "ARCHITECTURE all, especially sections 1-6/CTRL-04/ADR", "APR-20261020-01 and baseline manifest", "all task/contracts/fixtures/expected/coverage/gates/tool sources and listed evidence"],
        "selected_case_count": 24, "selected_case_ids": case_ids, "manual_cases_reviewed": 24, "skipped_cases": [], "uncollected_cases": [], "engine_cases_executed": 0,
        "case_reviews": [{"case_id": cid, "technical_expected_review": "passed", "method": "independent manual source/contract derivation with separate raw-byte fact audit where applicable", "reasoning": note, "actual_engine_result": "not_run"} for cid, note in zip(case_ids, manual_notes)],
        "independent_evidence": "docs/tasks/task001-review/independent-xpt-raw-v1.json; 8 raw-byte assertions executed",
        "reverification_assertions": assertions, "reverification_count": len(assertions), "findings": closures,
        "architecture_judgment": "Metadata Reconciliation remains central; observed/expected/reference/approved separated; field-specific authority; sidecar retains evidence/issues/decisions; no core engine or generator implemented. DDS conceptual mappings exist but byte/character and output compatibility gaps remain explicit.",
        "long_term_retained": ["XPT", "SDTM/ADaM Spec", "aCRF/preset values", "CT/IG", "Protocol/SAP", "DDS-aligned model", "No Data", "VLM", "SUPP", "CodeList", "Define-XML 2.1", "SDRG/ADRG", "validation", "decisions/lineage"],
        "quality_gates": {"Q01_Q05": "technical review and current evidence support readiness within recorded scope", "Q06": "package script/layout inspected only; actual package hash/copy verification pending post-package evidence", "Q07": "not_run; Chris must confirm exact package, first expectations and proposed deferrals"},
        "package_script_review": "Read source: refuses existing package/submission, requires passed independent review with no blockers and passed material/rebuild/doc records, copies project-relative files, rereads copied hashes/sizes, manifest excludes itself, external submission remains pending_chris. Not executed by reviewer.",
        "document_script_review": "Read source and 361-check evidence; verifies UTF-8 readability, fence pairing, internal link target existence and table endings only; does not validate external links/anchors/semantics.",
        "document_version_deltas": document_version_deltas,
        "material_run_index": "materials-04 reran the same 109-check script after only submission-filename index correction. Expected business content and contract unchanged; materials-03 kept as history.",
        "limitations": ["No live SAS execution; byte audit is limited to the two fixed single-member ASCII fixtures and nonblank DM final cell.", "No reconciliation, patch application, runtime schema, XML, CT, P21, DDS loading or RG execution; all 24 engine behaviors are not_run.", "Reviewer did not independently repeat network retrieval; fixed reference asset bytes/URLs/hashes and relevant DDE definitions were reviewed locally.", "Q06 package has not been made during this review; subsequent actual package evidence is required.", "Chris must approve semantics/expectations, current scope and deferrals; this report does not authorize MVP 0.1.", "Any post-review administrative updates need recorded final-version checks; reviewed hashes remain historical evidence and must not be silently replaced."],
        "reviewed_objects": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(paths)],
    }
    (OUT / "final-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Task 001 独立技术审阅", "", "Chris，当前审阅范围的技术准备复核通过；未发现新增技术阻断。业务预期、延期边界及 GATE-1 仍待你确认，Task 001 未验收。", "", "- 审阅人：`/root/review_contract`；审阅编号 `T001-IR-01`。", f"- 实际选择并人工复核 C01 至 C24 共 24 例，无遗漏或跳过；另执行独立原始字节 8 断言及版本/证据复核 {len(assertions)} 断言。", "- 引擎实际执行 0 例，全部行为结果 `not_run`。材料 109 断言、文档 361 断言和三个固定 XPT 重建证据与记录版本一致。", "- 对象逐文件 SHA-256、逐例推导、断言和局限见 [final-review.json](final-review.json)；原始字节事实见 [independent-xpt-raw-v1.json](independent-xpt-raw-v1.json)。", "", "## 发现与复测", "", "| ID | 原发现 | 修复复核与技术状态 |", "|---|---|---|", "| F-001 | 两份 DDE 文件同名覆盖，来源 hash 不可恢复 | 分路径后 7 项来源逐字节/hash/大小独立核算，一致；原登记保留；`closed_fixed` |", "| F-002 | family 在碰撞后才加入，可能改变旧身份 | 契约及 patch/依赖永久含 family，后加对象不改变旧 ID；`closed_fixed` |", "| F-003 | 逐例注册无条件显示 passed | 当前仅 registered，引擎 not_run；24 个实际选中 ID 明确；`closed_fixed` |", "| F-004 | checker 依赖描述与 imports 不符 | 已区分库审计和独立标准库字节审计；`closed_fixed` |", "", "## 需求与架构判断", "", "18 条 FR、7 条 NFR、11 条 AC 均有登记，当前只标 partial/not_covered；延期仍待 Chris 确认。长期 XPT/Spec/aCRF/CT/Protocol/SAP、DDS-aligned 模型、No Data/VLM/SUPP/CodeList、Define、SDRG/ADRG、验证、决策及溯源均保留。固定样本允许验证物理区别，不能据此宣布标准符合性或生产适用。", "", "四种断言、字段责任及人工批准分开；缺文件、损坏、零行、缺变量、全缺失不合并。独立核算确认 DM 三行，SEX 缺失 3，AGE 普通点/.A/.Z 各 1，ARMCD IBM 数值 1/2/1；VS 无数据 payload。冲突和 patch 场景推导与输入及 CTRL-04 一致。DDS 对照只属参考实现的概念映射，长度字符/字节差异和兼容未验证均明示。", "", "## 质量门与局限", "", "Q06 本次只读复核了打包脚本和布局；尚未执行实际包检查，必须另存包后副本/hash 核验证据。Q07 为 `not_run / pending_chris`，阻止阶段验收及 MVP 0.1。", "", "未执行 SAS、核对引擎、patch 应用、运行时模型、XML/XSD、真实 CT、P21、DDE 加载或 RG。原始字节方法仅适用当前两个固定单 member、ASCII 夹具，不能作为通用 XPT 解析器。审阅后状态/索引更新须保留对应版本核验，不改写本次对象 hash。", ""]
    (OUT / "final-review.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"technical_result": report["technical_result"], "reverification_count": len(assertions), "failures": failures, "objects": len(paths)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
