# MVP 0.1 开发启动提示词

> 版本 0.1 · 2026-10-20。此文件是交给后续 Codex Agent 的启动提示，不代表 MVP 0.1 已启动或已获得执行授权。用户将此提示用于明确启动时，按下列范围工作。

```text
请在 E:\Initiation\Define_Auto 开始 MVP 0.1：基于已批准的 Task 001 契约与合成夹具，实现本地 XPT + 结构化 Spec 的 Metadata Reconciliation 闭环。

启动前按项目 AGENTS.md 渐进读取规则，读取 GOALS、PLANS 当前入口／CTRL-01／02／03、REQUIREMENTS 的关联 FR/NFR/AC/OQ 与 CTRL-05／06、ARCHITECTURE §1–4.1／§5／CTRL-04，以及 Task 001 当前任务卡、批准记录和依赖版本。核验实际文件及 Git 状态；以 gate1-v0.1 manifest 所绑定的确切快照为批准依据，不把旧 DRAFT/Pending 当成当前结论。不得修改该冻结包或 Task 000 基线快照。

批准与起点：Task 001 GATE-1 已通过，APR-20261020-02 绑定 gate1-v0.1。首批输入完全合成；已批准的预期为 T001-C01–C24。先在 docs/tasks/ 建 MVP-0.1 任务卡，记录关联需求、逐条承接的延期、依赖版本/hash、所读文档、实现范围、交付物、质量门、独立预期和退出条件；更新 PLANS 当前入口／任务索引／交接。固定本阶段 Q01–Q07 适用性和证据要求。不得因任务编号或本提示而扩大范围。

实现目标：
1. 本地登记并校验输入 manifest；区分 not_provided、unreadable、present_empty、variable_absent、present_all_missing、present_with_data 和 unknown。
2. 读取首批 SAS XPORT v5 夹具与已批准的结构化 Spec，对齐稳定研究／SDTM family／dataset／variable 身份；生成 expected、observed、reference、approved 四视图及可定位证据。
3. 报告字段级缺失、额外对象和字段冲突；分别保存类型、label、Spec 长度、XPT 存储字节长度和观察内容长度。不得以一个来源覆盖另一个，不得将观察事实提升为项目决定。
4. 以本地可审阅的确定性报告呈现差异和状态；支持人工 patch 的校验、稳定 decision ID、幂等重放、同 ID 异内容拒绝、supersedes 历史和依赖快照。相关输入、标准、规则、配置、模型 schema、影响结果的工具或上游决定变化时按 CTRL-04 评估失效；影响不明则 needs_review。不得自动批准 patch 或业务解释。
5. 同一输入／规则／决定重跑时，业务结果、对象／issue 身份稳定；运行时间等审计字段分开记录。正式证据写入 artifacts/<task_id>/<unique_run_id>/，不得覆盖旧运行。

质量要求：
- 先读取并运行 Task 001 材料检查，确认固定预期仍与样本绑定；实现不能生成自己的标准答案。实现前冻结本阶段新增用例及独立预期，并取得所需业务确认。不得为适配代码而改写 gate1-v0.1/expected.json；修订须保留旧版、记录理由／来源／影响并另行批准。
- 将 T001-C01–C24 逐例分类为本阶段必测、明确 not_run 的承接项或有证据的 not_applicable；另补重复／歧义 Spec、Unicode、复杂日期及其他声明支持边界的反例。不得漏收集、跳过必需例或把材料检查误报为引擎通过。
- 按需求条款 → 用例 → 独立预期 → 实际运行／证据 → 结果维护覆盖表；自动检查与人工判断分列。No Data 正式语义、VLM、SUPP、完整 CT/aCRF、Define/XML/P21/DDE、SDRG/ADRG 与 Protocol/SAP 不属于 MVP 0.1 已实现范围，但必须记录承接阶段并保留长期能力。
- 实施者之外的 Agent/人员独立审阅契约对应、关键逻辑、边界失败路径、预期独立性、覆盖与实际证据；记录审阅对象版本/hash、发现、修订与复测。审阅者不能代替 Chris 批准业务含义或阶段验收。
- 退出前运行所有必需自动检查及适用的人工审阅；失败、未运行、零用例或未收集均不得报通过。清楚区分实现、执行、验证、验收、批准。

技术边界：以 Python 本地 CLI、文件输入和确定性规则为最小起点；优先标准库和已锁依赖。Task 001 的 pandas/pyreadstat 仅为夹具制作／检查依赖，不自动成为核心运行依赖。新增或替换核心依赖、改变批准契约／业务语义／长期目标、访问非公开数据或调用外部服务，须先提交具体依据、影响与方案供 Chris 判断；等待期间继续独立工作。不得实现 XSD/P21/DDE/Define/RG 适配器来扩大本阶段。

数据与 Git：仅用固定合成样本或用户明确授权的数据；默认本地。不得全局安装、公开发布或泄露保密材料。除非用户另行明确授权，本阶段不执行 Git commit/push。不得提交密钥、虚拟环境、缓存或无关改动。

交付时给出中文结果摘要、可读的差异报告样例、任务卡与 PLANS 入口、代码／运行证据路径、覆盖与未决项、独立审阅证据、实际检查结果及下一步。MVP 0.1 业务预期及最终验收由 Chris 或其指定人员批准；不得自行宣称阶段通过。长期目标仍为以 Metadata Reconciliation 为核心的 Define-XML 2.1 + SDRG/ADRG 系统，保留 SDTM/ADaM、DDS-aligned 模型、aCRF、CT、Protocol、SAP、No Data、VLM、SUPP、CodeList、验证、决策和全链溯源。
```

## 引用起点

- [Task 001 批准与交接](TASK-001.md#8-t001-a01最终批准与接续)
- [GATE-1 批准记录](../approvals/APR-20261020-02.md)
- 冻结批准对象：`artifacts/TASK-001/gate1-v0.1/manifest.json`
- 核心需求：`REQUIREMENTS.md` FR-001/002/003/006/007/015/018，NFR-001/002/003/004/006/007，AC-01/02/05/08/11；其他需求按批准的覆盖映射延期承接。
