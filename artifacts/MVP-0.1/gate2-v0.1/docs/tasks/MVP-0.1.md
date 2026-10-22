# MVP 0.1：本地 Metadata Reconciliation

> 2026-10-21 · task_id=`MVP-0.1` · CHG-009 · `blocked`（技术检查完成，GATE-2 待 Chris 最终验收）；交付 `review_ready`。当前成果与恢复入口见 §10；M01-D01 方案已接受，GATE-2 尚未批准。

## 1. 任务卡与授权

Chris 在本会话明确要求读取 `MVP-0.1-kickoff-prompt.md` 并开启开发。按该提示词 v0.2 实施；此指令授权本地实现、测试、正式证据、相关文档更新和实施者之外的独立 Agent 审阅。Git 提交／推送及业务批准仍分别管理。本卡不自行批准新业务语义。

| 字段 | 范围／责任 |
|---|---|
| baseline / depends_on | BL-20261020-01／APR-20261020-01；Task 001／APR-20261020-02；gate1-v0.1 manifest SHA-256=`b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3` |
| requirements | G-01/02/03/06/07；FR-001/002/003/006/007/014/015/018；FR-005/008 当前适用子集；NFR-001 至 007 的本阶段适用条款；AC-01/02/05、AC-08/11 当前子集 |
| acceptance_scope | 真实 XPORT v5 字节＋结构化 JSON Spec；四视图中心模型；来源、状态、差异、人工决定与依赖失效；机器产物及中文审阅表；24 条基线与承接边界的生产路径测试 |
| change_scope | `define_auto/`、`tests/`、`tools/mvp01/`、新增版本的 `fixtures/mvp01/`／`expectations/mvp01/`、`artifacts/MVP-0.1/<unique_run_id>/`、README／PLANS／本任务；Skill 配置单独确认后修改 AGENTS 与 docs/agents |
| protected | baselines、批准记录、gate1-v0.1、原始 Task 001 夹具／预期、discussion、现有 .workbuddy 及外部知识库保持只读 |
| implementation proposal | Python 3.12＋标准库（dataclasses、json、struct、hashlib、unittest 等），无需新增核心依赖；明确限定 v5 支持面，读不可靠时显式拒绝或 gap；若标准库路径不足，再提交具体依赖提案 |
| fixtures / independent expected | 冻结包内 `fixtures/task001/v0.1/` 与 `expectations/task001/v0.1/expected.json`；C01–C24 由 Chris 在 GATE-1 批准；新增技术派生预期先从样本／规则推导并独立复核，再实现对应逻辑 |
| review / acceptance | 实施：当前 Agent；独立审阅：实施者之外的 Agent；质量门清单与业务／最终验收：Chris。技术审阅不代替业务批准 |

## 2. 依赖读取与启动证据

已读取：当前 AGENTS、GOALS、PLANS §1／2／3／CTRL-01/02/03／§8；完整 REQUIREMENTS（含 CTRL-05/06、FR／NFR／AC／OQ）；完整 ARCHITECTURE（含 §1–4.1／字段责任／ADR）；Task 001 最新交接、批准记录、启动提示词、最小契约、技术依据、24 条独立预期、36 条 coverage 及 Q01–Q07。冻结包引用以包根解析；包内 DRAFT／pending 是批准前历史，当前效力以外置 APR-20261020-02 为准。

精确读取版本／hash、全部 82 份文件及 manifest 核验和恢复映射由 `tools/mvp01/startup_audit.py` 保存到唯一启动运行目录。开始前 `git status --porcelain=v1` 为空，HEAD=`9e3d8c1990119cd59b779044c53e4e661fac6785`。本轮未执行远端 Git 操作。

