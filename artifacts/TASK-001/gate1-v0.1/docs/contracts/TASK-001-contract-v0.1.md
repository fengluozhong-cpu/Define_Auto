# Task 001 最小契约 v0.1

> DRAFT / review_ready 目标；CHG-005；待 Chris 在 GATE-1 批准。继承 BL-20261020-01，未替换已批准 ARCHITECTURE。本文是项目契约提案，不是 CDISC 标准。

## 1. 范围与输入登记

先固定完全合成研究 `SYN001` 的 SDTM DM、VS、AE、CM，及结构化 JSON Spec。XPT 是实际物理事实，Spec 是合成设计意图；两个来源均不代表真实研究批准。未实现核对、patch 应用或模型／XML／RG 生成。目标机构、IG／CT 包版本保持未选；不生成“符合 SDTMIG”的结论。

输入 manifest 的 `source_id` 在研究中永久唯一；内容变化保留 ID，另增 source version／hash；来源被另一文件替代须记录 supersedes。字段为 `source_id, relative_path, sha256, source_type, version, acquired_at, confidentiality, completeness_scope, provision_status`；路径以夹具根为基准，必须是根内相对路径，不包含凭证。`provision_status=provided/not_provided` 是提交声明；读取结果另为 `not_attempted/readable/unreadable`。没有文件时 hash 为 null，原因与预期路径显式保存；有文件则必须有实字节 SHA-256。文件存在不代表可读或完整。

`completeness_scope` 必须说明 planned objects、实际交付范围、closed/open 声明及依据。此例 planned datasets 为 DM/VS/AE/CM，AE 明确未提供，因此提供范围 incomplete。aCRF、CT、Protocol、SAP 本轮未提供，不推断不存在；完整性只对所声明的合成包负责，不对真实研究负责。Spec 未支持列／重复对象／歧义必须成为缺口，禁止静默忽略。

## 2. 身份与可扩展对象

业务身份采用结构化元组；可读编码以 `/` 分隔，每段先按 UTF-8 百分号编码（safe 仅字母、数字、`-._~`），避免分隔符碰撞。研究 ID 区分大小写并保留原文；本批 dataset/variable 仅允许 ASCII 大写 `[A-Z][A-Z0-9_]{0,7}`，不默默折叠不合法名。版本／输入 hash 不属于业务 object_id，属于断言与依赖快照。重命名默认新对象，需显式人工对应，不用行号合并对象。

| 对象 | 身份与后续约束 |
|---|---|
| Study | `study/SYN001` |
| Dataset | `study/SYN001/family/SDTM/dataset/DM`，study、family、dataset 三部分始终必需；跨 family 不合并，后加同名对象不改变既有 ID |
| Variable | `study/SYN001/family/SDTM/dataset/DM/variable/SEX`；父 Dataset 必需 |
| ValueLevel / WhereClause | 预留 dataset、target variable、类型化条件 AST；AND/OR/操作符/类型显式，不只用 TESTCD。等价规范化尚未实现，未经证明不合并，MVP 0.2 前补契约与夹具 |
| SUPP qualifier | 预留父域、关联键语义和 QNAM；逐行关联另含合成关联键，不能仅凭 QNAM 合并；MVP 0.2 前补夹具 |
| CodeList/Term | 标准包版本 + CodeList ID + term identity；项目允许、采集预设和 observed 集合分别存储；版本不混用，无 NCI code 不伪造 |
| Method/Origin/Comment/Document | 可有稳定 ID、原始来源和批准关联；ADaM 分析追溯、Protocol/SAP、RG claim 均保留扩展路径 |

本批所有对象限定 family=SDTM；序列化始终含 family，未来 ADaM 同名对象不会改变旧 ID。断言 `assertion_id` 由 object、field_path、kind、source version/locator 和候选值摘要构成；issue 稳定键由 object、field、category、规则语义 ID 构成，候选／状态变化为 issue revision，不能因时间戳改变身份。同字段多来源的冲突保存在同 issue 的 candidates，不能后读覆盖先读。最终 XML OID 另由适配器契约确定。

## 3. 断言、证据与字段责任

每条 `MetadataAssertion` 包含 `assertion_id, object_id, field_path, value, assertion_kind, evidence_ids, rule_id, review_state`。Evidence 包含 `evidence_id, source_id, source_version, source_sha256, locator, raw_value, normalized_value, extraction_method, tool_version`；类型转换必须显式，null 表示未知而非空字符串。XPT locator 为 member/variable/聚合范围，必要时引用字节偏移；Spec 为 JSON Pointer；受试者明细不写日志。空格去除等规范化保留 raw，并按版本规则执行。

| kind／字段 | 责任来源 | 禁止的推断 |
|---|---|---|
| observed：文件、物理类型、存储字节长度、label、行数、缺失／distinct 聚合 | 可读 XPT + 输入清单 + 提取证据 | 不将 observed 最大内容长度当 Spec 长度 |
| expected：计划域／变量、声明类型／长度、Origin/Method/CodeList | 项目 Spec；本批仅合成 Spec，review_state=draft | 不凭 XPT 缺席删除设计对象 |
| reference：标准身份、约束、允许范围 | 经授权且锁定版本的 IG／CT | 未锁版本形成 gap；标准不能自动决定项目事实 |
| approved：字段最终选值、No Data 原因、例外 | 有权限的人对当前候选和依赖快照的批准记录 | Agent 候选、测试 patch 不具有真实批准效力 |

