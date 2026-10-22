# MVP 0.1 读取辅助声明契约 v0.1

> 2026-10-21 · CHG-010／M01-D01 · Chris 已在本会话接受“可追溯声明方案”。字段编码为该方案的实施细化；不替换 gate1-v0.1，也不代表 GATE-2 通过。

## 1. 目的与适用性

XPORT v5 不包含可靠记录数与字符编码。仅靠尾部空格，某些文件存在多种合法行数解释。因此读取上下文单独提供编码，以及必要时的可信记录数声明；生产代码仍解析真实 XPT 描述符与每条记录，不读取 source-data.json 或任何预期文件生成观察结果。

声明是交付方对记录边界的外部证据，不是从 XPT 独立证明的事实。记录 `row_count_basis`，区分 `unambiguous_layout` 与 `delivery_declaration`。无声明且存在多个相容行数时，明确拒绝／gap；禁止默认裁掉尾部空白记录。只有唯一合法行数时才可由布局确定。

## 2. 最小 JSON 结构

顶层：`schema_version=mvp01-read-context-0.1`、非空 `study_id`／`family`、布尔 `test_only`、`declarations` 数组。每条声明包含：

| 字段 | 约束 |
|---|---|
| declaration_id | 非空且在文件内唯一；内容变化须新 ID，保留旧声明 |
| source_sha256 | 64 位小写十六进制，必须匹配实际 XPT 文件 |
| member | 与实际 XPT member 名一致，遵循已批准对象命名规则 |
| encoding | 显式 Python codec 名；不得从系统语言、文件内容或文件名猜编码；解码错误不得 replacement 后继续报告成功 |
| record_count | 非负整数或 null，bool 不算整数；null 不提供行数证据 |
| provided_by | 非空交付方身份；测试夹具明确 TEST 前缀；身份声明的真实性由交付流程负责，CLI 不声称验证了身份 |
| provenance | `source_id`、`source_sha256`、`locator`；指向一份可访问的交付证据，并验证 hash；不得以预期答案冒充真实研究交付依据 |

同一研究／family／member／文件 hash 的重复或冲突声明拒绝。声明目标不存在、来源缺失、hash 不符、数量不相容、尾部不是合法 padding、解码失败均不得输出虚假可靠统计。

记录数的相容性至少要求：描述符和布局有效；`record_count * row_width` 不超出 observation payload；剩余不足 80 字节且全部为 ASCII 空格；每个声明记录的单元格可按其实际类型／宽度读取。声明的数量本身不能由上述条件证明为真实，只证明与字节相容；报告明确保留该限制。

## 3. 证据与依赖

声明文件及 provenance 源均作为输入登记，保存实际 hash、定位和提取方法。辅助声明与生效编码进入 DependencySnapshot／Run Manifest；声明或来源／研究／member 变化须检查相关断言、决定和下游验证／批准的适用性，不能因 XPT hash 不变而盲目沿用。

模型保留解码记录数、行数依据、声明 ID、padding 字节数、声明来源以及 `trusted_delivery_declaration_not_independently_verified` 说明。任何报告均消费同一模型，不能在渲染时重新猜行数。

## 4. 合成测试与原基线

测试专用声明顶层 `test_only=true`，在明确隔离测试模式中使用；普通研究运行拒绝测试声明。声明不具有业务选值或 approved 断言的效力。

原 C01–C24、XPT／Spec 及批准包保持只读。测试载体可从已经独立审阅的合成制造材料，另做新版本的记录数／编码声明，再从真实 XPT 解码并逐例比较原预期；生产 reader 不访问制造配方或预期。新增负例证明无声明歧义、错 hash／member／数量、来源缺失／变更及测试声明越界都被检测。
