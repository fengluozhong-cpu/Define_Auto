# Define_Auto

Define-XML 2.1 与 SDRG／ADRG 自动化项目，面向统计编程人员。长期目标以 Metadata Reconciliation 为核心：核对 SDTM／ADaM 设计、实际数据、适用标准和经批准的项目决定，形成有来源记录的中心模型，再生成、验证 Define-XML 与研究者指南草稿。

## 当前状态

Task 000 的五份核心文件已由 Chris 批准正式生效，基线 `BL-20261020-01`，见 [批准记录](docs/approvals/APR-20261020-01.md)。[Task 001](docs/tasks/TASK-001.md) 已验收，GATE-1 已由 Chris 确认通过；`gate1-v0.1` 的合成 XPT／Spec、最小契约、24 条独立预期、覆盖及质量门已批准作为后续实现依据，见 [APR-20261020-02](docs/approvals/APR-20261020-02.md)。未决项及延期保留；核对引擎尚未实现，MVP 0.1 实施待明确授权。阶段计划和退出条件以 [PLANS.md](PLANS.md) 为准。

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
