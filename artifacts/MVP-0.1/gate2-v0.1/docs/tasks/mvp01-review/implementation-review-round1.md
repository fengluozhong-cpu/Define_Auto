# MVP 0.1 实现独立技术审阅：第一轮

> 2026-10-21 · reviewer=`/root/read_context_expectations` · 仅审阅 common／model／xpt／engine 的当前实现。decisions、CLI、报告及完整测试套件仍在编写，本报告不是最终整包审阅或 GATE-2 通过。

Chris，本轮发现 4 项需要关闭的问题；其中真实 XPT 头校验和模型／证据边界直接阻断当前技术交付。没有修改实现、测试预期或原夹具。只在 `work/mvp01-review-round1/` 保存可复现脚本和临时结果，正式发现及版本记录保存在本报告中。

## 对象、依据与实际复现

读取根 AGENTS、GOALS、PLANS 当前入口和 CTRL-01／02；本任务卡 §3／4／7／8；ARCHITECTURE §1–4.1／CTRL-04；REQUIREMENTS FR-002、NFR-004、AC-02、CTRL-05／06；冻结 Task 001 契约全文和 24 条批准预期；读取辅助契约全文及 v0.2 独立技术预期。审阅时核验版本并只针对以下源码 hash 作结论：

| 文件 | SHA-256 |
|---|---|
| define_auto/common.py | `f2db20dc55f03c43f1b0208b3c4b8b51c6471ea4bbfb7fbcbfaa67cc33615ff7` |
| define_auto/model.py | `a874271009e012260aa7b00e72210c4d4ac02739e77716357a2a8fca414e7124` |
| define_auto/xpt.py | `4d2a4d3726023025b7cc011de9f6630709aca0395414aa26b94ba0ef42945ba7` |
| define_auto/engine.py | `923aad503ffae316b5210b210fbaf0bc73bebb08c75338e7b2f79a0543fb5a55` |
| expectations/mvp01/v0.2/read-context-cases.json | `486069d14f3d8b22a88c6b25eeb1eb8485effbd96d846b01322de6e512c44f6a` |

实际命令：`.venv-task001/Scripts/python.exe work/mvp01-review-round1/reproduce.py`。脚本使用冻结合成包实际字节和显式隔离测试声明调用真实实现，不 mock reader；结果见同目录 `results.json`。该命令是独立缺陷复现，成功收集结果不等于产品测试 passed。最初脚本在 reader 错误时直接退出，随后改为逐项捕获错误，未修改被测实现或输入。以下每项均有具体观察或标明静态证据。

## M01-IR-R1-01：合法 MEMBER／OBS 头被拒绝

**严重性：P1／阻断。** 位置：`xpt.py::_header`，当前第 56–58 行；由 `read_xpt` 在 MEMBER、OBS 校验调用。

实际 `read_xpt(utf8_fixture_bytes, encoding='utf-8')` 抛 `ContractError(code='invalid_xpt_header', locator='240')`。MEMBER 是 8 字节固定字段中的 `MEMBER` 加两空格，OBS 则是 `OBS` 加五空格；当前实现把传入 token 直接加一个空格后拼接 `HEADER RECORD!!!!!!!`，只有长度 7 的 LIBRARY／NAMESTR／DSCRPTR 能碰巧匹配。冻结基线 reconcile 因此把合法 DM／VS 一并记成 unreadable，无法满足 C01／C04／C06／C07 及实际新增夹具事实。

修复建议：按实际 8 字节 token 字段构造完整固定头前缀，保持真实格式验证；不要为让样本通过跳过头检查。关闭证据应包含冻结 DM、空 VS、UTF-8 实体输入的真实读取，以及坏头仍拒绝的负例。

## M01-IR-R1-02：模型接受无批准的 approved 视图及无效对象／计数

**严重性：P1／阻断。** 位置：`model.py::validate_model`，当前第 27–61 行。

在真实 reconcile 得到的模型上逐一独立修改后，以下均被 `validate_model` 接受：

1. 把 variable 对象的 `kind` 改为 dataset，但仍保留 variable 字段和变量 object_id。
2. 在 variable 的 `approved` 视图直接写入 `label='TBD'`，没有任何批准断言、决定或授权；也发生在 `test_only=true` 模型。
3. 在 DM variable 的 observed 中把 missing_count 改为 999；其当前父域甚至因 R1-01 而 unreadable、row_count=None，但仍允许宣称可靠计数。
4. 把 expected label 断言改成占位符 `TBD`。

此外，删除 source.read_status 抛未经转换的 KeyError；不是可定位的 ContractError。核心危险是四视图只检查“存在”，approved 的授权校验仅落在 assertion 上，直接伪造 approved 视图可绕开检查。当前对象 kind、父域状态／计数约束与断言 value 类型／必填未知值约束也不足。

