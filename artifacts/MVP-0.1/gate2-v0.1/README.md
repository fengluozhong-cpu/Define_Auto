# Define_Auto

Define-XML 2.1 与 SDRG／ADRG 自动化项目，面向统计编程人员。长期目标以 Metadata Reconciliation 为核心：核对 SDTM／ADaM 设计、实际数据、适用标准和经批准的项目决定，形成有来源记录的中心模型，再生成、验证 Define-XML 与研究者指南草稿。

## 当前状态

Task 000 基线 `BL-20261020-01` 与 Task 001／GATE-1 已批准，见 [APR-20261020-01](docs/approvals/APR-20261020-01.md) 和 [APR-20261020-02](docs/approvals/APR-20261020-02.md)。[MVP 0.1](docs/tasks/MVP-0.1.md) 已获清单 v0.2 及正式 Skill 配置确认，并实现本地核心、CLI、自动检查和中文审阅表。实际执行及独立审阅证据以任务卡最新交接为准；GATE-2 最终验收仍由 Chris 决定。长期未决项及延期保留，阶段退出条件见 [PLANS.md](PLANS.md)。

## 项目文档

- [AGENTS.md](AGENTS.md)：Agent 工作规则、读取顺序、变更控制和跨任务交接。
- [GOALS.md](GOALS.md)：完整长期目标与范围不变量。
- [REQUIREMENTS.md](REQUIREMENTS.md)：功能／非功能需求、验收场景、证据等级和开放问题。
- [ARCHITECTURE.md](ARCHITECTURE.md)：架构边界、逻辑数据契约和设计决策。
- [PLANS.md](PLANS.md)：当前状态、阶段索引、质量门、批准及任务入口。
- [docs/tasks/TASK-000.md](docs/tasks/TASK-000.md)：Task 000 任务记录、阶段验收汇总和交接证据。
- [docs/tasks/TASK-001.md](docs/tasks/TASK-001.md)：当前任务、契约、夹具、独立预期、技术审阅与 GATE-1 审阅包。

## Task 001 夹具检查

固定输入位于 `fixtures/task001/v0.1/`；人工推导预期与覆盖／质量门位于 `expectations/task001/v0.1/`。只含完全合成数据，不是递交级 SDTM。脚本检查材料和固定物理事实，不实现核对或应用 patch。

本机已在 `.venv-task001` 配置 Python 3.12.13，夹具工具版本锁定于 `tools/task001/requirements-fixtures.lock.txt`。恢复机器需先具备兼容的 Python 3.12，在项目内建立 venv 并执行 `python -m pip install -r tools/task001/requirements-fixtures.lock.txt`；不需全局安装。然后在项目根运行：

```powershell
.\.venv-task001\Scripts\python.exe tools/task001/check_materials.py --run-id materials-new
```

`run-id` 必须每次唯一，证据写入 `artifacts/TASK-001/<run-id>/`，不会覆盖旧结果。需要重建 XPT 时用 `build_fixtures.py --out work/task001-rebuild-new` 指定新目录；原始固定夹具不覆盖，重建物理字节与正式输入另行比对。不要将检查器通过误记为核对行为、业务预期或 GATE-1 已通过。

## MVP 0.1 启动材料核验

核心开发的任务卡、质量门及补测范围见 [MVP-0.1](docs/tasks/MVP-0.1.md)。以下入口只核验批准包／引用映射并记录依赖，不运行核对引擎，不表示 GATE-2 通过；`run-id` 每次使用新值：

```powershell
.\.venv-task001\Scripts\python.exe tools/mvp01/startup_audit.py --run-id startup-new
```

结果保存在 `artifacts/MVP-0.1/<run-id>/`；遇到批准 manifest／文件 hash 不符时返回非零并阻断依赖该副本的工作。

## MVP 0.1 本地运行与完整检查

核心仅使用 Python 3.12 标准库，不需要 pandas／pyreadstat。可用已有 Python 3.12 创建项目内独立环境（本次已实际重建并运行）：

```powershell
.\.venv-task001\Scripts\python.exe -m venv .venv-mvp01
.\.venv-mvp01\Scripts\python.exe -m define_auto --manifest artifacts/TASK-001/gate1-v0.1/fixtures/task001/v0.1/input-manifest.json --read-context fixtures/mvp01/baseline-context-v0.1/read-context.json --provenance TEST-BASELINE-MANUFACTURE-001=fixtures/mvp01/baseline-context-v0.1/delivery-record.json --isolated-test --out artifacts/MVP-0.1/demo-new
.\.venv-mvp01\Scripts\python.exe tools/mvp01/run_checks.py --run-id suite-new
```