| 实际检查 | 证据／结果 |
|---|---|
| 现有材料检查器适用性 | 已通读 `tools/task001/check_materials.py`：固定材料审计，根目录由脚本路径决定，包含冻结时 pending 检查，不是引擎测试；原样运行，不篡改历史语义 |
| 环境 | `.venv-task001`：Python 3.12.13；pandas 3.0.6／pyreadstat 1.3.6／numpy 2.5.4／narwhals 2.27.1；仅用于上游材料检查，不作为核心依赖批准 |
| 材料检查 | `artifacts/TASK-001/mvp01-start-materials-20261021-01/`：109 checks passed，0 failed，0 skipped；引擎用例执行数为 0 |
| 批准字节及 Git 恢复 | `artifacts/TASK-001/mvp01-start-bytes-20261021-01/checks.json`：91 项 passed，0 failed；工作区／HEAD Git blob／独立 archive 恢复一致；不表示引擎正确 |
| 冻结包／精确依赖审计 | `artifacts/MVP-0.1/startup-20261021-01/`：86 项 passed，0 failed，0 skipped；核对 manifest、82 份副本、24 例登记及 36 行覆盖；`reading-record.json` 保存读取 hash，`frozen-reference-map.json` 保存冻结引用映射，`carryover.json` 保留 36 条原始缺口和阶段承接 |
| 启动工具及保护复核 | `artifacts/MVP-0.1/startup-verification-20261021-01/checks.json`：20 项 passed；重复 run-id 被拒绝且旧目录各文件 hash 不变，原始夹具／预期 hash 未变；新增脚本 py_compile 成功；按 `git -c core.whitespace=cr-at-eol diff --check` 检查通过。项目保留 CRLF 原字节，未为消除 Git 默认提示改全局设置或格式化文件 |

## 3. GATE-2 检查清单 v0.2（Chris 已确认；最终验收待批准）

本节清单及 §3.1 已于 2026-10-21 获 Chris 直接确认；确认前文件 hash／可恢复副本见 §9 的 M01-AUTH-20261021-01。全部 applicable／required。与旧 Q01–Q07 关联，结果在本阶段重新取证；清单确认不表示检查通过或 GATE-2 验收。

| check_id | 原门 | 需求／方法及固定通过条件 | 计划证据 | 判定人 |
|---|---|---|---|---|
| M01-Q01 | Q01 | 自动：manifest hash、82 份副本大小／hash、Task 000 及原始夹具／预期保护、引用只解析到冻结副本；结束复核原批准对象未改变 | startup／closeout 的 checks 与依赖清单 | 实施＋独立审阅 |
| M01-Q02 | Q02 | 自动：真实 XPT／Spec 解析与核对；C01–C12／C23 逐例匹配固定事实、状态和冲突；生产路径禁止读取 source-data／预期答案；按 M01-D01 及读取上下文契约验证可信声明正常读取、行数依据及字节相容性，保留外部声明真实性未独立验证的限制 | suite/checks.json、逐例实际值与来源 | 实施＋独立审阅 |
| M01-Q03 | Q03 | 自动＋独立审阅：C01–C24 全部收集、选中、执行和断言；新增预期在对应实现前独立固定；24 条逐项对账；0 漏收集／跳过／失败／未运行 | suite/coverage.json、case-results.json；新增预期及 hash | 独立审阅 |
| M01-Q04 | Q04 | 自动＋人工：承接 §4 全部当前缺口；运行时约束、身份、证据、引用、拒绝路径均有实际断言；按 M01-D01 覆盖无声明歧义、错误 hash／member／数量、来源缺失／变更、测试声明越界及相关依赖失效；未实现长期能力保留后续阶段，不申报全部需求 covered | 本阶段 coverage 与 findings | 实施＋独立审阅 |
| M01-Q05 | Q05 | 独立 Agent 审阅关键逻辑、需求一致性、独立预期、失败路径、覆盖及版本；原发现、修复、原场景复测和确认均保留；0 未关闭技术阻断 | 正式独立审阅报告及复测证据 | 独立 Agent |
| M01-Q06 | Q06 | 自动＋人工：同源模型／issues／证据／patch／依赖和运行 manifest 可恢复；同输入及决定业务内容和 ID 稳定；改一条决定影响可解释；输出不覆盖；实际 CLI 与完整检查入口、重建说明、中文审阅表可用 | demo／rerun／suite／恢复核验；README | 实施＋独立审阅 |
| M01-Q07 | Q07 | 人工：Chris 确认本节清单；最终针对确切模型／依赖／交付快照审阅 GATE-2；此门完成前不得 accepted／approved | 本卡确认记录及未来包外批准记录 | Chris |

### 3.1 当前执行台账

以下为上述清单的执行状态，适用性均为 applicable，必需性均为 required；方法、范围、计划证据与判定人沿用对应行。每次正式评估更新实际证据及被检查版本，保留旧运行记录。准备材料检查结果不能直接充当 GATE-2 通过记录。