修复建议：验证对象 kind／身份形状、四视图类型和其业务一致性；approved 视图须与有效批准断言／决定／授权闭合，测试模型禁止真实 approved；按字段区分合法 unknown（例如 origin 候选）与不得为占位符的必填 label／类型／长度；只在可读且有可靠分母时接受观察计数。缺失必需字段应成为可定位的契约错误。新增回归必须真实构造这些坏模型并证明拒绝，不能只检查 dataclass 或 JSON 可序列化。

## M01-IR-R1-03：provenance 可指向错误声明，负数组索引也被接受

**严重性：P1／阻断。** 位置：`xpt.py::validate_context` 末尾及 `common.py::pointer`。

真实 baseline DM 的声明 count=3、hash=DM。在其一声明隔离上下文中，只把 provenance.locator 从 `/declarations/0` 改为 `/declarations/1`；实际来源的后者是 VS、count=0、另一 XPT hash。`validate_context` 仍成功。把 locator 改为 `/declarations/-1` 也成功；Python 的 int(-1) 索引被当作 JSON Pointer，而应是不存在的数组索引。独立调用 `pointer({'declarations':[{'a':1},{'b':2}]}, '/declarations/-1')` 返回最后项。

当前只证明“某个 JSON 值存在且整个源 hash 相符”，没有证明所指定位支持该目标 DM 声明；因此 field-level provenance 会关联到错误研究输入／数量证据。此处不是要求 CLI 独立证明交付者身份或真实计数，而是要求它不要接受已经可观察到的错目标引用。

修复建议：JSON Pointer 数组 token 按规范验证非负十进制且无无效前导零；对当前支持的结构化交付证据，解析 locator 指向的声明，并核对 member／XPT hash／count／encoding 的相容性。若未来来源是 PDF／文本等，需显式支持其定位方式并保留限制，不能把任意指针存在当作已验证目标绑定。至少增加 DM 指向 VS、负索引及正常来源定位的实际回归。来源真实性限制仍须保留。

## M01-IR-R1-04：空格规范化后原始 label 值丢失

**严重性：P2／当前范围应关闭。** 位置：`xpt.py::read_xpt.decode` 及 `engine.py::evidence`。

静态证据明确：所有字符串一经 decode 就 `.strip(' ')`；变量／dataset label 只返回此规范化结果。随后 engine.evidence 将相同 value 同时复制进 raw_value 与 normalized_value，没有其他原始 label 字段。独立实际模型中观察 evidence 的这两项也相等。尝试使用仅修改 label padding 的实体 UTF-8 沙箱输入，读取被 R1-01 提前阻断，所以该专门运行时路径需在头修复后重测；本报告不把它写成已成功运行的 label 提取。

冻结契约 §3 明确要求“空格去除等规范化保留 raw，并按版本规则执行”。原文件 hash／locator 使追溯到字节成为可能，但不满足 raw_value 字段实际保存原值的承诺。

修复建议：保留标签原始字节或未裁空格原文，并另存规范化候选及变换规则；字符数据只能保留隐私安全的聚合原始事实，不为修复 raw 保存要求而暴露受试者行级值。用带左右空格的 label 及普通 label 实体输入验证规范化值、raw 值和来源偏移；报告只消费同一模型。

## 正面观察、限制与时序风险

当前 source registry 对主 manifest 提供文件的根内相对路径、实际 hash、不提供却存在文件等边界有显式检查；context／provenance 作为独立输入登记，依赖快照包含其 hash；默认不产生 approved；USUBJID／SUBJID／STUDYID 的 observed_values 被屏蔽，输出是聚合而非逐行数组。这些静态防线仍需完整负例与 CLI 链路验证，不是对所有输入保护／隐私／稳定性已通过的声明。

完整 32 个独立读取预期的冻结晚于未运行 reader 草稿，但独立字节结论先提供，且本审阅者未读实现或实现结果来生成答案。补偿措施：保持预期 hash 不变；本轮另行从真实字节／契约作对抗复现；保存当前源码 hash 和原发现；修复后以同一输入和同一断言复测，并由最终独立审阅核对全部分支收集执行。此措施降低答案迎合风险，不能把时序历史重记为严格先测后写。

本轮结论为 **存在开放技术阻断，尚不具备 GATE-2 技术关闭条件**。后续决策、CLI、报告、完整检查入口及依赖恢复尚未整体审阅；最终报告必须重新绑定修复后版本、完整测试证据及关闭情况。Chris 的最终批准仍独立管理。

## RC 自动化补充执行及新增发现

本报告初稿后，主 Agent 已修正头字段、部分模型及 provenance／raw-label 问题，并明确委派本审阅者新增 `tests/test_read_context.py`。该文件仅消费上述固定预期，没有修改答案或生产实现。测试使用真实 `validate_context`／`read_xpt`／`reconcile`／`apply_decision`；32 个 unittest 方法、37 个独立场景分支全部被选中执行。RC29–31 经过实际重跑、人工决定尝试复用与下游 applicability 路径，未用 compare_dependencies 代替业务行为。拒绝测试核对相应语义错误码集合，并对数量不相容、错误 ASCII 解码另直接验证真实字节，避免被无关 ContractError 掩盖。