输出路径／run-id 每次使用新值；已存在则拒绝。完整检查独立登记全部必需用例，漏收集、零用例、跳过或错误均返回非零。`--probe missing|zero|skipped|error` 只运行质量门故障注入，预期退出 1，不能作为引擎套件通过证据。

上面的环境重建入口使用本机已存在的 Python 3.12 夹具环境作启动器；不从中继承第三方包。新机器须先具备 Python 3.12，并用其实际 executable 路径替换首条命令的启动器。本机 `py -3.12` 未登记可用运行时，因此不依赖该快捷命令。

运行目录保存 `model.json`、`issues.json`、`evidence.json`、`dependencies.json`、`patch-applicability.json`、输入／输出 manifests、`run.json`、`checks.json`、`coverage.json`，以及可直接打开的 `review.html`／`review.md`。单次 CLI 的 runtime 检查与完整回归分开，单次成功不表示 GATE-2 通过。完整套件另外保存逐例实际值、子分支、收集／执行数及需求覆盖。

当前支持：单 member 的 XPORT v5，140 字节 NAMESTR，合法连续变量布局；字符宽度 1–200 字节、数值宽度 2–8 字节；显式 codec，保留所有 28 种 SAS 缺失代码。日期保留物理数值、格式和部分日期原文，不自动补日期；未知格式明确为 gap。非 v5、多 member、136 字节描述符等不支持布局显式拒绝，不声称任意 SAS 文件均可读取。

读取辅助声明规则见 [读取上下文契约](docs/contracts/MVP-0.1-read-context-v0.1.md)。XPORT v5 可能无法唯一确定尾部行数；声明必须绑定实际 XPT hash／member 和登记的来源文件及定位，数量还须与真实字节相容。生产 reader 不读取制造配方或测试答案。当前来源定位适配器支持结构化 JSON；其他来源类型需显式扩展。CLI 不验证交付者身份真实性，也不以相容性证明外部计数真实。普通路径拒绝 test_only 声明；`--isolated-test` 仅用于明确隔离的合成验证。

人工决定参数为 `--patch <patch.json> --previous-dependency <dependencies.json> --authorization <authorization.json>`；跨运行再加 `--prior-model <model.json>`。历史模型加载验证内容摘要、引用及四视图约束；依赖变化时保留历史、撤下当前选值并标记重审。授权文件包含 `authorization_id`、`reviewer`、布尔 `test_only`、`scope`；scope 精确绑定 object_id／field_path／selected_value／dependency_snapshot_id。文件按实际 hash 登记；真实性由项目交付／人工批准流程负责，CLI 不代替身份认证。合成决定只产生 simulated_selection，不能写入真实 approved 或 resolved。

业务摘要排除纯运行审计时间；输入、读取声明、来源、有效配置、规则、模型 schema、上游决定、核心源码及 Python 实现／版本均进入依赖。报告默认屏蔽受试者标识和普通运行的内容取值明细；保留聚合统计、字段原始标签与规范化标签及证据。

正式工程 Skill 配置位于根 AGENTS.md 与 `docs/agents/`，供 to-spec／to-tickets／triage 等读取；它们继续遵守本项目授权规则。GitHub 仅用于工程任务及摘要，正式 Spec／契约／批准仍在项目文档。当前 `gh` 不可用，远端标签同步未执行，不影响本地核心使用。

## Git 恢复后的字节核验

项目 `.gitattributes` 保留原始字节，以免换行转换改变批准 manifest 的 SHA-256。克隆或恢复后，可运行以下命令核验 Git 中的 Task 000／Task 001 批准副本及独立恢复物；`run-id` 仍须唯一：

```powershell
.\.venv-task001\Scripts\python.exe tools/task001/check_git_preservation.py --ref HEAD --run-id git-restore-new
```

结果须为 91 项全部通过。失败时先定位恢复问题，不能重算批准 hash；修复过程与原失败证据见 Task 001 §10。此核验不是核对引擎测试。

## 长期能力

目标覆盖 XPT、SDTM／ADaM Spec、aCRF／采集预设值、CT、Protocol／SAP 及项目决定的核对；DDS-aligned 中心模型与字段溯源；Define-XML 2.1、SDRG／ADRG 草稿生成；以及可复现的分层验证和人工批准。

当前阶段的实现范围可以缩小，但不得将 ADaM、Protocol／SAP、No Data、VLM、SUPP、CodeList、研究者指南或验证能力从长期目标中删除。

## 协作与质量

每项实施任务须关联需求、任务范围、依赖版本、独立预期、必需检查、结果证据及未决项。阶段结果保存在对应任务记录和正式产物路径中；Agent 接手时从 PLANS 当前入口和任务记录恢复，不依赖聊天摘要。必需检查失败或未运行会阻止验收。