| check_id | 执行结果 | 实际证据／当前阻断与未完成项 |
|---|---|---|
| M01-Q01 | passed | closeout-20261021-02：86 项保护审计通过；独立 preservation：88 项（含正式配置）通过；原批准对象未变 |
| M01-Q02 | passed | suite-20261021-05：24 条基线逐例匹配；真实 XPT／Spec 与声明路径，详见 case-results.json |
| M01-Q03 | passed | 完整套件 88 收集／执行，0 漏项／失败／错误／跳过；RC 32 案例／37 固定分支；独立实际漏测及四类故障注入正确阻断 |
| M01-Q04 | passed | suite-20261021-05 coverage.json 逐条关联具体用例、预期与实际结果；仅本阶段子集，长期条款继续 partial／后续承接 |
| M01-Q05 | passed | 第一轮 R1-01–06、最终 F01–04 已由实施者之外的 Agent 复测技术关闭；报告与原失败证据保留，见 §10 |
| M01-Q06 | passed | demo-20261021-02／rerun-20261021-01 模型字节一致；CLI 历史恢复／修订／拒绝测试通过；恢复副本与无 Git 完整套件均 88/88，副本 CLI 快照一致 |
| M01-Q07 | not_run | 清单 v0.2 已确认；确切交付包的 GATE-2 最终验收尚待 Chris，不自行标 accepted／approved |

运行布局：`artifacts/MVP-0.1/<unique_run_id>/` 下保留 `run.json`、`checks.json`、`coverage.json`、`inputs-manifest.json`、`outputs-manifest.json`；引擎运行另存中心模型、issues、证据、patch 适用性、依赖快照及中文 Markdown／HTML。审计时间单列，稳定业务摘要不含纯运行时间。清单本身的确认不是阶段验收。

## 4. 必测基线、补测与延期承接

24 条基线全部必测：C01 正常字段与无自动批准；C02 缺文件；C03 读取失败；C04 零行；C05 缺变量；C06 字符全缺失；C07 SAS 特殊缺失；C08–C11 独立 label／长度／类型冲突；C12 额外对象；C13 幂等且合成不是真批准；C14–C20 七类依赖失效；C21 仅审计时间；C22 同 ID 异内容拒绝；C23 未选标准 gap；C24 跨研究／family／顺序稳定身份。精确预期引用冻结包 `expected.json`，不另维护答案副本。

| 新增检查组 | 对应承接 | 固定验收方向／范围 |
|---|---|---|
| M01-B01 | FR-001／NFR-004 | 真实文件完整性、hash 不符、根外／绝对路径、供应声明与实际不符；显式失败并保留原始输入 |
| M01-B02 | FR-002／AC-02 | UTF-8 内容的字节／字符长度分开；编码失败显式报出；其余 SAS 特殊缺失 ._／.B–.Y 保留；零值不是缺失 |
| M01-B03 | FR-002／AC-02 | 日期格式和部分日期保留原值／格式；不自动补日期、插补或解释临床含义；不支持格式／无法可靠解析时显式 gap 或拒绝 |
| M01-B04 | FR-003／FR-006 | 重复／歧义 dataset／variable、重复 JSON key、未知列、不支持非空扩展槽；保留或明确报告，不静默吞输入 |
| M01-B05 | FR-006／007／014 | 中心对象的类型、枚举、非空身份、证据引用、父对象、重复 ID、非法数值／占位符／未知必填值；错误输入明确拒绝 |
| M01-B06 | FR-015／AC-05/08 | 对象／字段／值／依据／授权／依赖不符拒绝；测试批准显式隔离；synthetic_only 在普通路径不能生成真实 approved；新 ID＋supersedes 保留历史；错误对象／字段和跨研究不复用 |
| M01-B07 | FR-018／NFR-001／AC-11 | 重跑及排序／时间变化稳定；单决定变更有影响链；下游验证／批准失效记录与历史保留可恢复 |
| M01-B08 | NFR-002/003/004/007 | 报告同源且中文可读；不输出受试者标识或行级数据；表格／HTML 安全转义；输出已存在拒绝；零收集／漏收集／跳过／执行错误正确阻断 |
| M01-B09 | FR-002／NFR-004 | XPORT v5 支持面明确；非 v5／损坏描述／截断／非法宽度、布局歧义等负例显式拒绝；M01-D01 的声明正反例与依赖检查按 §3 Q02／Q04 及读取上下文契约执行，不用固定偏移和固定样本结果冒充通用读取 |

