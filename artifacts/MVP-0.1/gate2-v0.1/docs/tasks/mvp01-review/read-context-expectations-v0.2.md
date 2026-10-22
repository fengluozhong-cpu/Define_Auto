# MVP 0.1 读取辅助声明 v0.2：实现前独立技术预期

> 2026-10-21 · reviewer／author=`/root/read_context_expectations` · 独立于 reader 实施者。仅固定技术预期，不是最终实现审阅、业务批准或 GATE-2 通过。

Chris，本次新增 [read-context-cases.json](E:/Initiation/Define_Auto/expectations/mvp01/v0.2/read-context-cases.json)，包含 32 个必需案例 ID、37 个独立场景分支。它按已接受的 M01-D01 补齐历史 A22／A23 的精确行为；原 v0.1 预期、原 24 条批准答案及所有实体夹具均未修改。预期文件 SHA-256：`486069d14f3d8b22a88c6b25eeb1eb8485effbd96d846b01322de6e512c44f6a`。

## 读取范围与依据

完整读取根 AGENTS、GOALS；PLANS 当前状态、CTRL-01／02 及最新交接；MVP-0.1 §3／3.1／4／6／7／8；ARCHITECTURE §1–4.1（包括 CTRL-04）；REQUIREMENTS 的 FR-002、NFR-004、AC-02、CTRL-05／06；读取辅助契约全文、原 additional-cases、原批准 expected、两组测试上下文及来源、前次读取材料审阅。本次职责只涵盖新增技术预期及该报告，未承担其他需求的完整覆盖判定。

核对的依赖 hash：

| 文件 | SHA-256 |
|---|---|
| AGENTS.md（配置落地前读取版本） | `c620815558b35d60bcdf6fdeeb5cafa23eeb2e7076dc4c33395ec88087792f89` |
| GOALS.md | `8aaa34ca717f8be23a3dae5d78952a127a1fe0e23990ea5c6880a9c1a4550f23` |
| PLANS.md（恢复前状态） | `170b60c0a218494b13a265a8a4808fd6b3c19bdd7b9037e86d91d5a76f563b32` |
| REQUIREMENTS.md | `17139ff7cbe22bad6fdcd9dd7915b89c02cc381dfd6998bc374b02cbc0a0aa2b` |
| ARCHITECTURE.md | `7e2822449772feb81de33d89e8df0b7a86c7d9dfebe28a193902ee2e8c1c02f7` |
| docs/tasks/MVP-0.1.md（恢复前 §8 交接版本） | `81db45fb4e34b7e08351ae4424b1e66ab30e93620540883a70f97a0e125236e8` |
| docs/contracts/MVP-0.1-read-context-v0.1.md | `99629de2acd4263fa16d908fac18fe07974a8b3dc347314f2d7f626984614a3b` |
| expectations/mvp01/v0.1/additional-cases.json | `34a92d1a8dd8039b20cbf380985d63c47189b6d86fd9c96fa04d77c9f768d40b` |
| 冻结包 expectations/task001/v0.1/expected.json | `acf277e0e0963eeddb3712b754770ec84e0077a488208d9e0e15f83bb93fa808` |

并行主任务随后更新状态／正式 Skill 配置时，不把这些更新自动当成读取语义变化；正式实现审阅仍须核对其具体影响。若读取辅助契约本身变化，本预期必须重新评估，不能只沿用本报告。

## 独立推导与固定结果

未导入或调用生产 reader、未读取其输出作为答案。标准库临时只读计算从实际 `NAMESTR` 的类型／宽度／位置、实际 `OBS` 标记及剩余字节推导边界：候选数量必须满足剩余不足 80 字节且全为 ASCII 空格。使用实际 SHA-256 固定原始及派生字节，未调用制造器。描述符偏移仅用于独立样本核对，不准被生产 reader 写成固定样本偏移。

| 输入 | row width | payload | 相容行数／padding | 固定结论 |
|---|---:|---:|---|---|
| 冻结 DM | 34 | 160 | 3／58；4／24 | 原 C01 仍为外部测试声明的 3 行；无计数证据拒绝／gap。新隔离声明若明确给 4 行则字节也相容，但不是修改原基线答案 |
| 冻结 VS | 5 | 0 | 0／0 | 明确编码后可由唯一布局得到 0 行；变量观察状态 unknown，但物理 missing／nonmissing 计数各为 0，与批准 C04 一致 |
| VS 追加 80 个空格 | 5 | 80 | 1 至 16 行；padding 75 至 0 | 无声明不能猜零行；声明 1 或 16 行保留全缺失记录；声明 0 行剩余 80 字节，必须拒绝 |
| utf8 | 84 | 160 | 1／76 | 计数为 null 仍可从唯一布局读 1 行；字符值固定为 5 字节／2 字符；编码不得猜测 |

