# MVP 0.1 读取辅助声明独立准备复核

> 2026-10-21 · reviewer=`/root/mvp01_independent_prep` · 材料准备审阅；核心 engine=`not_run`，不是最终技术审阅或 GATE-2。

Chris，8 份实体 XPT 与原独立预期的大小／SHA-256 全部一致；8 条新增及 2 条原基线测试声明的 hash、member、记录数、编码与 provenance 绑定均正确。本次未发现阻断材料使用的技术问题。原预期未修改；辅助契约符合已接受 M01-D01 的可追溯声明方案，没有将测试声明升级为业务批准。

## 范围与独立方法

只读审阅读取上下文契约、materialize_inputs.py、8 份新增 XPT、两组 read-context／来源／manifest，以及基线制造配方。没有调用制造器或导入生产 reader，唯一写入为本报告。标准库代码直接从实际 MEMBER／NAMESTR／OBS 字节核对成员名、行宽、计数相容性与 padding；严格解码检查只针对字符单元。

第一次临时独立检查错把 DSCRPTR 头里的偏移当作 member-data，导致本审阅脚本断言失败；重新依据 MEMBER＋168 的实际数据字段修正后重跑，不修改被审阅文件，也不将该临时检查器错误认定为产品缺陷。

已读取任务卡最新 §7：Chris 直接接受“可追溯声明方案（推荐）”，范围是该方案，不是对所有后续代码字节批准。原 A22/A23 pending 保留为历史，通过新方案／版本补精确预期，不回写旧独立期望。

## 实体材料结果

| 输入 | 字节数 | 记录数 | 行宽 | padding | 编码 | 严格解码 |
|---|---|---|---|---|---|---|
| utf8 | 1600 | 1 | 84 | 76 | utf-8 | passed |
| invalid_utf8 | 1600 | 1 | 84 | 76 | utf-8 | expected_failure |
| nbsp | 1600 | 1 | 84 | 76 | utf-8 | passed |
| partial_date | 1600 | 1 | 84 | 76 | ascii | passed |
| scale10000 | 841440 | 10000 | 84 | 0 | utf-8 | passed |
| all_missing_codes | 4240 | 31 | 88 | 72 | ascii | passed |
| numeric_date | 1760 | 3 | 88 | 56 | ascii | passed |
| unknown_format | 1600 | 1 | 88 | 72 | ascii | passed |

invalid_utf8 的严格解码失败是预定负例事实；材料检查 passed 表示其失败字节正确制造，不表示未来生产 reader 已实现正确拒绝。数值单元不按字符 codec 解码。

8 个 declaration_id 唯一，研究 SYN001／family SDTM、实际 VS member 与文件 hash 一致，记录数为 int 并与固定人工预期一致。provenance 绑定制造来源 hash、source_id 及 `/files/<index>`，对应 file／hash／count／test_only 全匹配；制造来源还绑定原 recipe 与制造器实际 hash。两组 manifest 中全部 12 条条目大小／hash 一致。

原基线 DM=3、VS=0，绑定原冻结 XPT hash 与实际 member；来源 `/declarations/0`／`1` 进一步关联原 source-data.json 的 `/datasets/0/rows`／`1/rows`。仅核对合成制造输入中的数组长度、文件 hash 与声明，不在本报告输出行级数据。制造来源 SHA-256 为 `5af451f1e0101009b36588da9d5cfb8a6f36a0c2c0779eba9b3e7cc9c47bce7d`。这证明外部制造证据链匹配，不能证明 XPT 字节唯一决定了记录数。

## 契约与边界判断

- 契约明确声明是外部证据，保留 row_count_basis、声明及来源依赖；相容性不等于真实性。无声明歧义拒绝／gap、codec 显式指定、严格解码和数量／padding／描述符约束符合接受方案。
- 同一研究／family／member／hash 重复声明拒绝，研究及对象依赖变化需重审，符合既有身份与 CTRL-04；未创建 No Data 原因、HasNoData 或业务 approved。
- TEST／test_only 的普通运行拒绝要求已经写入，实际隔离必须由未来运行时测试证明。当前10条都是测试声明，不能用作真实研究交付方证明。
- 制造器读取固定独立 byte recipe 是构造测试输入，功能限于字节编辑、hash 校验和制造记录。生产 reader 仍须只读实际 XPT、Spec、声明及登记的来源，不得读取制造配方或期望答案。当前尚无核心实现；未来需审查导入与文件访问路径。
- 当前来源可从同目录 manifest 和来源记录自身的 source_id 定位。未来 Input Registry 必须显式登记 source_id 到实际文件的映射并核验 hash，不能靠文件名或枚举目录猜来源。
- 凭实际文件与静态脚本审阅，未见契约越出 Chris 接受的方案。契约／制造材料并不替代质量门确认；后续错误声明、源缺失、codec 失败、依赖失效等生产行为均仍 not_run。

## 执行与版本证据

本次独立材料断言 73 条全部 passed；engine 实际执行 0。未运行制造器，不测试输出目录拒绝路径；只验证其静态写新目录和固定 recipe/hash 机制。最终核心独立技术审阅及 GATE-2 未进行。