逐条承接原 coverage 的 MVP 0.1 分配条款，并保留 FR-014、NFR-003/004/007 的每阶段责任。FR-002 的大样本条款保留本阶段合成规模运行证据；尚无 Chris 确认的性能阈值，不凭测试次数宣称生产容量。

已批准后续边界继续保留：MVP 0.2 的 aCRF／CT／VLM／SUPP／完整 No Data；MVP 0.3 的 XML／P21／DDS 精确导出及转换损失；RG 0.1、ADaM／ADRG、Protocol／SAP／USDM、集成与真实试点。当前不生成 XML／RG，不做标准符合性结论，不赋 No Data 原因／HasNoData。此处不新增延期或豁免 C01–C24。

## 5. 初始执行与交接（历史，最新见 §10）

当前完成：授权／入口和全部关联规则读取；旧材料检查器适用性及环境核验；109 项上游材料检查；91 项批准字节／Git 恢复检查；本任务卡和待确认清单准备。

待完成：新增技术派生预期及独立审阅；Chris 对 §3 清单确认；Skill 配置草案确认；之后实现与完整套件、CLI 演示、独立技术审阅及 GATE-2 材料。冻结包启动审计和精确读取记录已完成，证据见 §2。独立准备审阅已委派，只写新预期及准备报告，尚非最终实现审阅。

当前阻断范围：核心实现须等待 CTRL-02 的清单确认；不阻断材料和新增预期准备。Skill 的确认只约束配置写入，不构成引擎依赖。最终验收尚未进行，核心用例实际执行数仍为 0；不声明 verification_complete／accepted。

## 6. M01-D01：XPORT v5 尾部记录歧义（具体契约提案，待 Chris）

状态更新：下文保留原提案与待批准描述；Chris 随后接受方案，当前决定与实施见 §7，不能把历史“待 Chris”继续作为当前阻断。

独立准备审阅发现，主 Agent 另用标准库复算确认：冻结 `dm.xpt` 的 observation 起点为 1760，行宽 34，数据段 160 字节。按 SAS 文档不足 80 字节用空格补齐的规则，3 行＋58 填充与 4 行＋24 填充均符合物理布局；后一种解释的尾行都是 `0x20`。数值区 `2020202020202020` 在 IBM 浮点可解释为约 `3.687825414344431e-40`，并非非法编码，因此不能仅凭数值校验排除。SAS 格式不包含可靠 nobs；裁去所有空格默认作填充，会丢掉合法的尾部全空白记录。

影响：既有 C01 的 3 行在原始合成制造配方中已知，但不是单凭 v5 字节在所有情形下均能唯一证明的观察。原材料审计通过和固定预期不改；不能把制造配方／expected 文件接到生产 reader 来掩盖格式缺口，也不能擅自把 C01 改为延期或 gap。

建议：新增版本化的读取辅助声明，在有歧义时允许由交付方提供 `record_count` 与来源依据；声明绑定 XPT 文件 SHA-256、member、研究、提供者及记录来源，并进入 Evidence／DependencySnapshot。Reader 仍从真实字节解析所有变量和记录，同时验证声明数量与 payload、padding、描述符相容；声明变化触发相关决定重审。无声明且行数不能唯一确定时显式 gap／拒绝，不猜行数。编码同样由交付配置显式声明，因为 v5 不记录编码。

本提案改变输入契约，未获得批准前不写入正式核心契约或实现。若接受，新增 v0.2 辅助输入及预期，原 v0.1 批准包／24 条答案保持只读；基线运行显式使用测试专用的可信制造声明，独立审阅说明共同错误风险和局限，不声称从 XPT 自行验证了外部声明的真实性。若不接受，则须先确定另一个可验证的行数边界方案，不能直接开写会静默丢行的 reader。

本节为 CHG-010 提案，不表示改变已批准范围。原始证据、SAS 条款和独立复现由 `docs/tasks/mvp01-review/startup-review.md` 及其关联正式证据保存。

## 7. 本轮确认、准备产物及交接（最新见 §8）

Chris 直接回复 M01-D01 选择题：“接受可追溯声明方案（推荐）”。记录日期为 2026-10-21，精确消息时间未提供。确认范围是 §6 展示的方案：可信记录数声明绑定文件 hash 和来源、真实字节解析及相容性验证、无声明歧义拒绝／gap、保留原批准包／24 条预期、另添测试声明。不是对后续代码／本文全部字节的批准，不代表 GATE-2。