派生 VS blank-tail XPT 的 SHA-256 为 `8c3556fdcbb5da8021e64d0b9194f53825794c1406cf8328983e1029b9e33675`。其构造是冻结 VS 原字节后拼接 `0x20` 80 次；新增 provenance 由测试沙箱明确登记，不修改原夹具，也不声称它是真实研究交付。

最后一条 DM 空格记录的 `2020202020202020` 数值不属于 SAS 缺失编码；不能用“空格数值必定无效”排除 4 行候选。声明相容性检查只能证明与字节不矛盾，不能验证交付方身份真实性或记录数真实性。

## 覆盖与实施约束

- RC01–RC06 固定 A22 的成功、无声明／null 歧义、物理兼容的替代声明及不足／超量分支。
- RC07–RC11 固定 A23 的 16 个可能数量、1／16 行全缺失正例、0 行错误以及真正空数据集边界。
- RC12–RC18 固定 XPT hash／member 目标、来源注册／可访问性、源 hash 变化与 test_only 普通运行越界。
- RC19–RC24 固定 bool／负数／float／string 数量、重复 ID、不同 ID 重复／冲突目标及 study／family 不符。每个 independent_mutations 必须逐一执行，不能一例代表所有分支。
- RC25–RC28 固定缺编码、未知 codec、严格解码失败、唯一布局 null 数量及 hash 重绑定后仍非法 padding。
- RC29–RC31 固定 XPT 不变而上下文数量、来源或编码变化时的依赖检查、旧决定禁止自动复用及历史保护。它们明确不提供“已证明不影响”的分析，因此期望保守 needs_review；不删除 CTRL-04 允许经证据证明无影响后保留有效性的分支。
- RC32 固定相同业务依赖及仅运行时间变化时的稳定业务内容／标识；运行审计记录可变化，需记录影响分析。

JSON 中 outcome 和 reason 是可测试的业务含义，不强制新增 API 字段或错误码拼写；测试适配时可映射现有字段，但必须真正断言拒绝、可定位诊断和没有可靠统计。`all_missing` 的规范含义可映射为原契约 `present_all_missing`；零行的观察状态仍为 unknown，不能映射成 all_missing。成功计数声明均要求模型保留声明 ID、来源及实际 hash、行数依据、padding 与 `trusted_delivery_declaration_not_independently_verified`，且 approved 新增数为 0。

## 实际检查、限制与共同失误风险

实际执行：JSON 成功解析、32 个案例 ID 唯一、读取基线的 XPT hash／OBS／payload／候选相符、派生 blank-tail hash 及 16 个候选相符；旧预期 hash 保持不变。检查的是本预期的可恢复输入与算术，不是产品行为。**engine 用例执行为 0、结果 not_run。** RC29–RC32 尤其必须在未来真实模型／patch／运行链路上执行，当前没有伪造成功记录。

生成过程中曾把空 VS 的变量计数草拟为 null；在冻结前对照已批准 C04，纠正为 0，并保持观察状态 unknown。这是预期草稿复核纠正，不涉及运行失败、放宽批准答案或修改原文件。最终固定 hash 对应纠正后的版本。

共同失误风险：本预期与实施者共用同一读取契约；若误读 padding 条款，可同时犯错。以短行 DM、5 字节全空白 VS 和 84 字节 UTF-8 行三个独立算术例降低风险，但不能消除此风险。来源文件说明也由测试制造者产生，无法独立证明实际研究声明真实性；测试需检查绑定和限制说明，不能把“hash 匹配”升级成“提供者或记录数真实性已验证”。最终技术审阅者应重新查看实际字节、测试是否覆盖全部分支，并检查生产 reader 不读本预期或制造配方。

本次仅新增本报告及 v0.2 预期文件。未修改原预期／夹具／契约／任务卡，未运行临床处理、未提交或推送。主 Agent 可记录该 hash 并在对应 reader 逻辑实现前冻结，随后以真实实现结果填充实际证据；本报告不替代最终独立技术审阅或 Chris 的 GATE-2 批准。

时序补充：主 Agent 在本文件完成后通知，本审阅者已发送上述独立字节结论之后、完整 JSON 预期 hash 冻结之前，主 Agent 写过 reader 草稿；主 Agent 声明尚未运行或正式采纳该草稿。审阅者没有查看该草稿或任何实现结果，答案仍从原字节与契约独立导出。此事实限制了“全部完整预期先于任何代码草稿”的表述；本报告仅能证明独立字节结论先提供、完整预期在首次 reader 执行／正式采纳前固定。最终独立技术审阅须保留并评估该时序，不将它静默改记为严格无草稿的 test-first。
