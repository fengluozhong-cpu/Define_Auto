# TASK-001：核对契约、合成样本与独立预期

> v0.1 · 2026-10-20 · `accepted` · 交付状态 `approved`（作为后续实现依据）· GATE-1 `passed`；批准记录 [APR-20261020-02](../approvals/APR-20261020-02.md)。

当前结论以 §8 及外置批准记录为准。§1–7 保留形成材料、技术检查及分组审阅时的历史状态，不能将其中待批准文字当作最新状态；冻结包未回写。

## 1. 任务卡与完成契约

| 字段 | 本次记录 |
|---|---|
| task_id / baseline_id | TASK-001；已生效 `BL-20261020-01`，批准依据 APR-20261020-01；本任务新增内容不自动成为基线 |
| authorization | Chris 于 2026-10-20 在本会话明确授权六项 Task 001 工作，包括独立子 Agent 审阅；不含核对引擎、Git 提交／推送、公开发布、全局安装或保密数据外发 |
| depends_on | Task 000 已批准核心五份文件；本地批准记录及快照；依赖版本、起始工作区和保护文件 hash 固定到 `artifacts/TASK-001/start/dependencies.json` |
| reading_record | AGENTS 全文 v0.4；GOALS 全文 v0.1；PLANS 全文 v0.4，重点 §1–4、CTRL-01/02/03、§6/8；REQUIREMENTS 全文 v0.3，含全部 FR/NFR/AC/OQ 和 CTRL-05/06；ARCHITECTURE 全文 v0.2，含 §1–4.1、字段责任、长期对象及 ADR；APR 全文、manifest 与批准检查附件；TASK-000 §11 及关联历史交接；README。未读取无争议的 discussion 或外部知识库 |
| requirements | G-01 至 G-08 保留；当前重点 FR-001/002/003/006/007/008/015/018，NFR-001 至 007；AC-01/02/05/08/11 的明确子集；CTRL-01 至 06 |
| acceptance_scope | 形成契约和固定夹具／独立预期，审查可恢复、可定位、覆盖透明；只核验材料和夹具，不宣称核对行为实现。业务预期和 GATE-1 由 Chris 确认 |
| change_scope | 新建本卡、`docs/contracts/`、`fixtures/task001/`、`expectations/task001/`、`tools/task001/`、`artifacts/TASK-001/`、独立审阅目录；仅更新 PLANS 当前入口／变更／交接和 README 使用说明；项目内夹具环境与忽略规则。五份已批准核心正文不重写，冻结基线不改 |
| fixtures / expected_results | 完全合成 SDTM 小样本及 JSON Spec v0.1；独立预期手工推导先于核对实现；确切 hash 随正式交付 manifest 固定；Chris 确认 pending |
| required_checks | Q01 基线及保护文件完整性；Q02 固定输入、hash／结构／XPT 事实；Q03 独立手工推导与复核；Q04 覆盖、状态与延期；Q05 独立技术审阅及缺陷复测；Q06 可恢复交付快照；Q07 Chris 业务确认／GATE-1；详见下文及覆盖文件 |
| failure_rule | Q01–Q06 必需检查失败、未运行、零收集或阻断技术发现未关闭时不宣称技术检查完成；Q07 未确认则不 accepted，不进入 MVP 0.1；未知业务语义保留待确认，不自行批准或假定不适用 |
| review | 独立 Agent `/root/review_contract`；只审阅，不替代 Chris 批准；审阅对象 hash、原始发现、处理与复核存 `docs/tasks/task001-review/` |
| completion / acceptance | 实施者仅声明修改／检查；技术审阅由独立 Agent 确认；阶段及业务验收人 Chris，时间和结论尚无 |

## 2. 成果、检查与覆盖

检查布局为 `artifacts/TASK-001/<run_id>/`，输出目录只增不覆盖。运行证据与业务核对结果分列；本任务没有核对引擎，全部 24 例引擎行为 `not_run`。`review_ready` 只表示可审阅，不能由此判定验收。