已据此细化 [读取上下文契约](../contracts/MVP-0.1-read-context-v0.1.md)，继续使用标准库，无新增核心依赖。正式模型／reader／patch 尚未实现；质量门清单待确认仍阻断核心开发。

| 准备产物 | 版本／hash／状态及用途 |
|---|---|
| [独立准备审阅](mvp01-review/startup-review.md) | SHA-256=`c9fd5e26a14d70eed2d6f542c12cc0e2f45a1f75070d9967a6e480c43c38c6c9`；82 份副本独立匹配；M01-IR-PREP-01 指向 M01-D01；不是最终核心技术审阅 |
| [独立新增预期](../../expectations/mvp01/v0.1/additional-cases.json) | SHA-256=`34a92d1a8dd8039b20cbf380985d63c47189b6d86fd9c96fa04d77c9f768d40b`；23 条，21 条 fixed 技术派生、A22/A23 保留当时 pending 状态；后续按已接受 M01-D01 补精确分支预期，不回写旧记录 |
| [实体化输入](../../fixtures/mvp01/v0.1/manifest.json) | 已用 `tools/mvp01/materialize_inputs.py --out fixtures/mvp01/v0.1` 实际制造 8 份 XPT，8/8 大小／hash 与预先固定字节定义一致；含 10000 行合成规模输入；没有运行 reader 或性能测试 |
| [制造来源](../../fixtures/mvp01/v0.1/manufacturing-record.json)／[测试读取声明](../../fixtures/mvp01/v0.1/read-context.json) | 明确 TEST／test_only，计数来自固定制造操作；不能声称仅凭 XPT 独立证明计数、不能生成业务批准。生产代码不得读取预期文件；材料制造工具可使用独立配方重建测试输入 |
| [材料制造入口](../../tools/mvp01/materialize_inputs.py) | 标准库；新版本目录写入，存在则拒绝，批准 seed 与独立配方 hash 必须匹配；交付不依赖 work |
| [基线辅助声明](../../fixtures/mvp01/baseline-context-v0.1/manifest.json) | DM=3／VS=0；单独 TEST 来源与读取声明，来自原制造配方的计数，原始 XPT／Spec／预期不改；生产 reader 不读取制造配方 |
| [读取声明独立材料复核](mvp01-review/read-context-review.md) | SHA-256=`cb7e71ffd6eaf94bf2bc99784911b03606a401e5555bdad6f11c731eec016311`；73 条材料断言 passed，0 failed；8 份 XPT 和共 10 条测试声明的 hash／member／数量／编码／来源匹配。不是 reader、测试隔离或引擎行为通过；未来 Input Registry 必须显式登记 provenance source_id 到文件 |

当前最后完成点：启动核验、独立准备报告及预期、M01-D01 方案确认与读取契约、8 份实体化固定测试输入和 2 条基线辅助声明。制造结果和共 10 条测试声明的独立复核已完成，未将其当作核心实现审阅。

明确未完成：Chris 对 §3 质量门清单的确认；Skill 配置草案写前确认与远端标签同步；A22/A23 按已接受契约细化的新版精确预期；中心模型／reader／核对／patch／CLI／完整套件／中文报告／最终独立审阅及 GATE-2。引擎 C01–C24 实际执行仍为 0，不声称 verification_complete／accepted。

恢复入口：PLANS §1 → 本节 → §3 待确认清单及已接受 M01-D01 → 独立准备报告／新增预期／读取契约。先核对当前文件及 hash；核心只在质量门清单确认后开始，Skill 配置确认不构成引擎实现依赖。若开始前依赖变化，按 CTRL-04 重读受影响部分并记录。无运行中服务、没有 Git 提交／推送；原批准对象及夹具／预期未改变。

本轮收尾核验：`artifacts/MVP-0.1/closeout-20261021-01/` 再次执行 86 项批准包／登记断言，86 passed、0 failed、引擎执行 0；记录新增契约、预期、独立报告及材料 manifest 的依赖 hash。两个准备脚本 py_compile 及 CRLF 口径下的 Git diff 检查通过。该运行之后仅追加本条证据索引，不将状态索引追加当作引擎变更或阶段批准。

## 8. 历史交接：审查建议落实与额度恢复后接续

