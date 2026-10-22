# Task 001 技术依据与待确认边界

> v0.1 · 2026-10-20 · DRAFT；仅技术提案及一手资料核实，不批准业务语义。

最小方案采用本地文件、JSON 契约和 Python CLI，符合 ADR-001/002/003。当前只安装项目内夹具工具；没有实现核对引擎、数据库、Web 服务、XML 或 P21 适配器。未选 IG/CT 不影响研究无关的物理事实小样本审阅，但阻止任何标准符合性结论。

| 选择／资料 | 当前证据与用途 | 限制及落实阶段 |
|---|---|---|
| JSON + Python 标准库 | 可人工审阅和固定 hash；无需引入模型框架 | v0.1 仅文档约束与定点结构检查，不是完整 JSON Schema 验证器；MVP 0.1 才实现运行时模型约束 |
| pandas 3.0.6 + pyreadstat 1.3.6，仅夹具 | [pyreadstat 作者 API 文档](https://ofajardo.github.io/pyreadstat_documentation/_build/html/index.html)，write_xport/read_xport；本机实际写读结果见 materials 运行 | Python 3.12.13 项目 venv，精确依赖锁在 tools/task001；同库写读存在共同错误风险，补 SAS 原始字节检查及独立审阅。核心依赖选择仍待 MVP 0.1 |
| XPORT V5 原始结构 | [SAS 官方布局](https://support.sas.com/content/dam/SAS/support/en/technical-papers/record-layout-of-a-sas-version-5-or-6-data-set-in-sas-transport-xport-format.pdf)，pp. 3–7 的 80 字节记录、NAMESTR、缺失编码 | 仅固定两份单 member、ASCII 样本，不能推广为完整解析器。普通 .、.A、.Z 均缺失但保留代码；不测试真实 SAS 执行 |
| Define 2.1 目标 | [CDISC Define-XML v2.1 页面](https://www.cdisc.org/standards/foundational/define-xml/define-xml-v2-1-0) 确认版本定位、标准／CT 版本及 Origin 更新 | 网页不代替完整规范；本轮未获取登录后规范，不据此关闭 OQ-04 或证明 VLM No Data 序列化 |
| DDS-aligned 参考 | [DDE 固定 commit](https://github.com/cdisc-org/data-definition-engine/tree/dc3e47bc24e864805d998f663f6e85ddc32d0cd9)，本地 README、dds.yaml、两份 define.yaml 有分别命名的快照／hash | README 的 ADaM 输出仍列 Planned；未安装、未运行 DDE，不接受其输出能力作为本项目验收结果 |

本地来源与来源原 URL、检索时间、SHA-256 见 `artifacts/TASK-001/references/sources.json`；上游 commit=`dc3e47bc24e864805d998f663f6e85ddc32d0cd9`。DDE 代码／schema 与文档的许可区分按 README License 段及仓库 LICENSE 记录（MIT、CC-BY-4.0）；署名：Content based on Data Definition Engine (CDISC GitHub), used under CC-BY-4.0 where applicable。SAS PDF 与 pyreadstat API 页作为公开技术文档保存审阅证据，版权仍归原作者；不复制商业验证规则或使用受限账户。官方实现与标准规范分列。

## 最小 DDS 对照

以下行只核实锁定 `schemas/dds/define.yaml` 的类／字段存在及定义。未运行 LinkML 校验或转换；不能把“概念上相近”写成兼容通过。

| 项目对象／字段 | 固定 schema 定位 | 状态／差异 |
|---|---|---|
| Study identity | StudyMetadata.studyOID；MetaDataVersion 的 StudyMetadata mixin，约 307–335 行 | 概念映射；项目研究身份另保留 family |
| Dataset.name/domain | ItemGroup.domain/items，约 525–624 行；名称还受 GovernedElement/Labelled 影响 | 候选映射；project object_id 不直接等于 XML OID |
| Variable.type | Item.dataType，约 479 行 | 候选映射；character/numeric 到 Define datatype 不是此阶段自动转换 |
| Variable.design_length | Item.length，约 484 行，描述为 characters | **有语义差距**：本批 declared_length 明确 SAS 字节，非 ASCII／数值不能直接复制；物理存储与观察长度留 sidecar，MVP 0.3 须转换或报 gap |
| Origin/Method/CodeList | Item.origin/method/codeList，Origin.type/source/documents，约 489–520、1241–1267 行 | 保留候选；本批未验证 Origin 枚举映射或文档引用 |
| ValueLevel/WhereClause | Item.applicableWhen，WhereClause.conditions，Condition.operator/conditions，约 498–517、948–1013 行 | 组合条件概念映射；条件等价、VLM 身份、输出保真延期 MVP 0.2/0.3，不把不同 AST 默认为相同 |
| No Data | ItemGroup.hasNoData，约 614 行 | 实现字段存在不证明正式语义；变量／VLM 序列化与 OQ-04 仍开放 |
| Source/Evidence/Assertion/Issue/Patch/Approval/RG claim | 本项目 Evidence/Review Sidecar | 本阶段不承诺 DDE 原生兼容；不丢失原始候选、依赖和审签 |
| SUPP、ADaM lineage、Protocol/SAP | Artifact Model 扩展 + sidecar | 保留，精确映射在对应实现前补齐；不让 DDS 参考限制长期目标 |

OQ-05 的建议决策是：本阶段只冻结本项目的身份、断言和 sidecar 契约，锁定上述参考 commit；暂不引入 LinkML，暂不宣称可直接加载 DDE。Chris 接受此边界后，精确导出兼容性承接 MVP 0.3；该未验证部分继续保留，不作为 Task 001 已通过能力。

## 需 Chris 判断的具体方案

1. 批准 SYN001 的 DM/VS/AE/CM 和 24 条独立预期为首批 GATE-1 对象。它们故意含不完整设计／错误物理数据，不能作为递交级 SDTM 样本；作用是证明将来不会混淆缺席、空数据和冲突。
2. 接受字符 ASCII 全空格为缺失、.A/.Z 计入缺失但保留代码、零行不判全缺失、No Data 原因及 XML 标记保持未知。复杂日期／Unicode／其余特殊缺失、重复／歧义 Spec 等保留明确补测阶段。
3. 接受保守 patch 失效规则：输入未变而标准／规则／配置／schema／上游决定／结果相关工具变化时，不能证明不受影响便重审关联链。仅纯运行审计时间变化不触发业务重审。
4. 接受本阶段 DDS 对齐边界和覆盖表的落实阶段。本阶段不为任何未实现行为写 passed，也不请求提前批准 MVP 0.1。
