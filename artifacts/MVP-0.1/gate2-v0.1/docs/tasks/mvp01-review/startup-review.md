# MVP 0.1 独立启动准备审阅

> 2026-10-21 · reviewer=`/root/mvp01_independent_prep` · 仅准备与新增预期；核心技术审阅及实际引擎测试均 `not_run`。

Chris，当前任务卡承接了 Task 001 分配给 MVP 0.1 的范围；发现 1 项必须先解决的 XPORT 行数／契约阻断问题。新增预期另存 `expectations/mvp01/v0.1/additional-cases.json`，SHA-256=`34a92d1a8dd8039b20cbf380985d63c47189b6d86fd9c96fa04d77c9f768d40b`。23 条预期中，21 条为既有规则派生的固定技术预期，A22／A23 等待契约确认，核心执行均 `not_run`。

## 读取及独立性

已完整读取 AGENTS、GOALS、ARCHITECTURE（含 §1–4.1、字段责任、ADR）、REQUIREMENTS（含 CTRL-05/06、相关 FR/NFR/AC/OQ）、PLANS（含当前状态、阶段、CTRL-01/02/03、交接）、启动提示与任务卡、APR-20261020-02、冻结契约、技术依据、覆盖、原预期、Spec、patch、依赖。冻结包引用以包根解析；包内 DRAFT 是批准前历史。

独立实际核验 manifest SHA-256=`b9ce2f9788cb157b3cfde09d05de9165371a223a57a7425261b6a5db5f38fea3`，82/82 份文件大小和 hash 一致。本次未重复运行上游 109 项／91 项检查，不将它们作为本审阅的新执行。开始推导时 `define_auto/`、`tests/` 均不存在，没有实现输出。仅在下述两个新路径写入；未修改冻结包、原夹具、原预期或共享任务卡。

已使用 pdf Skill 读取固定 SAS 官方 PDF，使用本机现有 `C:/Users/Administrator/AppData/Roaming/kimi-desktop/daimon-bundle/runtime/git/mingw64/bin/pdftotext.exe`。PDF SHA-256=`c7c82e664651fdf7c74134b3536af2ba1c5c2834ca91ea427e886eea0b118ac3`。仅抽取布局正文，不修改 PDF、不安装依赖、不联网。来源：[SAS 官方 XPORT 布局](https://support.sas.com/content/dam/SAS/support/en/technical-papers/record-layout-of-a-sas-version-5-or-6-data-set-in-sas-transport-xport-format.pdf)。

## M01-IR-PREP-01：尾部 padding 无法唯一确定行数

严重性：阻断相关解析设计与 GATE-2；状态 `open`；主实施者已承接为 M01-D01／CHG-010。不能通过弱化 C01、暗增 row-count 字段或重算批准 hash 关闭。

SAS PDF p.3 规定物理记录 80 字节；p.6 规定数据流尾部以 ASCII 空格填充，没有特殊结束记录。NAMESTR 不提供观察行数。冻结 `dm.xpt` 长 1920，OBS 头偏移 1680，数据起点 1760，payload 长 160，stride=34。以下两个等式均已独立执行并成立：

```python
b = frozen_dm.read_bytes()
assert len(b[1760:]) == 160
assert b[1760 + 3 * 34:] == b" " * 58
assert b[1760 + 4 * 34:] == b" " * 24
```

因此可解释为 3 行加 58 字节 padding，也可解释为 4 行加 24 字节 padding。第 4 候选行全为 `20`，其中 AGE、ARMCD 都是 `2020202020202020`。按 SAS PDF pp.11、20–21 的 IBM 格式：正号，指数 32−64=−32，规范化尾数 `0x20202020202020 / 2^56`，值约 `3.687825414344431e-40`。不能以“数字全空格一定非法”排除该候选。

直接 `rstrip(b" ")` 会删掉合法尾部空字符内容／全空行；`floor(payload/stride)` 会把 padding 算作观察。要求所有候选行数唯一又会拒绝已批准 DM，不能静默选择该路线。VS 追加 80 个空格时，同一 payload 也可为 1–16 个全空 5 字节观察；零行则需要额外完整 padding 记录，不作该假设。

建议主实施者将可追溯可信行数辅助声明、无声明歧义拒绝等选项作为具体契约变更交 Chris 判断。本审阅没有建立该字段，也没有修改原 C01 答案。相关新增案例状态为 `pending_business_or_contract_confirmation`。

## 承接及新预期设计

对照冻结 coverage 分配到 MVP 0.1 的 FR-001/002/003/006/007/014/015/018、NFR-001/003/004/007、AC-01/02/05/08/11，当前任务卡 B01–B09 均有承接方向，未发现遗漏整个条款。新增技术预期聚焦 Unicode 字节／字符、编码、全部 SAS 缺失、日期原值／格式、重复与不支持 Spec、模型引用和 patch 授权。正例使用至少 80 字节行宽，以避免新增短行歧义干扰已有规则检验。

SAS p.27 明确 XPORT 不传递编码。Unicode 用例显式给测试配置 UTF-8，不猜系统编码；NBSP 按已批准 ASCII-only 规则保持非缺失。日期只检查数字／格式及字符部分日期保留，不引入日期插补或临床解释。全部测试授权必须 TEST／test_only 隔离，不能生成真实业务批准。

需要在完整套件继续落实：hash、路径和供应声明、独立字段冲突、reference 引用 gap、中文报告、HTML 转义、无行级身份信息、同输入稳定、零收集阻断。它们已在任务卡列明，新增预期不能替代完整必需清单。

## 验证与接续

本次已实际执行冻结 82 份副本核验、原 DM/VS NAMESTR／OBS／stride 字节核对，以及 DM 两候选行数等式。8 组新 XPT 输入以虚拟字节定义固定，包含 seed hash、定长字节修改、明确 payload／重复次数、padding、结果长度与 hash；独立按该定义重建到内存后，8/8 大小／hash 一致，UTF-8 中／é／NBSP 字节已断言。JSON 的 23 个案例 ID 唯一，21 fixed／2 pending。规模样本固定为 10000 行，未设未经批准的性能阈值。尚未将输入实体化为正式 fixture 文件，测试载体与运行时约束案例也仍需在实现时构造并执行，不能将其报为已运行。

`git -c core.whitespace=cr-at-eol diff --check` 实际通过；未改变 Git 配置。核心引擎执行数为 0；本文件不是最终核心技术审阅，不表示 GATE-2 或阶段验收通过。新增预期保留宽口径的“明确拒绝或 gap”等既有允许分支，实际接口确定后须逐分支断言，不能仅凭异常退出或字符串存在宣称通过。

下一步：处理 M01-D01 和质量门确认；落地并复核新增预期的固定字节输入；实现完成后由非实施者审阅确切代码、测试、运行和 manifest 版本，执行失败路径复核。