2026-10-21，Chris 明确要求按质量门和 Skill 草案的审查建议更新文件，完成交接后等待额度恢复再继续。本轮授权是落实这些文档修订；不将其登记为 GATE-2 验收或正式 Skill 配置写入批准。此前 MVP 0.1 本地开发授权及已接受的 M01-D01 继续保留。

最后完成点：§3 清单修订为 v0.2，Q02／Q04 明确纳入读取上下文契约及声明正反例／依赖失效检查，§3.1 补齐七项执行结果和阻断台账；§4 B09 关联该契约。Skill 配置草案已清除多余字符，并明确 GitHub Issues 用于工程任务及实施需求摘要，正式 Spec／契约等继续由项目既有位置管理。

本轮修改范围仅为本任务卡、`MVP-0.1-skill-setup-draft.md` 及 PLANS 当前状态／交接。正式 AGENTS／docs/agents 配置、远端标签、核心代码和原批准包均未修改；无 Git 提交／推送。核心 C01–C24 执行仍为 0，七项 GATE-2 门项均为 not_run。已有材料通过记录保持原范围，不升级为引擎验证。

恢复入口：PLANS §1／§8 → 本节 → §3 v0.2 与 §3.1 → §7 成果索引及读取上下文契约。恢复时检查工作区改动和依赖 hash；原批准对象继续只读。确认清单范围及 Skill 配置的记录仍分别管理，不把本轮编辑指令扩展为阶段批准。

下一步：待 Chris 恢复额度并要求继续后，接续尚未完成的清单确认／Skill 写入确认；在对应逻辑实现前，为 A22／A23 和 M01-D01 分支建立新版独立精确预期，保留旧记录；随后按既有授权实现中心模型、reader、核对、patch、CLI、中文报告及完整套件，执行独立技术审阅与 GATE-2。Skill 配置不是引擎依赖；远端标签须先读取现有标签，再仅创建缺失项，工具或登录未就绪时如实保留未执行状态。

本轮验证：逐项检查 Q01–Q07 登记完整、结果均为 not_run、M01-D01 场景及契约引用齐全、草案杂字符已清除、项目权威位置说明一致；执行 CRLF 口径的 Git diff 检查。仅为文档检查，不执行引擎测试或重用旧通过记录替代新证据。无运行中服务，下次接续不依赖临时进程。

## 9. 恢复开发与确认记录（执行起点，最新见 §10）

2026-10-21，Chris 明确确认 §3 v0.2／§3.1，并授权正式 Skill 配置、本地核心开发及独立技术审阅。确认前完整任务卡与 Skill 草案副本及 hash 见 `artifacts/MVP-0.1/authorization-20261021-01/authorization.json`（M01-AUTH-20261021-01）；仅确认标准和配置，不是 GATE-2 验收。旧 pending／等待额度为历史。

开工回执：冻结包 86 项恢复审计通过；草案 hash 与用户确认一致；先配置、独立预期，再模型／reader／核对／决定及 CLI／报告／检查，最后独立技术审阅。主要风险：尾部行数歧义及依赖变化后的错误决定复用。核心执行起点为 0。正式本地配置已按草案写入；gh 未在 PATH 找到，远端标签 not_run，不阻塞本地开发。

当前 in_progress；完整门项仍依实际执行判定，Q07 最终批准 not_run。接续时先读本节及后续执行证据，不以旧等待状态阻塞已获授权实现。

## 10. 技术交付、GATE-2 确认卡与最新交接

2026-10-21：本地核心、正式 Skill 配置、CLI、测试、中文审阅表及独立技术审阅完成；交付 review_ready，任务因最终人审保持 blocked。M01-Q01–06 通过；Q07 最终批准 not_run。没有 Git 提交／推送、业务 Issue 创建、全局安装或保密数据外发。以下事实以正式证据为准，不继承旧启动准备通过记录。

