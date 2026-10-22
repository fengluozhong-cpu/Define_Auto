# MVP 0.1 最终独立技术审阅

> 2026-10-21 · reviewer=`/root/final_review` · 最终冻结源码复测完成，F01–F04 技术关闭，当前无开放技术阻断。本报告不是 Chris 的业务批准或 GATE-2 验收；恢复候选包本身的装包与复跑另由主任务保存证据。

## 范围、依据与版本

完整读取 AGENTS、GOALS、冻结 Task 001 契约及读取辅助契约；读取 PLANS 当前状态／CTRL-01／02／阶段退出条件、当前任务 §3／4／9，ARCHITECTURE §1–4.1／来源责任，REQUIREMENTS 关联 FR／NFR／AC 及 CTRL-05／06。实际检查 define_auto 全部源码、tests 全部测试、run_checks、正式 Skill 配置及草案，另读两份准备预期审阅与实现第一轮审阅。实现者同时修复源码，因此下述发现按复现时具体 hash 绑定，最终结论须重新绑定封存版本。

初始独立复现：`.venv-task001/Scripts/python.exe work/mvp01-final-review/reproduce.py`。初始结果及当时全部生产源码 hash 最初保存于临时目录，随后将原始脚本、initial-results.json、漏测探针及保护核验脚本原样保存到正式 `artifacts/MVP-0.1/independent-findings-20261021/`，逐文件 hash 见该目录 outputs-manifest.json。脚本只构造合成模型，不修改生产实现、预期或夹具。以下发现保留原始情况，即使后续关闭亦不删除。

首轮独立完整检查：`.venv-task001/Scripts/python.exe tools/mvp01/run_checks.py --run-id independent-review-first-20261021`，84 收集／执行，0 failure／error／skip，退出 0。证据 `artifacts/MVP-0.1/independent-review-first-20261021/`。这是真实执行记录，不能消除下述未覆盖缺陷，也不能自动升级为质量门通过。

## M01-IR-F01：模型恢复入口缺少内容身份及事实一致性约束

**严重性：阻断；关联 M01-B05／B07、FR-006／007／015、NFR-001／004、CTRL-04。责任人：主实施 Agent。状态：in_progress。**

初始实际复现：真实 baseline 模型各自独立修改后，`validate_model` 仍接受 observed.type 为数组、expected.label 与对应 assertion 分离、全零 model_snapshot_id／dependency_snapshot_id，以及 downstream_records 的空 record_id 和未知状态。全部结果见上述 initial-results。单改 evidence_id 时现有引用检查正确拒绝，resolved issue 指向不存在决定也正确拒绝；这些正面结果不混作所有模型约束通过。

模型内部可变构造与持久化载入的检查职责应明确：内存中合法编辑可重新计算摘要，持久化的 prior-model 必须校验所宣称的 model／dependency 摘要，并验证四视图、断言、决定、授权和下游记录闭合；不能把一个字符串非空当作可复现内容身份。关闭需原负例及真实 CLI 篡改历史模型路径均明确拒绝，正常封存、恢复和修订仍可用。

## M01-IR-F02：真实 CLI 初版无法恢复决定历史，普通授权 supersedes 初版失败

**严重性：阻断；关联 M01-B06／B07、FR-015／018、AC-05／08／11。责任人：主实施 Agent。状态：in_progress。**

首次静态审查时 CLI 每次只 reconcile 出空 decisions，未提供历史模型输入；因此新 ID＋supersedes 无法定位前一决定，也无法跨运行验证幂等。首次 decisions 普通授权分支直接追加第二条 approved 断言，导致当前 approved 与旧断言冲突。发现已及时发给实施者；实施者在独立复现脚本执行前补了 `--prior-model`／resume_model 和替换当前 approved 断言，故 initial-results 中真实授权 supersedes 已成功。保留这个时序，不把修复前缺陷伪装成已运行失败。