| 成果角色 | 正式位置／版本 | 状态与允许用途 |
|---|---|---|
| 项目最小契约 | [contract v0.1](../contracts/TASK-001-contract-v0.1.md) | DRAFT；输入、身份、字段来源、断言、状态、patch、依赖、运行布局；待 GATE-1 冻结 |
| 技术依据及具体决策 | [technical basis v0.1](../contracts/TASK-001-technical-basis-v0.1.md) | Verified-local/doc 与提案分列；包含 DDS 字段映射差距及四项批准建议 |
| 固定合成输入 | [input manifest](../../fixtures/task001/v0.1/input-manifest.json)、同目录 source-data/spec/patch/dependencies/dependency-changes/spec-changed 及 dm/vs/cm.xpt | v0.1；3 个 XPT 文件，其中 CM 故意损坏；AE 故意不存在，禁止以空文件替代。全部合成，不是标准符合性样本 |
| 独立预期 | [expected v0.1](../../expectations/task001/v0.1/expected.json) | 手工推导 24 例；来源、算术和未知业务语义明确；Agent 复核不能代替 Chris 确认 |
| 需求覆盖 | [coverage v0.1](../../expectations/task001/v0.1/coverage.json) | FR 18 + NFR 7 + AC 11 共 36 行，条款／用例／预期／证据／结果／延期阶段分列；所有延期待 Chris 确认，不是已批准例外 |
| 质量门 | [gate1 checklist v0.1](../../expectations/task001/v0.1/gate1-checklist.json) | Q01–Q07 均必需；清单初始执行栏保留 pending，当前实际结果以本卡及最终外置提交核验为准；Q07 未运行阻止验收 |
| 可重跑工具／环境 | [build_fixtures.py](../../tools/task001/build_fixtures.py)、[check_materials.py](../../tools/task001/check_materials.py)、[fixture lock](../../tools/task001/requirements-fixtures.lock.txt) | Python 3.12.13 项目 venv；只制造／检查固定夹具，不包含 Spec-XPT 比较、patch 应用或模型生成；环境可重建，不将 venv 作为正式产物 |
| 一手资料固定证据 | [sources.json](../../artifacts/TASK-001/references/sources.json) 及列出的副本 | DDE 固定 commit、SAS 官方布局、pyreadstat API 和许可证；参考实现不是标准。初始同名路径错误保留为 F-001 |
| 起始／保护依赖 | [dependencies.json](../../artifacts/TASK-001/start/dependencies.json) | 原基线 7 文件及当前批准同步 8 文件匹配；当前与批准前快照不混称逐字节相同 |
| 材料检查证据 | `artifacts/TASK-001/materials-01/`、`materials-02/`、`materials-03/` 及最终 `materials-04/` | 01：102 断言；02：109 断言；旧结果保留，最终版本看 04 及其对象 hash。01 的 case-readiness 误标问题见 F-003，不能用其作为当前通过证据 |
| 固定 XPT 重建证据 | [rebuild checks](../../artifacts/TASK-001/rebuild-01/checks.json) | 新目录重建 dm/vs/cm 三文件，逐字节 SHA-256 全相同；仅 XPT 物理复现，不是引擎业务稳定性测试。正式证据与 build record 已脱离 work 目录保存 |
| 独立原始字节证据 | [independent raw audit](task001-review/independent-xpt-raw-v1.json)、同目录 independent_xpt_audit.py | 独立 Agent 用标准库定位 headers、解 NAMESTR/IBM numeric；8 断言 passed，不读主 builder/checker，不用 pyreadstat/pandas |
| 独立发现及处理 | [finding register](TASK-001-findings.json)、`docs/tasks/task001-review/` 最终审阅 | F-001 至 F-004 保留原证据、修订和复测；技术关闭须独立审阅确认 |
| 拟批准交付快照 | `artifacts/TASK-001/gate1-v0.1/` 及其 manifest | 由包制作脚本固定全部材料副本与 hash；外置 `gate1-v0.1-submission.json` 记录实际包核验。只有生成并核验后才成立，不能由本行推定已经批准 |

