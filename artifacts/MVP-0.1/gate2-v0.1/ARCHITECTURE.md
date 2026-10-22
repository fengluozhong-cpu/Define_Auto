# Define_Auto 架构基线

> Task 000 · v0.2 · 2026-10-19（Asia/Shanghai）
> **APPROVED -- 五份核心文件已由 Chris 批准生效。** 基线 `BL-20261020-01`；[批准范围与快照](E:/Initiation/Define_Auto/docs/approvals/APR-20261020-01.md)。本轮仅同步批准状态，正文版本沿用；明确开放的问题、未验证事实及未来任务授权仍分别管理。

## 1. 端到端结构

```text
XPT / SDTM-ADaM Spec / aCRF-EDC / CT-IG / Protocol-SAP / Issues-Decisions
                              |
                 只读适配器 + 输入清单 + 版本和定位
                              |
             原始证据与候选层：observed / expected / reference
                              |
               Metadata Reconciliation + Gap / Conflict Queue
                              |
                  人工裁决与 Patch + 批准快照
                              |
            DDS-aligned 中心模型 + Evidence / Decision Sidecar
                     /                         \
        Define 输出适配器                     RG 输出适配器
      P21 Excel -> CLI（待试验）         SDRG / ADRG 参数化事实与文本草稿
      DDS -> XML（候选，待比较）                 |
                     \                         /
          模型 / XSD / 交叉检查 / CT / P21 / 人工语义验证
                              |
               Findings 回流核对 -> 修订 -> 人工批准交付
```

验证也在输入和中心模型阶段执行，不只在产物末端。Define 与 RG 使用同一 `model_snapshot_id`，避免清单与解释不一致。P21 报告回流须记录具体输入快照及引擎版本。

## 2. 模块边界

| 模块 | 职责 | 边界 |
|---|---|---|
| Input Registry | 文件清单、内容 hash、来源类型、版本、完整性声明、保密级别 | 不扫描无关目录，不推定未提供资料不存在 |
| Source Adapters | 提取 XPT 物理属性与统计、Spec 设计、aCRF 页码／预设值、CT 参考、Protocol／SAP 结构化候选 | 保留原始值与坐标；PDF／OCR／LLM 输出需审阅，不直接写权威值 |
| Standard Provider | 装载锁定版本的 IG、CT、BC、DS、合法导出与授权 API 数据 | 离线快照可用；不因网络失败自动换成“最新”版本 |
| Reconciliation Engine | 身份匹配、字段比较、集合差异、缺口／冲突分类、规则建议 | 不依赖 Excel sheet 名称，不静默覆盖冲突 |
| Review / Patch | 供人填写缺失、选择候选、解释例外，校验 patch 的对象身份及相关依赖 | 按 CTRL-04 检测输入、标准、规则、配置和模型变化；受影响裁决需重新审阅 |
| Canonical Model | 为 Define 与 RG 提供统一、受约束、可版本化的对象与批准状态 | 内部含未决对象；可生成／可交付视图须按门槛筛选 |
| Output Adapters | 转成 P21 Excel、Define XML、SDRG／ADRG 等外部格式 | 转换损失和不支持字段必须报出，不自行补造业务事实 |
| Validation / Run Registry | 分层执行、汇总发现、记录实际覆盖与执行状态、保存运行 manifest | `not_run`、`failed`、`passed`、`not_applicable` 明确区分 |

## 3. DDS-aligned 的含义