关闭需固定源码后实际 CLI 三次以上运行：首次决定、相同决定幂等、新 ID＋supersedes、相同 ID 异内容拒绝及依赖变化后的历史保留／当前失效。普通授权路径的测试材料必须明确合成测试用途；不产生项目真实业务批准。恢复旧记录时不能因模型未经验证而引入任意授权或旧选值。

## M01-IR-F03：中文报告遗漏长度批准选值及正常字段来源

**严重性：阻断当前可审阅交付；关联 M01-Q06、M01-B08、NFR-003、FR-007／015。责任人：主实施 Agent。状态：in_progress。**

初始 reporting.review_rows 的长度显示行使用 approved.declared_length，而长度冲突／决定的实际字段为 storage_vs_declared_length，故长度批准选值无法进入对应表格。证据栏只从同对象 issues 获取，正常且无 issue 的字段始终为空，虽然模型中存在字段断言和 Evidence。用户依赖中文表日常审阅，不能要求先读 JSON 才能核对关键来源及选值。

关闭需对长度人工决定生成真实报告并核对批准列；对无冲突正常字段，表格应给出相应断言证据，且避免把其他字段的冲突／证据误显示为本字段结果。HTML／Markdown 仍须安全转义，并消费同一模型快照。

## M01-IR-F04：必需 runtime 检查漏收集仍报 passed，覆盖映射过宽

**严重性：阻断；关联 M01-Q03／Q04、M01-B08、NFR-007、CTRL-02／06。责任人：主实施 Agent。状态：in_progress。**

实际复现命令：`.venv-task001/Scripts/python.exe work/mvp01-final-review/omission_probe.py`。脚本不改生产或测试文件，仅在内存中的 unittest discover 结果中过滤 `test_raw_label_and_privacy`。真实完整检查入口随后仍返回 83 collected／83 executed、missing=[]、passed、退出 0。正式证据 `artifacts/MVP-0.1/independent-review-omission-20261021/`；这个 passed 是被测防线的错误观察结果，不能当作产品通过。

根因：必需注册只包含 24 基线、21 A、32 RC，实际必需 runtime 回归没有固定登记；移除它们不会触发 missing。必须独立固定这些必需 test_id，并测试漏收集／零收集／跳过／执行错误确实阻断。

初始 coverage.json 将全部 M01-ID 广泛附给每条当前适用需求，缺少条款对应的固定输入／预期及确切实际记录。这不足以说明某条验收要求由哪一断言证明。关闭需精确映射当前适用条款，保留具体长期未覆盖／批准延期，而不把测试数量替代覆盖结论。

## 配置、支持面与初步正面观察

正式 AGENTS Agent skills 段与草案一致；docs/agents 三文件保持原有正式需求、Spec、契约、证据、ADR 的单一权威位置，没有自动建 Issue 或扩大外部写入权限。gh 不可用时远端标签 not_run 的处理符合授权边界，本地配置不因此失效。

独立标准库保护核验实际执行 88 项全部通过，正式证据 `artifacts/MVP-0.1/independent-preservation-20261021/checks.json`：批准 manifest hash、82 份文件大小／hash、用户确认草案 hash、AGENTS 及三配置文件逐块对照。此结果只证明保护及配置一致性，不证明引擎正确。

生产代码只读取实际 manifest／Spec／XPT／外部声明及来源，没有导入 source-data 或 expected 答案，也没有按样本内容硬编码预期结果。XPORT 支持范围明确为单 member v5／140-byte NAMESTR，不支持变体显式拒绝。保留 M01-D01 外部声明真实性限制；未选标准为 gap，不赋 No Data／HasNoData。默认普通路径不输出 observed_values；身份字段在测试路径也屏蔽观察标识。以上观察仍须最终封存版本回归绑定。

## 当前结论与待关闭

本段保留首次判断：当时存在 M01-IR-F01–F04 开放技术阻断，实施者收到原因后修复，当时不支持 verification_complete。随后冻结版复测及关闭如下；不能将后续通过倒写为初始版本通过。

## 冻结版独立复测、关闭与最终技术结论