当前输入 dm.xpt SHA-256=`fa525a236c6aec06a0bbb4edbf5838b93c8b2782a7ba4e03a71710b7ed82a0f7`；vs.xpt=`3216c84eaa21ff1291543f2e681836fd6dba9e1f18c78661d8ef102ef21f1e22`；cm.xpt=`3ec294e0af5b7d2956467a4c9a96e242e19c07e153638d133daba3873236007a`。其余文件精确版本以 run inputs manifest、审阅 object hashes 和最终包 manifest 为准。

首轮实际依赖：Python 3.12.13、pandas 3.0.6、pyreadstat 1.3.6，完整安装版本在 lock。开始前系统 Python 3.14.4 没有这些库，因此建立项目本地 `.venv-task001`，未全局安装；公开技术资料下载仅获取公共 URL，无保密资料或账户数据外发。未访问 P21／CDISC 账户，也未运行 XSD／DDE／P21；这些不是本任务材料检查，不记作通过或自动 not_applicable。

### 2.1 质量门判定口径

| check_id | 当前实际检查／范围 | 结果判定 |
|---|---|---|
| Q01 | 实际批准 manifest/7 份快照、当前批准同步 8 份文件、保护文件 hash | start 和 materials 的逐项实证；保护文件后续变化则阻断相关检查 |
| Q02 | 固定输入/缺席/损坏/零行/缺失/物理属性及简单 Spec 结构 | materials 只核验固定事实；三文件重建同字节另有证据 |
| Q03 | 手工推导 C01–C24；原始来源定位；独立原始字节复核 | 独立技术复核与业务确认分列，业务预期待 Chris |
| Q04 | 36 行条款覆盖、24 例、自动/人工理由、延期与落实阶段；长期对象保留 | 覆盖只是 partial/not_covered；所有引擎实际结果 not_run |
| Q05 | 独立 Agent 审阅对象版本、F-001 至 F-004 原发现/修订/复测 | 以最终独立报告为准；报告前不宣称审阅通过 |
| Q06 | 正式包每个副本可读取/hash 一致；对象/运行/预期/依赖版本可恢复 | 以 `gate1-v0.1-submission.json` 的实际检查为准，不凭目录存在判通过 |
| Q07 | Chris 确认包内样本、字段责任、状态/预期、DDS/延期边界和最小契约 | `not_run / pending_chris`；阻断 Task 001 验收和 MVP 0.1，Agent 无权批准 |

## 3. 未决项与批准对象

OQ-01 首批研究选 SYN001、DM/VS/AE/CM 和 JSON Spec，24 例预期；OQ-05 建议只冻结本项目契约、锁定 DDE commit 作概念映射参考，暂不引入 LinkML、不宣称可直接装载 DDE，精确导出能力承接 MVP 0.3。方案和影响见 technical basis；两项均待 Chris 确认，不能记为 closed。

需确认的业务含义：ASCII 全空格／普通点与 .A/.Z 缺失，零行不判全缺失，缺文件／读失败／缺变量不互换，No Data 原因及 HasNoData 保持 null；字段冲突人工选择而非全局覆盖；patch 相关依赖变化保守重审。合成 patch 不具真实批准效力。

OQ-02/03/04/06/07/08/09/10 保留原责任与阶段；复杂日期、Unicode、其他特殊缺失、重复/歧义 Spec 和运行时模型约束待 MVP 0.1；aCRF/CT/VLM/SUPP/完整 No Data 待 MVP 0.2；XML 与 DDE/P21 保真待 MVP 0.3；SDRG、ADaM/ADRG、Protocol/SAP/USDM 及集成均继续保留，不删除。延期精确条款和承接阶段在 coverage.json；Chris 尚未确认承接，不视为已获豁免。