| 成果／验证 | 正式入口及实际结果 |
|---|---|
| 核心与正式配置 | `define_auto/`：注册／真实 v5／Spec／四视图模型／证据／issues／决定／依赖失效／CLI／报告；AGENTS Agent skills 与 docs/agents 三文件按已确认草案写入 |
| 独立精确预期 | `expectations/mvp01/v0.2/read-context-cases.json` SHA-256=`486069d14f3d8b22a88c6b25eeb1eb8485effbd96d846b01322de6e512c44f6a`；32 案例／37 分支，接续原 A22／A23；旧 24 条答案及 v0.1 预期不改 |
| 完整套件 | `artifacts/MVP-0.1/suite-20261021-05/`：88 收集、88 执行、0 失败／错误／跳过／漏项；24 基线、21 补充、32 RC 及 11 必需运行时回归；逐例实际、子分支、输入／输出 hash、需求覆盖均保存 |
| 独立技术审阅 | `docs/tasks/mvp01-review/implementation-review-round1.md`：R1-01–06 原发现及复测；`docs/tasks/mvp01-review/final-review.md`：F01–04 关闭、独立完整套件、实际 CLI 历史／授权／模型篡改／报告复测；没有开放技术阻断 |
| 独立原失败及关闭 | `artifacts/MVP-0.1/independent-findings-20261021/`、`independent-retest-20261021/results.json`；独立完整套件与漏测复测见 final-review 报告精确索引。原错误的漏测 passed 记录保留为缺陷证据，不当作通过 |
| 中文演示与重跑 | `artifacts/MVP-0.1/demo-20261021-02/review.html`／review.md、同目录模型／issues／evidence／依赖／manifests；`rerun-20261021-01` 与演示模型字节一致，模型 ID=`model-59dcd646167b6cba78e3676ab268e4511325d4def22d5f292d52b133a47d1d01`；基线预期内有 10 项待业务审阅 issue |
| 保护及交付检查 | `closeout-20261021-02`：86/86；`independent-preservation-20261021`：88/88；`delivery-checks-20261021`：45/45（固定预期／夹具／输出 manifest／重跑）；compileall、CRLF 口径 diff 检查通过 |
| 反向验证 | `probe-missing/zero/skipped/error-20261021` 各为预期 failed／退出 1；独立实际移除必需 privacy 回归时，87 项虽执行通过，完整门仍因 missing 返回 1。故障注入通过不等于故障目标通过 |
| 独立环境与恢复 | 新 `.venv-mvp01` Python 3.12.13，仅 pip、无第三方核心依赖；README 提供实际入口。`gate2-v0.1` 副本内恢复套件 88/88；设 Git ceiling 的 recovery-no-git 套件 88/88，HEAD 明确 unavailable；副本 CLI 模型与源演示一致 |
| 候选冻结包 | `artifacts/MVP-0.1/gate2-v0.1/manifest.json`；仅保存白名单代码、测试、文档、输入与证据，不含 .git／venv／work。包外 receipt 绑定最终 manifest hash，批准须引用此确切快照 |

支持面、运行／完整检查／环境重建及恢复历史参数见 README 的 MVP 0.1 章节。源码环境使用 `.venv-mvp01/Scripts/python.exe`；可在项目根执行 `python -m define_auto --help` 查看 CLI，完整检查为 `python tools/mvp01/run_checks.py --run-id <新的唯一ID>`。固定 demo 的实际完整命令及参数保存在 run.json；交付及复测均不依赖临时进程。

需要 Chris 最终确认的内容：是否接受上述确切候选包作为 MVP 0.1／GATE-2 交付，保留长期延期及下述限制。批准前不生成真实 approved 元数据或扩展 XML／RG 生成阶段，不自动执行提交／推送。

限制及未完成项：XPORT 仅明确支持单 member v5／140 字节 NAMESTR；不支持变体显式拒绝。声明相容性不证明交付者身份或计数真实性；当前 provenance 定位适配器支持 JSON。完整 RC 预期文件冻结前有未执行 reader 草稿，独立字节结论先提供；独立答案未取自实现输出，时序事实、共同失误风险及补偿复测在报告公开保留，不宣称严格无草稿的 test-first。10000 行仅是合成规模运行，不建立生产容量阈值。标准未选择仍 gap；No Data 正式语义、精确 DDS 导出及后续 XML／RG／ADaM／Protocol／SAP 等按原覆盖和延期继续保留。

GitHub 标签同步因 gh 工具不可用仍 not_run；本机未找到可用 GitHub 专用连接器，未绕过登录或全局安装，未伪称完成。此项与核心验收分开，后续工具就绪后先读现有标签，只创建缺失五项。

最新恢复入口：PLANS §1／§8 → 本节 → 候选包外 receipt／manifest、完整套件及最终独立审阅。先核对字节和工作区已有改动；当前等待 Chris 对 GATE-2 的最终决定，后续开发／扩展不由技术审阅自动授权。历史配置待确认／等待额度条目不再作为当前阻断。