本审阅者实际使用新建的 `.venv-mvp01/Scripts/python.exe`（Python 3.12.13、核心仅标准库）执行以下检查。完整套件的确切源码／测试／runner／预期 hash 位于 `artifacts/MVP-0.1/independent-review-final2-20261021/inputs-manifest.json`。独立原场景复测另在 `artifacts/MVP-0.1/independent-retest-20261021/results.json` 保存 15 份源码／测试／runner／README 的执行前后 hash，全部一致。该文件对应源码包括 model=`4f9fe85be4b6d7b4d9e4bd24ac555e5289c1774139edbe183cad131cafd69665`、decisions=`0c5f6f9f4475d03a8e7002a32db9209a13e69adc8be3fa50c28f00af75ab19c4`、reporting=`9bbba9ebebb11a6b3bd6742334eaa1beee439a98a8d8173fc18fa8c775976171`、runner=`9c0442b6fe2698d5dfb4ea693bf9c46c76ece4d01475688653da6d342fdf0349`。

1. 完整套件：`.venv-mvp01/Scripts/python.exe tools/mvp01/run_checks.py --run-id independent-review-final2-20261021`，**88 收集、88 执行、0 failure、0 error、0 skipped，退出 0**。其中 24 条批准基线、21 条原新增技术预期、32 条读取上下文案例及 11 条固定登记 runtime 回归均实际收集并通过。读取上下文 33 条 subcase 及 4 个直接执行的依赖／稳定性分支合计 37 个固定分支。早一轮 independent-review-final-20261021 的 88 次通过发生在最后报告改动前，其版本不冒充最终版。
2. F01 原场景：16 项独立复测中的 6 条模型负例全部拒绝。持久化入口 `sealed=True` 分别拒绝错误 model 摘要和重新计算 model 摘要后仍错误的 dependency 摘要；内存结构检查拒绝非法 observed 类型、视图与断言分离、非法下游记录及悬空 resolved 决定。真实 CLI 的两条被篡改 prior-model 均返回 1、明确对应 hash 错误、不创建成功产物；不只测试帮助函数。
3. F02 真实 CLI：在正式独立复测目录执行 baseline → 首个合成决定 → 相同决定幂等 → 新 ID＋supersedes → 同 ID 异内容拒绝 → 生效编码配置变化后的 needs_review。幂等两次模型规范内容一致；修订保留原决定原文；所有隔离输出真实 approved 为空；依赖变化保留历史并阻止自动复用。另以明确合成的 review-only 内存材料检查普通授权分支，supersedes 后仅保留当前一条 approved 断言，历史决定原文不变。这是技术分支验证，不是创建项目业务批准。
4. F03：通过真实 apply_decision 的长度选值检查中文表对应批准列和证据，所有正常字段均有来源。最后追加的 ARMCD 长度行独立检查为无 field_conflict，避免 label／type 冲突污染长度行；相应自动回归也在最终 88 项套件内。HTML／Markdown 转义通过，报告消费同一模型快照。README 的恢复入口改为实际已有 Python 3.12 建立项目内 venv，没有伪称不可用的 py 启动器已被验证。
5. F04 实际故障注入：正式见证 `artifacts/MVP-0.1/independent-guard-retest-20261021/results.json` 及同目录 `guard_retest.py`。分别在内存的真实发现／执行过程注入漏收集、零收集、跳过和 RuntimeError；四次实际运行完整入口均返回 1，目标套件均为 failed。漏收集精确列出必需 `tests.test_boundaries.RuntimeBoundaryTests.test_raw_label_and_privacy`；零收集／执行均为 0；跳过数／错误数各为 1。**故障处理验证通过，四个被注入故障的目标套件仍然是 failed**，不计入产品 88 项通过。此前错误 passed 的初始证据保持只读。
6. 覆盖：runner 已将必需 runtime ID 独立登记，当前 coverage 按具体需求选择关联案例并给逐案结果和预期来源，保留长期 partial／延期，不将所有 M01-ID 批量挂到每条需求。源码与工具依赖记录实际 Python 实现／版本；输入、标准、规则、配置、schema、上游决定和工具变化的必测基线及 M01-D01 真实上下文变化路径均通过。纯审计时间与业务依赖分开。

