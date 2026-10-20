# Define_Auto

Define-XML 2.1 与 SDRG／ADRG 自动化项目，面向统计编程人员。长期目标以 Metadata Reconciliation 为核心：核对 SDTM／ADaM 设计、实际数据、适用标准和经批准的项目决定，形成有来源记录的中心模型，再生成、验证 Define-XML 与研究者指南草稿。

## 当前状态

项目处于 Task 000 文档基线阶段。文档均为 **DRAFT，待 Chris 审阅批准**；系统尚未实现，Task 001 尚未获准启动。阶段计划和退出条件以 [PLANS.md](PLANS.md) 为准。

## 项目文档

- [AGENTS.md](AGENTS.md)：Agent 工作规则、读取顺序、变更控制和跨任务交接。
- [GOALS.md](GOALS.md)：完整长期目标与范围不变量。
- [REQUIREMENTS.md](REQUIREMENTS.md)：功能／非功能需求、验收场景、证据等级和开放问题。
- [ARCHITECTURE.md](ARCHITECTURE.md)：架构边界、逻辑数据契约和设计决策。
- [PLANS.md](PLANS.md)：当前状态、阶段索引、质量门、批准及任务入口。
- [docs/tasks/TASK-000.md](docs/tasks/TASK-000.md)：Task 000 任务记录、阶段验收汇总和交接证据。

## 长期能力

目标覆盖 XPT、SDTM／ADaM Spec、aCRF／采集预设值、CT、Protocol／SAP 及项目决定的核对；DDS-aligned 中心模型与字段溯源；Define-XML 2.1、SDRG／ADRG 草稿生成；以及可复现的分层验证和人工批准。

当前阶段的实现范围可以缩小，但不得将 ADaM、Protocol／SAP、No Data、VLM、SUPP、CodeList、研究者指南或验证能力从长期目标中删除。

## 协作与质量

每项实施任务须关联需求、任务范围、依赖版本、独立预期、必需检查、结果证据及未决项。阶段结果保存在对应任务记录和正式产物路径中；Agent 接手时从 PLANS 当前入口和任务记录恢复，不依赖聊天摘要。必需检查失败或未运行会阻止验收。