批准对象是最终 `gate1-v0.1/manifest.json` 列出的审阅包，不是当前可变目录或聊天摘要。后续实际批准记录必须单列人/日期/范围/manifest hash；本任务不伪造批准，不自动启动 MVP 0.1。

## 4. 交接

最后完成点：契约、合成输入、独立预期、覆盖和门清单已形成，起始依赖与材料检查及独立原始字节复核已保存；修订及最终技术复核／交付包状态随 §5 最新实际记录补入。无持久服务，无 Git add/commit/push，无全局安装或用户资料处理。

接续入口：先按 AGENTS 读取当前文档和本卡，核对 start、最终 run inputs manifest、独立报告及包 manifest；相同依赖下只复核新增影响，不重复全部历史。若 Chris 批准 GATE-1，先按 CTRL-03 在包外登记批准绑定，不回写包；再依据明确授权建立 MVP 0.1 任务卡、冻结独立预期并实现核心。若有调整，保留当前包/旧预期/旧失败证据，新版本包再审，不覆盖 v0.1。Q07 尚缺 Chris 业务与阶段确认，当前不得 accepted。

## 5. 最新执行／审阅及阶段汇总

Task 001 仅一个实际开展任务，未另建空子任务；四项审阅发现属于本任务修订，并不构成已获业务批准。

2026-10-20：材料修改及技术检查完成。最终 `materials-04` 执行 109 项材料断言，109 passed、0 failed、0 skipped；实际登记并选择 C01–C24 共 24 例，引擎实际执行 0 例。`materials-01/02/03` 全部保留，01 的逐例材料 passed 标记已在 F-003 明确纠正；不能用旧登记提升当前行为结果。三份 XPT 在新目录重建逐字节相同（rebuild-01）；独立 raw audit 8 断言通过。

独立审阅 `T001-IR-01` 记录时间为 2026-10-20T10:02:40.923873+08:00，见 [最终报告](task001-review/final-review.md) 和 [逐例判断／68 个对象 hash](task001-review/final-review.json)。24/24 例独立人工复核，无跳过／漏收集；另有 97 项版本／证据复核。`technical_result=passed`、`open_technical_blockers=[]`；F-001 至 F-004 独立确认 `closed_fixed`，发现登记只增加关闭记录，原发现与旧证据保留。未更改独立预期以迁就任何实现。

Q01–Q05 技术准备检查完成；Q06 在本卡冻结后由 `package_gate1.py --package-id gate1-v0.1` 实际复制并重读每份副本，判定保存在包外 `artifacts/TASK-001/gate1-v0.1-submission.json`，不是批准记录。最终任务／PLANS／发现状态注记更新后运行 `check_documents.py --run-id documents-02`；361 项的 documents-01 原结果仍保留。交付时需核对 documents-02 和包后实际结果，未生成或失败即阻断 Q06，不可仅凭本段假设成功。审阅后仅状态／索引变更，由最终外置核验记录保留差异，不回写独立报告原 hash。

当前产物 `review_ready`，任务 `blocked` 的具体原因是 Q07 必需业务确认尚未发生；没有未关闭技术阻断。阶段 Task 001 **未 accepted**，GATE-1 **pending_chris**，没有验收人／批准时间。Q06 的包后核验通过也不消除 Q07；只有 Chris 对确切 manifest 确认，才可按 CTRL-03 另行登记批准。四项具体判断方案见 technical basis，未解决事实继续留为 OQ。

下一步只等待 Chris 审阅 GATE-1 包或提出调整。此处不是暂停长期项目，也未自行进入 MVP 0.1。其他 Agent 从 PLANS 与本任务卡接续，读取最终包／实际核验／独立审阅和 Q07 状态即可定位最后完成点。

## 6. 分组业务审阅记录

### T001-BR-01：第 ① 组已确认

记录日期：2026-10-20（Asia/Shanghai；消息精确时间未提供）。确认人：Chris。授权来源：本会话在第 ① 组中文审阅表之后的直接回复：“第一组都同意，符合业务判断。”