```json
{
  "input_sha256": {
    "docs/contracts/MVP-0.1-read-context-v0.1.md": "99629de2acd4263fa16d908fac18fe07974a8b3dc347314f2d7f626984614a3b",
    "tools/mvp01/materialize_inputs.py": "36952c9a8f765cb438b4ac211b9016d799e215ba9c91c225cc3dee684f76ed78",
    "expectations/mvp01/v0.1/additional-cases.json": "34a92d1a8dd8039b20cbf380985d63c47189b6d86fd9c96fa04d77c9f768d40b",
    "fixtures/mvp01/v0.1/read-context.json": "596d2df418bb09fdc958d065d2586f4f5aa4dd3d75e444005b48d15348780a98",
    "fixtures/mvp01/v0.1/manufacturing-record.json": "08d594a75845d04ba6c3f55536818a8949f784576a41aadb9dfb5eb098eae35a",
    "fixtures/mvp01/v0.1/manifest.json": "98e88fe8c507623dbaa2e15d44cde1b37984de4f3146371521945fd6220f629e",
    "fixtures/mvp01/baseline-context-v0.1/read-context.json": "dd2bb06e831e4fa6cb2ad435bdd9191ad7a0475b3a2c6de393ada0e907f1c7b6",
    "fixtures/mvp01/baseline-context-v0.1/delivery-record.json": "60aea2b0366ad3182d3cea2c8b2ad9f9e4327de817a107b79fd91189e94bfccd",
    "fixtures/mvp01/baseline-context-v0.1/manifest.json": "3927c937f3fbe773d5cd93e40d825afb5a5d308b9718ece96437ae17ce7dd5cb",
    "docs/tasks/MVP-0.1.md": "457bf4c98d8d919f62dee464fb008c60249f4dc2f5956192379e1270e48d2331"
  },
  "material_checks": [
    {
      "check_id": "RC-PREP-001",
      "check": "original expectation hash unchanged",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-002",
      "check": "test namespace/identity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-003",
      "check": "8 unique declarations",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-004",
      "check": "builder binding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-005",
      "check": "recipe binding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-006",
      "check": "utf8 bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-007",
      "check": "utf8 member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-008",
      "check": "utf8 provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-009",
      "check": "utf8 codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-010",
      "check": "utf8 layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-011",
      "check": "utf8 expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-012",
      "check": "invalid_utf8 bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-013",
      "check": "invalid_utf8 member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-014",
      "check": "invalid_utf8 provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-015",
      "check": "invalid_utf8 codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-016",
      "check": "invalid_utf8 layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-017",
      "check": "invalid_utf8 expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-018",
      "check": "nbsp bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-019",
      "check": "nbsp member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-020",
      "check": "nbsp provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-021",
      "check": "nbsp codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-022",
      "check": "nbsp layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-023",
      "check": "nbsp expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-024",
      "check": "partial_date bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-025",
      "check": "partial_date member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-026",
      "check": "partial_date provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-027",
      "check": "partial_date codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-028",
      "check": "partial_date layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-029",
      "check": "partial_date expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-030",
      "check": "scale10000 bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-031",
      "check": "scale10000 member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-032",
      "check": "scale10000 provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-033",
      "check": "scale10000 codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-034",
      "check": "scale10000 layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-035",
      "check": "scale10000 expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-036",
      "check": "all_missing_codes bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-037",
      "check": "all_missing_codes member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-038",
      "check": "all_missing_codes provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-039",
      "check": "all_missing_codes codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-040",
      "check": "all_missing_codes layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-041",
      "check": "all_missing_codes expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-042",
      "check": "numeric_date bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-043",
      "check": "numeric_date member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-044",
      "check": "numeric_date provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-045",
      "check": "numeric_date codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-046",
      "check": "numeric_date layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-047",
      "check": "numeric_date expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-048",
      "check": "unknown_format bytes/hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-049",
      "check": "unknown_format member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-050",
      "check": "unknown_format provenance",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-051",
      "check": "unknown_format codec/provider",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-052",
      "check": "unknown_format layout/padding",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-053",
      "check": "unknown_format expected decode outcome",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-054",
      "check": "baseline manufacturer recipe hash",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-055",
      "check": "baseline namespace/identity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-056",
      "check": "DM baseline hash/member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-057",
      "check": "DM baseline provenance/codec",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-058",
      "check": "VS baseline hash/member/count",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-059",
      "check": "VS baseline provenance/codec",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-060",
      "check": "fixtures\\mvp01\\v0.1\\all_missing_codes.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-061",
      "check": "fixtures\\mvp01\\v0.1\\invalid_utf8.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-062",
      "check": "fixtures\\mvp01\\v0.1\\manufacturing-record.json manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-063",
      "check": "fixtures\\mvp01\\v0.1\\nbsp.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-064",
      "check": "fixtures\\mvp01\\v0.1\\numeric_date.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-065",
      "check": "fixtures\\mvp01\\v0.1\\partial_date.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-066",
      "check": "fixtures\\mvp01\\v0.1\\read-context.json manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-067",
      "check": "fixtures\\mvp01\\v0.1\\scale10000.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-068",
      "check": "fixtures\\mvp01\\v0.1\\unknown_format.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-069",
      "check": "fixtures\\mvp01\\v0.1\\utf8.xpt manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-070",
      "check": "fixtures\\mvp01\\baseline-context-v0.1\\delivery-record.json manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-071",
      "check": "fixtures\\mvp01\\baseline-context-v0.1\\read-context.json manifest integrity",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-072",
      "check": "original expectation still unchanged",
      "result": "passed"
    },
    {
      "check_id": "RC-PREP-073",
      "check": "manufacturing script syntax",
      "result": "passed"
    }
  ],
  "engine_cases_executed": 0,
  "engine_result": "not_run",
  "test_declarations_reviewed": 10
}
```