实际命令：`.venv-task001/Scripts/python.exe -m unittest discover -s tests -p test_read_context.py -v`。本轮两次运行均为 32 tests，1 failure、1 error、0 skipped；其余 30 个方法通过。上述执行不是最终固定版本总回归，且不能继承为 R1-02／03／04 全部回归关闭。执行时 engine.py SHA-256=`a0cd2db5f8f80d124c32e395a3f20c3d58a166aff9ac56d3df65f736e848312b`、xpt.py=`ebf50353473dbf8c67c62405616f70ee822860c6a5e6cce6a637edc48f92df04`。

### M01-IR-R1-05：已登记但缺失的 provenance 文件抛原始 OSError

**严重性：P2／当前范围应关闭。** RC15 将 provenance.source_id 显式登记到一个不存在的本地交付文件路径，再调用实际 reconcile。engine.py 在 `Path(path).read_bytes()` 抛 FileNotFoundError，未形成带 source_id 的 ContractError。CLI 当前故障包装可能另外记录错误，但核心 API 未满足可定位的失败契约；不能把原始 Python traceback 当成规范诊断。

关闭需把不可访问来源文件转换为可定位错误，并通过固定 RC15。输入丢失仍必须阻断，不得因转换异常而忽略来源继续运行。

### M01-IR-R1-06：实际生效编码只有上下文 hash，依赖快照未保存可恢复值

**严重性：P2／当前范围应关闭。** RC31 创建新的合法 DM UTF-8 声明／来源，保留 XPT 字节并实际 reconcile。依赖 snapshot 只有 READ-CONTEXT 的 hash／版本，config.encoding 仍是 fallback ascii；整个 snapshot 不包含实际生效的 utf-8，也没有内嵌声明内容。虽然 hash 变化已能保守触发重审，但契约 §3 要求“辅助声明与生效编码进入 DependencySnapshot／Run Manifest”，ARCHITECTURE CTRL-04 又要求有效配置可恢复。只有 hash 而没有实际生效值不足以准确说明每个输入使用了何种编码。

关闭可通过在依赖快照保存版本化声明内容及按对象的生效 codec，或清晰可恢复的有效配置结构；不新增业务语义。固定 RC31 必须实际验证新编码记录及旧决定／下游需重审路径。

## 第一轮修复后的独立复测与关闭

主 Agent 修复后，本审阅者保留上述原发现及失败记录，重新实际运行：

1. 原独立缺陷复现脚本，输出另存 `work/mvp01-review-round1/results-retest.json`，不覆盖初始 `results.json`。真实 UTF-8 已读 1 行；kind 伪造、无授权 approved、999 计数、TBD label、缺 source 字段、错目标 provenance、负数组索引均以对应 ContractError 拒绝。空格 label 的未裁原文与规范化结果分别保留。
2. `.venv-task001/Scripts/python.exe -m unittest discover -s tests -p test_read_context.py -v`：32 tests、37 固定独立分支，0 failures、0 errors、0 skipped。RC15 及 RC31 原失败均已通过；RC29–31 包含真实人工决定复用／下游失效路径。
3. `.venv-task001/Scripts/python.exe -m unittest tests.test_boundaries.RuntimeBoundaryTests -v`：7 tests，全部通过，0 failure／error／skip。覆盖修复回归、主 manifest 边界、来源定位、raw label／隐私、HTML／Markdown 转义、输入排序稳定、真实 CLI 交付 hash 及拒绝覆盖。
4. 追加独立构造 resolved issue＋不存在 decision_id 的负例，实际拒绝为 `missing_resolution_decision`。这一项与原 R1-02 同属模型引用闭合，不能仅以非空 ID 替代有效决定。
5. 独立查看 dataset 层：DM／VS observed.raw_label 保留 40 字符原文；`DM/label/descriptor`、`VS/label/descriptor` 的 xpt_ascii_trim_v1 Evidence 分别保存原始标签与规范化标签。R1-04 的 dataset 与 variable 两部分均已取证。

复测版本：common.py=`d741f19445a487343f8354edf021ee09f270c24eaa43f214723c9ba0a5947c54`，model.py=`00d7fd61f89e06fc378373d4c57cc98c34745cb4b2751bff64ca39c3af028216`，xpt.py=`ebf50353473dbf8c67c62405616f70ee822860c6a5e6cce6a637edc48f92df04`，engine.py=`6e106c64c84661044e504e2bbc2e42ebd8f10341429f569a8aba51a0914475ab`。模型在修复期间继续增加引用约束，追加 resolved 负例及最终版本另行核对；不把早一版复现自动当作后一版全面验证。

**M01-IR-R1-01 至 R1-06 在上述复测范围内技术关闭。** 完整质量门仍需最终整体审阅、完整检查入口及冻结交付版本证据，本报告不将第一轮技术关闭等同于整包 GATE-2 通过。