本记录只确认下列业务规则，对应 [gate1-v0.1 独立预期](../../artifacts/TASK-001/gate1-v0.1/expectations/task001/v0.1/expected.json) 的 C02–C07。绑定 [包 manifest](../../artifacts/TASK-001/gate1-v0.1/manifest.json)，本次重读 SHA-256 为 `b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3`。中文解释的确认不扩展为包内全部字段、全部用例或契约的批准。

| 已确认规则 | 关联用例 |
|---|---|
| 计划有 AE 但未提供文件：报告缺文件，等待补充或解释，不能推断无 AE 数据 | C02 |
| CM 文件已提供但无法读取：报告读取失败，等待修复，不能推断无数据 | C03 |
| VS 有表头但零行：记录零行，不能据此判变量全缺失；业务原因仍待解释 | C04 |
| DM 有记录但没有 ARM 列：报告缺变量，不能当作变量存在且全空 | C05 |
| SEX 全为空格、AGE 全为 SAS 缺失值：变量存在且全缺失；普通点、.A、.Z 均计为缺失并保留区别 | C06、C07 |

共同边界：系统报告可观察事实；No Data 业务原因仍需证据和人工判断。本次确认不解决 OQ-04 的正式标准语义。

Q07 当前为部分业务确认，GATE-1 仍为 `pending_chris`；Task 001 未 accepted。上述 §1–5 中“尚未确认”是本记录之前的整体状态；以后以本节分组记录为准。冻结包、独立预期和旧技术证据均不回写。下一步用中文实例审阅第 ② 组字段冲突及来源责任，再审阅第 ③ 组决定复用与延期范围，最后单独确认 GATE-1。

### T001-BR-02：第 ② 组已确认

记录日期：2026-10-20（Asia/Shanghai；消息精确时间未提供）。确认人：Chris。授权来源：本会话在第 ② 组四条中文实例及共同原则之后直接回复：“第二组同意”。

绑定 T001-BR-01 所列同一冻结包；本次重读 manifest SHA-256 仍为 `b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3`。对应独立预期 C08–C12 及契约 §3–4，确认范围如下。

| 已确认规则 | 关联用例 |
|---|---|
| SEX Label 的 Biological Sex／Sex 并列报告冲突，由人判断修订数据、Spec 或记录有依据的决定 | C08 |
| SEX 设计长度 3、存储长度 1、非缺失内容长度 0 分别保留；全空不能证明长度符合要求 | C09 |
| ARMCD 类型和 Label 冲突分别报告；字符型与数值型即使同为长度 8 也不一致 | C10、C11 |
| EXTRA 为计划外变量，等待确认；不自动删除或纳入已批准元数据 | C12 |

共同原则已确认：Spec 记录设计要求，XPT 记录实际情况，标准提供约束，人工决定记录最终处理；保留各来源及冲突，人工选值不改写原始 XPT 事实。本次批准的是处理规则，不是选定这些样本冲突的最终值，不赋予合成 patch 真实批准效力。

第 ①、② 组已确认；第 ③ 组及最终 GATE-1 尚待 Chris。Task 001 仍未 accepted，不进入核对引擎实现。下一步审阅决定复用／失效、首批合成样本及技术边界、延期承接阶段，再单独请求阶段确认。本次仅追加审阅记录及更新 PLANS 指针，不修改冻结包或历史技术证据。

### T001-BR-03：第 ③ 组已确认

记录日期：2026-10-20（Asia/Shanghai；消息精确时间未提供）。确认人：Chris。授权来源：本会话在第 ③ 组 A／B 中文表及阶段安排之后直接回复：“第三组同意”。

绑定 T001-BR-01 所列同一冻结包。已重新读取并核验全部 82 份副本的字节数及 SHA-256，82 份匹配，manifest hash 不变；证据见 [本轮包完整性核验](../../artifacts/TASK-001/business-review-03-integrity.json)。