本批 Origin/Method/CodeList 只有保留字段与候选，不验证内容语义；不存在真实 approved 断言。XPT、Spec、aCRF、CT、Protocol/SAP 的责任按 ARCHITECTURE §5 分字段，冲突须并列审阅，不设全局权威顺序。

## 4. 状态分层与差异

以下维度不可合成一个枚举：

| 维度 | 枚举／含义 |
|---|---|
| 供应／读取 | not_provided 与 unreadable 分开，不能据此断言无数据 |
| 观察 | present_empty（数据集零行）、variable_absent（已读父域缺变量）、present_all_missing（父域行数大于零且该变量全部缺失）、present_with_data（至少一个非缺失值）、unknown（无可靠观察） |
| 设计差异 category | expected_missing、unexpected_object、field_conflict、reference_error、unsupported_metadata、ambiguous_identity；缺文件时 expected_missing 并关联供应 not_provided，不等于 variable_absent |
| issue status | open -> in_review -> resolved；亦可 rejected／needs_review。resolved 必须有关联且当前有效的人工决定，不等于该产物已获批准 |
| 业务解释与序列化 | no_data_reason 为 null 或有证据且待批准的候选；XML HasNoData 不由上述状态自动赋值，OQ-04 保持开放 |

本批字符缺失只定义 ASCII 全空格／空串；数字普通 `.` 与特殊 `.A/.Z` 都是 missing，但 missing code 各自保留，不按 0 处理。partial date、Unicode 空白、其他特殊缺失尚未覆盖，不能声称完整 AC-02。零行 VS 的每变量 missing_count=0、nonmissing_count=0，状态为父域 present_empty 下的 `unknown`，不判全缺失。缺变量 ARM 的统计为 null，不是 0；不可读 CM 的行数和变量清单为 null。

字段比较先确认对象和可比语义：Spec declared length 与 XPT storage length 分列，字符长度可比较；数值 Spec length 是 SAS 存储字节，不当作有效数字位数；观察内容长度另列，非 ASCII 字节／字符长度须在 MVP 0.1 增加夹具。类型、label、长度三类冲突不能只报一个“不同”。

## 5. 人工 patch、依赖失效

Patch 字段为 `decision_id, issue_ids, object_id, field_path, selected_value, rationale, reviewer, decided_at, dependency_snapshot_id, validity_status, supersedes, authorization_status`。值和引用必须类型正确、对象存在、当前候选／选值依据可定位；未知值／占位符不能进入 approved。fixture patch 的 `authorization_status=synthetic_only`，不得实际应用为用户批准。相同 decision_id／内容重复导入不得新增业务变化；同 ID 不同内容应拒绝，修订使用新 ID + supersedes。

依赖快照保存可恢复的输入、study/object/field 身份、IG/CT、规则及变换、有效配置、模型 schema、上游决定、影响结果的工具版本及内容 hash。未选择的标准也须显式 `not_selected`，不能虚构版本。内容寻址摘要使用规范化 UTF-8 JSON（sorted keys、无无意义空白、禁止 NaN），纯 run timestamp 排除；涉及业务内容的时间不得排除。

任一相关依赖变化，保守将 patch、下游模型／验证／批准设 `needs_review`；影响范围未能证明时整条关联链重审。旧记录保留，不能将旧批准就地“升级”。仅纯审计时间变化可不触发业务重审，但记录影响依据。输入 hash 未变而 CT/rule/config/schema/upstream decision/tool 变化的用例均在预期文件中列明。对象／字段身份变化拒绝自动应用。复核通过并获新批准才可恢复适用性；本任务不实现这些行为。

## 6. 运行证据与交付

正式布局：`artifacts/<task_id>/<run_id>/run.json`（命令、开始结束、环境、收集/执行/跳过数、返回码）、`checks.json`（逐项断言）、`coverage.json`（需求条款/用例/独立预期/实际证据/结果）、`inputs-manifest.json`（确切输入）、`outputs-manifest.json`（产物角色与 hash）。MVP 运行再增加 model snapshot、issues、patch applicability、validation、approval；当前不生成虚假的模型结果占位文件。

Task 001 固定交付包位于 `artifacts/TASK-001/gate1-v0.1/`，复制契约、输入、独立预期、工具、依赖与审阅及实际检查，manifest 排除自身避免递归。包内容修改必须新目录。批准记录未来另存并绑定 manifest hash，不能回写批准对象。审计时间与业务快照分列；工具检查 passed、引擎 not_run、GATE-1 pending_chris 分别保存。

## 7. DDS 映射与技术最小方案

本阶段采用 JSON 文档与 Python 文件 CLI；不选 LinkML/Pydantic/数据库，不建立 P21 sheet 作为模型。夹具制作／库读取审计使用项目内 pandas + pyreadstat（可读写 XPT 5），原始 XPT 结构另用 SAS 官方布局和 Python 标准库独立检查；材料检查脚本只检查固定夹具和材料结构，不产生核对差异或应用 patch。包版本记录于 requirements-fixtures.lock.txt；这不是核心引擎依赖批准。

上游 DDE README 与 define.yaml 在 references/sources.json 绑定 commit／hash，见本任务技术依据。对 Dataset/Variable/ValueLevel/CodeList/Method/Origin 等仅建立概念映射；精确字段保真和转换能力须 MVP 0.3 逐项实验。evidence/assertions/issues/patches/approval/RG claims 属本项目 sidecar，绝不声称 DDE 原生承载。ADaM/Protocol/SAP/VLM/SUPP/CT/No Data/XML/RG 与所有 GOALS 对象保留，延期需在覆盖表可见；DDE 上游文件是参考实现，不是标准规范。
