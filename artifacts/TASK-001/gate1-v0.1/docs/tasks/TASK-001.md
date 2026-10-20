# TASK-001：核对契约、合成样本与独立预期

> v0.1 · 2026-10-20 · `blocked`（等待 Chris 确认业务预期与 GATE-1）· 交付状态 `review_ready` · GATE-1 `pending_chris`

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