借鉴 [DDE](https://github.com/cdisc-org/data-definition-engine) 的中心 DDS 思路，建立本项目中心模型与 DDE DDS 的字段映射。**DDS-aligned 不宣称是一个独立获批的 CDISC 标准，也不宣称天然支持全部 ADaM 或 RG。** USDM、BC、DS、DDS、Define-XML 与 ODM 是不同层次，不能相互替代；Define-XML 2.1 的 XML 目标不能直接混用 ODM 2.0 schema。

拟维护两部分：

- **Artifact Model**：Study、StandardVersion、Dataset、Variable、ValueLevel、WhereClause、CodeList、CodeListTerm、Method、Comment、Document、Origin，以及 ADaM 分析追溯的扩展。
- **Evidence / Review Sidecar**：源证据、观察统计、候选值、差异、裁决、批准、验证结果、RG 论述及其关联。若 DDE DDS 不承载这些信息，则明确保存在旁表，不能为了兼容而丢弃。

建模工具尚未选择。LinkML 是对齐 DDE 的候选，Pydantic／JSON Schema 是本地约束候选；优先比较最小字段契约与验证成本，再决定。不在 Task 000 创建代码 schema 或数据库。

## 4. 最小逻辑数据契约

| 对象 | 拟保留字段／关系 | 设计意图 |
|---|---|---|
| SourceArtifact | `source_id, relative_path, sha256, source_type, version, acquired_at, confidentiality, completeness_scope` | 不在正式 manifest 存凭证；相对路径由运行根解析 |
| Evidence | `evidence_id, source_id, locator, raw_value, normalized_value, extraction_method` | locator 为 sheet／row／column、PDF 页／注释、JSON path 或统计范围 |
| MetadataAssertion | `object_id, field_path, value, assertion_kind, evidence_ids, rule_id, review_state` | `assertion_kind` 区分 observed／expected／reference／approved；保留多个候选 |
| ReconciliationIssue | `issue_id, object_id, category, candidates, evidence_ids, severity, status` | 差异和冲突可追踪，不用一个空字符串混合所有未知情况 |
| Decision / Patch | `decision_id, issue_ids, object_id, field_path, selected_value, rationale, reviewer, decided_at, dependency_snapshot_id, validity_status, supersedes` | 依赖快照绑定输入与相关标准、规则、配置、模型及上游决定；保留旧裁决和重审记录 |
| Model / Run Manifest | `schema_version, model_snapshot_id, input_hashes, standard_versions, rule_versions, tool_versions, config_hash, decision_ids, output_hashes` | 复现及影响分析的依据；时间等运行信息与业务值分开 |
| Approval Record | `approval_id, scope, approver, approved_at, model_snapshot_id, dependency_snapshot_id, decision_ids, output_hashes, gate_evidence_ids, validity_status` | 批准绑定具体内容及证据；受影响时失效而不覆盖历史批准 |
| Finding / RG Section | `finding_id, rule_id, scope, status, evidence_ids, decision_ids`；段落另关联 `claim_ids` | 验证与 RG 解释同源；未裁决内容不能伪装成已解决 |

逻辑 ID 应稳定且在研究与版本上下文中唯一；OID 生成规则后续用固定样本验证。VLM 的身份须包含数据集、目标变量与规范化条件；不能仅用 TESTCD。条件需支持多个变量、比较操作和组合约束。SUPP 身份需结合父域及关联键语义，而非只把 QNAM 当作普通变量名。

### 4.1 CTRL-04：依赖变化、裁决有效性与批准重审

Task 001 冻结依赖快照的逻辑契约。每项裁决及相关验证／批准至少能够定位：源输入 hash、研究及对象／字段身份、适用 CT／IG、规则与转换逻辑版本、实际生效配置、模型 schema、上游决定，以及影响该结果的工具版本。快照保存对应配置与版本清单；只有 hash 而无可访问内容不足以复现。后续实现应记录可重建环境，具体格式随技术选型确定。

相关依赖变化时按以下规则处理：

1. 比较依赖快照，记录变化、影响对象及判断依据；影响范围尚不能可靠确定时，保守地将相关裁决及下游结果整体标为 `needs_review`。
2. 受影响 patch 在重新确认对象身份、适用条件和选值依据前不得自动应用；其下游模型快照、验证证据及产物批准不能继续作为当前有效结果。
3. 保留旧裁决、原始验证结果及批准记录；修订以 `supersedes` 或新的批准记录关联旧版本，不改写历史。修订后重新执行受影响检查及回归，通过 PLANS 的 CTRL-02 后才能重新批准。
4. 能证实不影响业务内容的变化可以保留原裁决有效性，但必须记录影响分析依据；纯审计时间变化不触发无意义的业务重审。新产物仍须检查内容 hash 与批准范围是否匹配。

本机制适用于“输入不变，但 CT、规则、配置或模型变化”的情况。FR-018 的影响报告与本规则共同决定是否重审，不能把“已发现变化”视为“批准已自动更新”。详细依赖字段及失效用例在 Task 001 确定，首次复用裁决前实现并验证。

## 5. 核对与权威规则

不设全局单一来源优先级，按字段建立来源责任表：

| 字段／信息 | 初始责任来源 | 冲突处理 |
|---|---|---|
| 交付文件、物理类型、存储长度、实际行数、观察值 | 实际 XPT 与完整运行清单 | 与 Spec 不同则报告；不改写 Spec 让差异消失 |
| 预期域／变量／VLM、计划 Origin／Method | 批准的 SDTM／ADaM Spec | 与 aCRF、Protocol、SAP 冲突则提出审阅；标准默认值仅作候选 |
| 页码、采集选项、采集字段映射 | aCRF／EDC 元数据及经批准桥接表 | 页码区分 PDF 物理页和印刷页；映射有版本与审阅状态 |
| CT 身份、NCI 编码与允许范围 | 指定版本 CT + 项目预设值及扩展政策 | 不用概念 C-code 直接替代 submission value；不把未观察值删除 |
| 分析意图与复杂派生解释 | Protocol／SAP、Spec、程序说明、批准决策 | 实际实施与计划的偏离必须可见，不凭任一文件单独裁定 |
| 例外原因、验证解释、最终选值 | 有权限人员的记录与批准 | 与对象及证据绑定，不能自动跨研究套用 |

映射字典保存项目／组织 CRF 字段到标准对象的规则、上下文、适用版本和审阅状态；不与 IG／CT 标准库混成一个无版本表。`aCRF Mapping Sheet` 是项目桥接格式，不是 CDISC 标准；优先利用可用结构化来源，再考虑 PDF 提取。

## 6. No Data、VLM、SUPP 与 CodeList

核对至少区分 `not_provided`、`unreadable`、`expected_missing`、`present_empty`、`present_all_missing`、`present_with_data`、`not_applicable`；名称可在 Task 001 讨论，含义不得合并。观察状态、设计预期、业务原因和 XML 序列化分开存储。

- 数据集无文件、零记录、非计划对象不同。变量未提供、全缺失不同；零记录数据集中“全缺失”不能靠空集合逻辑直接下业务结论。字符空白、SAS 普通／特殊数值缺失和部分日期等规则需分别定义。
- VLM 同时使用计划条件和实际条件；需区分“条件无记录”与“条件有记录但目标值全空”，并保留未观察的计划 VLM。不能将所有 distinct 值机械转为最终 VLM。
- 本地 XSD 支持 `ItemGroupDef/@def:HasNoData` 与 `ItemRef/@def:HasNoData`，`ValueListDef` 包含 `ItemRef`；因此 VLM 的 ItemRef 表达路径需要评估。不得向不存在的 `ValueLevelDef` 添加臆造属性。具体语义、Comment 位置／条件及生成器行为须以规范和最小夹具验证后冻结。
- SUPP 按 `RDOMAIN、USUBJID、IDVAR、IDVARVAL、QNAM、QLABEL、QVAL、QORIG、QEVAL` 等可用字段理解父子关系及 QVAL 元数据；计划 QNAM 与实际 QNAM 比较，必要时形成 QVAL 的 VLM／CodeList。QNAM 是 qualifier 标识，不等于 QVAL 的允许值清单。
- CodeList 分别保存标准全集、项目允许值、采集预设值和观察值。处理可扩展性、外部词典、同义词、显示值与提交值的区别，NCI code 带标准包版本。
- XPT 字符存储长度、观察最大内容长度及 Spec 声明长度单列；不能以样本最大长度覆盖设计长度或字节语义。

## 7. P21 与 DDE 的可替换适配器

**候选 A：中心模型 -> P21 Excel -> Community CLI -> Define。** 优点是可沿用熟悉流程；风险是版本、模板列、VLM／No Data／ADaM 及生成命令支持未在本机确认。官方验证 CLI 文档仅证明验证路径，不能单凭它确认所有生成参数。

**候选 B：中心模型 -> DDE／odmlib 或自有序列化适配器 -> Define。** 需比较字段覆盖、稳定性、许可证、ADaM 支持和验证结果。DDE 是参考实现，不能承诺开箱替代本项目核对与溯源能力。

先用同一最小夹具做能力矩阵，必要时仅保留一条首发路径。没有证据前不锁定 P21，也不同时实现两个完整后端。任何适配器丢字段、遇占位符或不支持对象时必须失败或输出明确缺口，不能静默忽略。

## 8. RG 与 LLM 的边界

SDRG 与 ADRG 模板分别版本化。事实清单由中心模型确定性渲染；项目问题、P21 comment／回复、特例和决策形成带证据的论述输入。Protocol／SAP／程序说明的提取可使用 LLM 候选，须记录模型／提示版本、来源位置和审阅状态，并按授权控制外发。

LLM 不补写未知 No Data 原因，不自行认定分析符合 SAP，不把未关闭 finding 描述成已解决。复杂统计解释与 ARM 若纳入，需单独制定审阅和溯源要求。最终产物保留人工审签及未决事项清单。

## 9. 验证与工程选择

建议本地 CLI、文件优先、Python 为候选；不在基线阶段引入 Web 服务、数据库或多代理。后续项目内依赖需有必要性与版本记录。XSD 保持完整 include／import 相对布局，记录来源、版本及 hash，以 `define2-1-0.xsd` 为本地候选入口。

验证层为输入完整性、模型约束、核对预期结果、XSD／OID／引用完整性、XPT-Define-RG 交叉一致性、CT、外部验证和人工语义审阅。失败路径包括乱码／读失败、输入不完整、冲突、过期 patch、工具不可用和字段不支持。输出写新运行目录，避免覆盖旧结果。

产物是否可审阅、阶段是否完成及是否批准交付，统一遵循 PLANS 的 CTRL-02；生成器成功退出不能自行提升这些状态。验证记录关联确切的模型、依赖及产物快照，缺陷与例外关闭遵循 REQUIREMENTS 的 CTRL-06。

## 10. 设计决策登记

| ID | 提案 | 状态 | 依据／取舍 |
|---|---|---|---|
| ADR-001 | 核对核心先于生成器全面开发 | Accepted（APR-20261020-01，方向层面） | 先证实预期与观察差异可被正确解释，减少生成错误被固化 |
| ADR-002 | DDS-aligned 中心模型 + 溯源旁表 | Accepted（APR-20261020-01，方向层面） | 借鉴 DDE，但保留项目特有审阅、ADaM 与 RG 信息 |
| ADR-003 | 本地文件与 CLI 优先 | Accepted（APR-20261020-01，方向层面） | 降低学习和运维成本；数据库／服务由实际规模驱动 |
| ADR-004 | 经授权的版本化标准快照，支持离线 | Accepted（APR-20261020-01，方向层面） | 不把会员 API 或“最新版本”作为唯一前提 |
| ADR-005 | P21／直接 XML 路径先做最小试验再选择 | Open | Community 生成能力与模板保真尚未实测 |
| ADR-006 | 确定性事实 + LLM 候选 + 人工批准 | Accepted（APR-20261020-01，方向层面） | 事实和表达分离，避免不可追溯的自动裁决 |

批准须记录到 PLANS；此表不使用“未反对即已锁定”的规则。