| 已确认范围 | 关联预期／契约 |
|---|---|
| 同一人工决定重复导入只生效一次；修订保存新决定并关联旧决定，保留历史 | C13、C22；契约 §5 |
| 相关 Spec、标准、规则或影响结果的工具等依据变化时检查影响，无法证明不受影响便重审关联决定及下游验证／批准；纯运行时间变化不触发业务重审 | C14–C21；契约 §5 |
| Task 001 采用完全合成 DM／VS／AE／CM 及 24 条预期，样本故意含错误；本阶段不交付核对引擎 | technical basis 方案 1；OQ-01 首批方案已确认，正式阶段验收待 GATE-1 |
| MVP 0.1 实现 XPT＋结构化 Spec 核对、人工决定和重跑检查，并补重复／歧义 Spec、Unicode、复杂日期等边界；JSON 供程序使用，业务审阅采用中文表格 | 契约 §1、§7；coverage 的 MVP 0.1 承接安排 |
| MVP 0.2 扩展 aCRF／CT／VLM／SUPP／完整 No Data；MVP 0.3 验证 Define 输出及工具转换；SDRG、ADaM／ADRG、Protocol／SAP 按后续阶段推进，长期能力保留 | coverage 的阶段安排；不豁免各阶段必需检查 |
| 当前仅 DDS 概念对齐，不承诺直接兼容 DDE；未选标准版本时不出具标准符合性结论 | C23；契约 §7；OQ-05 本阶段边界已确认，精确兼容性仍未验证 |

以上确认限于实际展示的规则与安排，不推定 Chris 已逐字段批准 JSON 或全部技术细节。三组业务审阅均完成，Q07 尚待最终包级 GATE-1 确认；Task 001 仍未 accepted。未执行引擎用例，不改变任何旧运行结果；OQ-04 等标准语义及后续能力缺口继续保留。下一步使用下节确认卡请求最终阶段验收，不重新要求逐一浏览工程证据。

## 7. GATE-1 最终确认卡（待 Chris 确认）

批准对象：`gate1-v0.1`，精确 manifest 及 SHA-256 见 §6；本节作为包外中文审阅说明，不改写冻结文件。

| 项目 | 本次验收含义 |
|---|---|
| 交付范围 | 接受冻结包内最小契约、固定合成样本、24 条独立预期、需求覆盖和质量门，作为后续实现及测试依据 |
| 业务规则 | 已确认的三组规则和阶段安排见 T001-BR-01／02／03 |
| 其余基础约束 | 无差异不等于人工批准（C01）；不同研究或 SDTM／ADaM 的同名对象分开，输入排列顺序不改变对象身份（C24）；合成 patch 不能成为真实批准 |
| 工程证据 | 最终材料检查 109 项通过；独立审阅 24/24 例、无未关闭技术阻断；本轮 82 份冻结副本匹配。工程检查用于支持本阶段材料验收 |
| 实际能力 | 核对引擎尚未实现，24 例引擎行为均未运行；本次通过不代表软件、标准符合性或递交就绪验证通过 |
| 保留项 | No Data 正式标准语义、精确 DDS／DDE 兼容性及后续阶段能力仍待验证；延期不删除长期目标，不豁免后续检查 |
| 批准后的动作 | 在包外登记 Chris 的最终批准及 manifest 绑定，更新当前入口；MVP 0.1 实施须另有明确授权 |

建议确认语：“确认 GATE-1 通过，接受 gate1-v0.1 作为后续实现依据，保留已列明的未决项与延期范围。”此句目前仅为建议，未收到即不得记作批准。

## 8. T001-A01：最终批准与接续

Chris 于 2026-10-20 在本会话直接确认：“确认 GATE-1 通过，接受 gate1-v0.1 作为后续实现依据，保留已列明的未决项与延期范围。”

按 CTRL-03 在包外保存 [APR-20261020-02](../approvals/APR-20261020-02.md)，绑定 `gate1-v0.1` 及 manifest SHA-256 `b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3`。批准登记及核验时间为 2026-10-20T23:36:21.257260+08:00；不是用户消息精确时间。本轮重读 82 份副本，大小及 hash 全部匹配，既有材料 109 项和独立 24 例技术审阅证据成立，见 [核验附件](../approvals/APR-20261020-02-checks.json)。

