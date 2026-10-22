# 六卡新增行为独立技术审阅

2026-10-22；独立审阅者 `/root/review_policy_independent`，不是实施者。

结论：本次 CARD-01–06 的实现、固定预期与失败防线达到技术关闭条件；以下发现均已修复并按原场景复测。最终完整入口实际收集／执行 **133 项，全部通过**，无失败、错误、跳过、漏收集或未运行项。此结论不替代 Chris 的 GATE-2 批准；候选封装、恢复及确切交付 hash 以任务卡后续封存记录为准。

## 审阅范围与独立性

已读取根 AGENTS／GOALS、PLANS 当前状态及 CTRL-01／02、MVP-0.1 §3／§11／§12、REQUIREMENTS CTRL-05／06、ARCHITECTURE CTRL-04，以及审阅策略契约。检查 `review.py`、engine／model／decisions／CLI／reporting 集成，40 条 RP 测试、5 条新增失败回归及完整检查入口；另检查候选封装工具的白名单和不覆盖限制。

最终复核运行版本为 `define_auto 0.1.1`，依赖规则版本 `mvp01-rule-0.2`；已重读补充后的审阅策略契约，SHA-256 为 `659262ffd8d9c4c13f40007d2b28a8f31c8d9afc9c366dfb7ba33f2df9a676c6`。README 的新增操作示例与最终接口及隔离边界一致。

独立预期文件 `expectations/mvp01/v0.3/review-policy-cases.json` 的 SHA-256 仍为 `0e36a52f457072f624f094ffd426e8a7357bcf9fb22df75c3299043fd418fdf0`，作者为实施者之外的预期 Agent，状态明确为实现前技术推导，不是业务批准。旧 24 条批准基线和既有新增预期未改。实际结果从真实 XPT 字节、当前模型、CLI 产物和运行断言取得；合成非测试授权仅用于边界检验，未充当真实业务授权。RP08／09 检查实际部分缺失和数值零；RP27 检查真实 XPT 字符变量存储长度为 2 的违规场景，避免只验证 Spec 长度。

## 发现、修复与原场景复测

| ID | 原发现与影响 | 修复与复测 | 当前状态 |
|---|---|---|---|
| IP01 | DM.ARM 实际缺席时，type 规则因缺少观察字段而返回 `passed_local_rule`，虚报局部核查通过，影响 FR-005／014 | 记录 `not_evaluable`，规则及标准核查为 `not_completed`；独立原场景及 `test_unavailable_rule_is_not_pass` 通过 | closed_fixed |
| IP02 | 人工将普通字段冲突退回上游后，仅保存操作历史，策略投影与中文报告未体现返工；同一输入后续选值还可能关闭返工，影响 FR-006／015 | 人工返工进入阻断队列，中文对应字段显示上游返工；后续候选 patch 被 `returned_issue_requires_upstream_rework` 阻止；独立定点报告检查及原场景回归通过 | closed_fixed |
| IP03 | `return_upstream.value=[[]]` 先执行集合转换，发生未受控 `TypeError`，影响 NFR-004 | 先验证列表成员类型，再检查重复；原场景返回定位 `ContractError:invalid_return_scope`，输入模型不变；另独立运行畸形规则的真实 CLI，退出 1、结构化错误、无 traceback／输出目录 | closed_fixed |
| IP04 | 新增 No Data／有限标准检查／Comment 映射未进入完整覆盖表，FR-005／008／011 仍整行 not_run，影响 CTRL-06 | 按新版 RP 需求关联纳入当前适用子集，列 `new_policy_scope`、精确用例和实际结果，累计需求仍 partial；完整入口证据已独立核对 | closed_fixed |

原始三项失败保存于 `artifacts/MVP-0.1/independent-policy-before-20261022-01/checks.json`；原始覆盖缺口可从 `review-policy-suite-20261022-01/coverage.json` 复核。失败结果保留，没有修改预期迎合实现。实现还补存人工操作的完整依赖及审阅观察快照，沿用展示原／当前统计、候选和输入变化；独立 IP05 复核通过。所有已确认原因在依赖变化后清空当前适用性，历史保留；没有自动恢复旧验证或最终批准。

## 实际验证

使用项目现有 `.venv-mvp01\Scripts\python.exe`，无新增核心依赖、全局安装或外部临床数据处理。

```powershell
.venv-mvp01\Scripts\python.exe tools/mvp01/review_policy_independent_probe.py --run-id independent-policy-retest-20261022-02
.venv-mvp01\Scripts\python.exe tools/mvp01/run_checks.py --run-id independent-policy-full-20261022-02
.venv-mvp01\Scripts\python.exe tools/mvp01/review_policy_collection_probe.py --run-id independent-policy-missing-20261022-02
```

上述 run-id 已存在；复跑须使用新 ID。第一项 5 条独立探针通过；第二项完整 133／133 通过，精确源码／测试／工具 hash 在其 `inputs-manifest.json`，独立复核时无漂移，记录在 `independent-policy-retest-20261022-02/independent-source-verification.json`。完整套件包含旧 88 项、40 条固定 RP 与 5 条失败回归。

第三项实际从 unittest discovery 移除 RP40，运行余下 132 项且无测试失败／错误／跳过，仍以 `missing=[M01-RP40]` 和退出 1 阻断。此为漏收集故障防线通过，目标套件状态明确为 failed，不冒充完整检查通过。未改测试源码或删除必需登记。

## 结论边界

未提供／不可读／缺变量不会变成 No Data；可靠零行及实际全缺失自动标志与人工原因分别管理。测试确认仅模拟，普通确认需精确授权及当前事实。强制标准错误和额外对象须上游修复，不能以 Define 选值隐藏。沿用需新的人工授权、当前候选及依赖校验，并保留旧历史；下游验证／批准仍待重审。

当前未选择正式项目 IG／CT；合成锁版规则只证明有限规则接口，完整标准符合性 `not_assessed`，P21／XML 生成／XSD 未运行。未来 Comment 映射是结构化接口承诺，不是已生成 Define-XML。VLM／SUPP／完整 CT 服务及后续生成范围继续由原计划承接。没有剩余未关闭的本轮核心技术阻断；最终业务和阶段批准由 Chris 决定。