| finding_id | 原状态 | 当前状态 | 独立关闭依据 |
|---|---|---|---|
| M01-IR-F01 | open → in_progress | closed_fixed | 冻结版 6 条原模型负例、真实 CLI 篡改入口、最终 88 项受影响回归 |
| M01-IR-F02 | open → in_progress | closed_fixed | 真实 CLI 连续决定历史／幂等／修订／拒绝／失效，普通授权分支技术复测及最终回归 |
| M01-IR-F03 | open → in_progress | closed_fixed | 实际长度选值映射、正常来源、字段冲突隔离、转义及最终回归 |
| M01-IR-F04 | open → in_progress | closed_fixed | 真实发现漏项重现由错误 0 变为正确 1，四类故障注入、精确需求覆盖及最终完整套件 |

第一轮 R1-01–R1-06 原始发现、修复与独立复测已保留于 implementation-review-round1.md；当前最终套件继续覆盖实际头读取、无授权批准／计数、来源指针／来源文件、原始 label 与生效编码等回归。本轮没有改动生产实现、固定答案或夹具。

**最终技术结论：在所绑定的 MVP 0.1 本地合成输入与明确支持面内，F01–F04 已独立技术关闭，当前无开放技术阻断，可以编制 GATE-2 待批准交付包。** 原批准包及 Skill 配置独立保护检查 88 项全部通过；最终候选恢复包的 manifest、在副本内重跑和最终状态文档仍由主任务完成并绑定，不能用本报告替代尚未发生的装包检查。Chris 仍须针对确切交付快照做最终验收；本报告不批准真实研究元数据、标准符合性、No Data 语义、生产容量或递交就绪。

保留限制：外部记录数和提供者真实性不由 CLI 独立证明；共享契约与测试来源仍有共同失误风险；完整 RC 预期冻结前曾存在未执行 reader 草稿，事实和补偿审阅已在独立预期报告保存，不能重记为严格无草稿的 test-first。测试规模 10000 行仅为已运行样本证据，未建立生产性能阈值。GitHub 标签因工具不可用仍为 not_run，本报告不虚构远端同步，也不将其变成核心验收失败。

### 最后 runner 恢复适用性差异复核

上述核心冻结后，主实施者发现无 Git 元数据的源码恢复目录会在收尾读取 HEAD 时失败，仅将 runner 的 Git HEAD 读取改为可选审计字段；其余生产源码／测试未变。审阅者核对差异：必需登记、收集／执行、失败／跳过阻断及证据写入逻辑均未放宽。最终 runner SHA-256 为 `f52c1ab0e2d66c3510e1a0c0fdf454523e3225ba4fe82a11ad585136d11de4f2`，替代本报告前段记录的旧 runner hash。

独立实际补测：`.venv-mvp01/Scripts/python.exe work/mvp01-final-review/nogit_retest.py`，在仅 Git 可发现性设为不可用的沙箱调用真实完整入口，仍 **88／88 passed，0 failure／error／skip，退出 0**，正式证据 `artifacts/MVP-0.1/independent-review-nogit-20261021/`，run.json 明确 `head=unavailable_in_source_bundle`。该测试仅注入 Git 不可用，核心 XPT／Spec／patch 和完整测试均真实执行。最终版本 hash 见该次 inputs-manifest；不以此模拟替代主任务在独立候选副本中阻止上级 `.git` 继承后的真实恢复核验。

主任务随后通知候选副本已在独立目录执行 recovery-suite、显式 Git ceiling 的 recovery-no-git 及 recovery-demo。审阅者对源码技术关闭结论保持有效；最终候选 manifest 尚由主任务封存，不在本报告未运行时宣称其最终 hash 或批准。主任务应在最终状态及包外记录中绑定最终 manifest 和恢复证据。当前 **0 个开放技术阻断**，四项发现均为 closed_fixed，GATE-2 仍 pending_chris。