Q01–Q06 的材料／技术门通过；Q07 由 Chris 本次人工确认通过。Task 001 已 `accepted`，契约／样本／独立预期交付在指定用途内 `approved`，GATE-1 `passed`。历史工程报告中的 pending 不回写；引擎行为仍全部 `not_run`，覆盖仍为 partial／not_covered，不能转为软件测试通过。

OQ-01 首批方案及 OQ-05 当前对齐边界已确认；No Data 正式语义、精确兼容性和批准记录所列延期／未决项继续保留。长期 G-01 至 G-08 不减，延期承接以冻结覆盖表及批准记录为准。

最新接续入口：PLANS → 本节 → APR-20261020-02 → 冻结包。[MVP 0.1 启动提示](MVP-0.1-kickoff-prompt.md)已备妥；它是提示草案，不代表阶段已启动。收到明确实施授权后，新任务先建任务卡、承接补测项并冻结质量门，再开发核对核心。本次只登记批准及同步 TASK-001／PLANS／README，未实现引擎，未提交／推送，无运行中服务。

## 9. 启动提示词审阅与交接缺口

2026-10-20：Chris 明确要求审阅提示词并直接修改必要部分。v0.1 原文已随 Git 提交 `30748ec94c4bfc208d164e814e357eaeee25c8fe` 推送至 origin/main；本节补充的是该提交之后的审阅，不改写 §8 或原批准记录。MVP 0.1 未启动。

[提示词 v0.2](MVP-0.1-kickoff-prompt.md) 已修订，正文 3360 字符。审阅依据为已批准契约、覆盖和 CTRL-01 至 CTRL-06，使用 kaz-leader 方法检查执行歧义；按项目既有任务卡交接，不另建 PROGRESS/BLOCKED 体系，不创建 Goal。

| 发现 | 修订与理由 |
|---|---|
| v0.1 允许 Agent 将 C01–C24 自行改成延期或不适用 | 固定 24 例为必测基线；改变范围须指定验收负责人批准，防止自行缩小验收 |
| 直接沿用 Task 001 的 Q01–Q07 | MVP 0.1 独立限定检查 ID，映射旧门但不继承通过结果，最终目标明确为 GATE-2 |
| 共享模型与运行时约束没有明确交付要求 | 点名中心对象、模型/证据快照及所有报告同源，避免实现退化为扫描器 |
| “不得自动批准 patch”容易被误解为不能自动应用人工决定 | 区分有效人工授权的自动应用与 Agent 自行批准；合成 patch 仅用于隔离测试 |
| 新预期要求一概先向 Chris 请求批准，技术细节与新增业务规则混杂 | 已批准规则的技术派生案例自主推导并独立复核；新语义或范围改变仍须确认 |
| 报告只要求可读，容易继续只交 JSON | 明确中文 Markdown/HTML 表格和字段；保留机器格式，减少人工阅读负担 |
| 原文缺少精确批准 hash、真实读取路径及恢复失败处置 | 加入 manifest hash、从真实 XPT/Spec 读取、禁止固定答案替代核心行为，核验失败阻断依赖部分 |

### T001-POST-01：Git 字节保真缺口（open）

本轮实际对比本地批准副本和上述提交的 Git blob，证据见 [git-byte-integrity.json](../../artifacts/TASK-001/prompt-review01/git-byte-integrity.json)。本地 82 份副本及 manifest 均仍匹配批准 hash；提交中 54/82 份文件及 manifest 的 hash 不匹配，所有不匹配项均可由 CRLF→LF 转换解释。Git 配置 `core.autocrlf=true`，仓库无 `.gitattributes` 字节保真规则。原“工作区干净、推送成功”不能证明 Git 可恢复同样的批准字节，这是上次交付未检出的验证缺口。

