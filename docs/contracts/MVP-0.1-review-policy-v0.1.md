# MVP 0.1 审阅策略扩展 v0.1

2026-10-22。业务依据：任务卡 §11 的 CARD-01–06／CHG-012–016 及 Chris 本轮实施授权。此为这些已确认规则的实施契约，不替代原始批准契约；旧冻结包与预期保持只读。

## 模型与状态

原 `observed` 保留物理观察和未知业务原因，不将策略写回原始事实。模型新增 `review_policy`，版本 `mvp01-review-0.1`；同一模型快照向 CLI、Markdown、HTML 提供自动 No Data 标志、待人工确认队列、上游返工、标准核查状态及决定沿用影响。

计划数据集可靠可读且 row_count=0 时自动 HasNoData=Yes；计划变量实际存在、可靠父域 row_count>0、nonmissing_count=0 且 missing_count=row_count 时自动 HasNoData=Yes。缺文件、读失败、缺变量、零行父域的变量均不作此推断；保留 SAS 缺失代码。每个标志绑定当前依赖、观察证据及确定性规则。原因初始为空、确认 pending。

原因由有授权的人员确认，非空且不能是占位符；保留确认人、时间、理由、当前依赖及原记录关联。数据集目标为 ItemGroupDef/@def:HasNoData 与 CommentOID→CommentDef；变量目标为 ItemRef/@def:HasNoData 与 ItemDef/CommentOID→CommentDef。这里只存后续生成所需的结构化内容及目标，不生成 XML，不声称已完成 XSD／P21／递交验证。测试确认仅 test_simulated，不产生真实 approved 元数据。

缺输入／读失败／缺变量明确要求人工确认。额外对象的 issue 强制 upstream_rework，不能靠字段裁决或文字说明关闭。只有新版本输入实际消除问题，重新核对才撤销当前返工；历史保留。

## 锁版规则的有限执行面

未输入规则文件时 standard_check=not_completed，标准参考仍 gap。不自动选择 IG／CT，不将 Spec 与 XPT 比较当成标准核查通过。可用 `--review-rules` 提供本地已授权规则摘录：版本、IG／CT 标识、来源定位和 SHA-256，规则精确指定对象、字段及约束。本阶段支持 type、flag_length 和 label_exact；label_exact 仅允许明确的 SDTMIG 3.2 及以前版本；后续版本的 label 语义等价不由字符串相等判定。

规则文件是显式输入，全部内容及 hash 进入依赖；每条规则必须有依据定位和适用版本，引用已登记对象，不支持的规则拒绝。普通路径拒绝 test_only。规则同时检查 Spec 设计与 XPT 事实；确定违规产生标准错误／upstream_rework，人工选择不得消除。通过只表示列明的局部规则通过，完整标准符合性始终 not_assessed。此接口不是完整 Standard Provider、CT 服务或 P21 引擎；合成规则测试不能用于真实合规声明。

## 人工操作及沿用

新增 `--review-action` JSON：`action_id, kind, object_id, reviewer, decided_at, rationale, dependency_snapshot_id, supersedes, value`。kind 为 confirm_no_data、return_upstream、confirm_reuse。授权 scope 精确绑定整个 action；源文件 hash 登记沿用既有授权机制。action_id 同内容重复幂等，同 ID 异内容拒绝，修订必须指向当前同对象／同操作记录。没有真实授权的测试操作只能在隔离模型模拟。

confirm_no_data 的 value 为人工原因文本；执行前重新检查当前自动 No Data 事实。return_upstream 的 value 为待处理 issue ID 列表，只登记返工，不关闭问题。confirm_reuse 的 value 为原 decision_id：必须保有原记录及原依赖，当前确有 XPT 输入变化，Spec、规则及其他结果相关依赖不变；读取声明变化可伴随 XPT 更换，但必须重新读取验证。展示前后输入、对象统计／候选、其他依赖及影响链。重新校验对象／字段／当前候选／标准错误，生成新 ID＋supersedes 的决定并绑定新授权与当前依赖。它不恢复历史验证／最终批准，仍要求重跑。

No Data 原因的沿用通过新的 confirm_no_data＋supersedes 完成：当前事实仍须成立，旧理由只作为人工可见的历史，不自动填充。依赖变化后的所有当前原因确认清空，旧记录保留；仅审计时间变化则保留适用性。

审阅记录保存完整依赖快照及当时聚合统计；字段决定另保存当时统计和候选。沿用界面同时展示前后统计／候选及输入差异。历史缺少原统计的旧版本决定不补造历史值，显示未知并保守重审。动作时间必须是带时区的 ISO 8601；动作授权 scope 是整个 action 对象，包含原因、当前依赖和修订关联，不只是对象名。

规则输入 wire schema 为 `mvp01-review-rules-0.1`：顶层精确包含 `schema_version, version, ig_version, ct_version, test_only, source_id, rules`。rules 每条精确包含 `rule_id, object_id, kind, value, locator`。支持 kind=`type`（character／numeric）、`flag_length`（1）、`label_exact`（明确 IG 3.0–3.2）、`label_semantic`（仅标人工语义审阅）。locator 指向规则摘录的依据位置；输入文件本身作为 `review_rules` 来源保存实际 hash，并与依赖绑定。未选 CT 可明确填写 `not_selected`，该输入仍只支持列明局部规则，不代表 CT 检查完成。缺失可检查的设计／实际字段时记录 not_evaluable／not_completed；不能按空集合默认通过。

人工 return_upstream 同样投影到当前返工队列及报告，不改变 issue 的未解决状态；同一输入下不能用字段选值撤销返工。原因确认和沿用动作分别经当前约束检查，所有操作先在副本构造，错误不部分写入原模型。持久化恢复先验证 sealed 模型摘要和政策事实一致性；构造型 API 重新计算派生政策，不能信任外部提供的 eligibility 标记。

## 验证与权限

新增独立预期见 `expectations/mvp01/v0.3/review-policy-cases.json`，SHA-256=`0e36a52f457072f624f094ffd426e8a7357bcf9fb22df75c3299043fd418fdf0`；40 项在对应核心逻辑前由独立 Agent 固定。全部旧 88 项继续必测，另加 5 项技术边界回归，全部进入完整检查入口的独立必需登记。最终候选另存版本，技术通过不等于 Chris 的 GATE-2 批准。