影响：当前本地 GATE-1 批准对象有效，批准内容和历史检查不改；从现有 Git 提交恢复的副本不得直接视为同一批准对象。必须核验实际恢复字节，不能重算 hash 消除差异。本次仅修订提示词／交接并收集只读证据，未修改 Git 配置、索引或冻结文件，未提交／推送。

具体修复建议：增加项目内 `.gitattributes` 对冻结快照及校验材料禁用文本换行转换；以本地仍匹配的原始字节重新入库并保存新提交，不重写旧提交或批准对象；在独立目录从新提交恢复，核验 manifest 及全部文件 hash 后才能关闭本项。修复应同时检查 Task 000 基线及其他按字节校验的来源资产，不能只验证工作区或只验证文件数。该修复尚未执行；后续 Agent 先核对本项最新状态，再决定哪些依赖工作可继续。

## 10. T001-POST-01 修复及接续（2026-10-21）

Chris 明确要求“请你先修复 Git”。本轮延续此前 Git 提交／推送工作，保留 §9 原始失败与发现；最新技术处理为 `closed_fixed`，实际推送状态以 Git 远端核验为准。GATE-1 原批准持续有效，未修改批准记录或冻结对象。

根因：`core.autocrlf=true` 且缺少项目属性，Git 入库和恢复时对混合 LF／CRLF 文件作了转换，造成提交 blob 或恢复物不匹配批准 hash。新增项目根 `.gitattributes` 的 `* -text`，使所有可能参与 hash 的项目文件按原字节入库／恢复；PDF 和 XPT 另禁用文本 diff/merge。此设置只属项目，不改变任何全局 Git 配置。重新暂存原始本地字节，没有重算批准 hash、修改快照或重写历史。

验证入口：[check_git_preservation.py](../../tools/task001/check_git_preservation.py)。参数 `--ref <commit-or-tree> --run-id <unique>`；脚本核对 Task 000 的 7 份快照及 manifest、Task 001 的 82 份副本及 manifest，共 91 项；分别比较工作区、Git blob 和独立 git archive 解包目录。正式检查记录保存到 artifacts/TASK-001/<run-id>/；恢复目录可重建，正式结果不依赖 work 目录存续。

| 检查 | 实际证据与结果 |
|---|---|
| 原提交反例 | [git-bytefix-before01](../../artifacts/TASK-001/git-bytefix-before01/checks.json)：91 项，88 项至少一个维度失败；本地 0 项失败，Git blob 56 项失败、恢复字节 32 项失败，验证器正确返回非零 |
| 修复后 Git tree | [git-bytefix-index01](../../artifacts/TASK-001/git-bytefix-index01/checks.json)：91 项全部通过，0 failed；独立恢复与批准字节一致 |
| 最终修复 tree 复核 | [git-bytefix-final01](../../artifacts/TASK-001/git-bytefix-final01/checks.json)：91 项全部通过；[全部暂存文件字节检查](../../artifacts/TASK-001/git-bytefix-index01/all-index-bytes.json)另确认 186 份源文件／夹具／证据按原始字节暂存 |
| 实际修复提交独立克隆 | [fresh-clone.json](../../artifacts/TASK-001/git-bytefix-final01/fresh-clone.json)：从实际提交 da2ad3cfed50410e1b652e45ba2945bcb6d001a1 新克隆并检出，91 项批准检查全部通过；当时全部 188 份跟踪文件与原工作区逐字节一致 |

新增检查器覆盖恢复失败路径；没有执行核对引擎或改变已有预期。提示词只同步 Git 缺口已修复的最新指针，v0.2 其他审阅修订保持。此前提示词审阅产生的修改／正式证据随本次 Git 修复一起保留，不丢弃。

下一步：核对本次修复提交及 origin/main 一致；MVP 0.1 仍待明确启动授权，接续入口为 [启动提示词](MVP-0.1-kickoff-prompt.md)。将来克隆或更改 Git 处理方式后仍须重跑批准字节检查；旧提交 30748ec 不应作为原始字节恢复依据。
