# 工程 Skill 配置草案

> 2026-10-21 · Chris 已选择 GitHub Issues 和默认五标签；本文件展示拟写入的完整内容，等待 setup-matt-pocock-skills §3 确认后生效。

探索结果：origin=`https://github.com/fengluozhong-cpu/Define_Auto.git`；仅根 AGENTS.md，无 CLAUDE.md、Agent skills 配置、GLOSSARY、docs/adr、docs/agents、.scratch 或 monorepo 信号；本机已安装 triage。现有 ADR 主正文位于 ARCHITECTURE §10，继续作为权威位置；不为配置新建重复术语或 ADR 正文。当前 PATH 未发现 gh，远端标签实际同步须有可用工具和登录会话，未执行不得宣称已创建。

## 拟追加至根 AGENTS.md

```markdown
## Agent skills

### Issue tracker

工程 Issue 使用 GitHub Issues；阶段任务卡、证据与批准继续按本文件管理。调用工程任务 Skill 时读取 `docs/agents/issue-tracker.md`。

### Triage labels

使用五个默认 triage 标签；执行 triage 时读取 `docs/agents/triage-labels.md`。

### Domain docs

采用 single-context 布局；探索术语或设计决策前读取 `docs/agents/domain.md`，其中指向现有权威正文。
```

## 拟写入 docs/agents/issue-tracker.md

```markdown
# Issue tracker: GitHub

`fengluozhong-cpu/Define_Auto` 的 GitHub Issues 用于工程任务及实施需求摘要，通过 gh CLI 操作。正式需求、输入 Spec、契约、任务证据与批准记录仍按项目既有位置管理；现有 `docs/tasks/`、PLANS 及批准记录继续承担项目控制职责，Issue 引用相应记录。创建或修改 Issue 需要当前任务已有外部写入授权；本配置不自动启动建单或授予未来任务外部写入权限。

- 读取：`gh issue view <number> --repo fengluozhong-cpu/Define_Auto --json number,title,body,labels,comments`。
- 查询：`gh issue list --repo fengluozhong-cpu/Define_Auto --state open --json number,title,body,labels`。
- 已获授权时创建：`gh issue create --repo fengluozhong-cpu/Define_Auto --title "..." --body-file <utf8-body-file>`；多行正文使用 UTF-8 文件。
- 已获授权时评论：`gh issue comment <number> --repo fengluozhong-cpu/Define_Auto --body-file <utf8-body-file>`。
- 已获授权时标签操作：`gh issue edit <number> --repo fengluozhong-cpu/Define_Auto --add-label "..."`／`--remove-label "..."`。
- 已获授权时关闭：`gh issue close <number> --repo fengluozhong-cpu/Define_Auto`。

PRs as a request surface: no.

Skill 要求 publish to the issue tracker 时，目标是创建 GitHub Issue；要求 fetch the relevant ticket 时读取对应 Issue。操作前确认当前任务授权、数据公开范围及工具可用性；保密资料不写入远端。工具／登录不可用则记录未执行，不改用其他 tracker 或伪造结果。
```

## 拟写入 docs/agents/triage-labels.md

```markdown
# Triage labels

| Canonical role | GitHub label | 含义 |
|---|---|---|
| needs-triage | needs-triage | 等待维护者评估 |
| needs-info | needs-info | 等待补充资料 |
| ready-for-agent | ready-for-agent | 范围已明确，可由 Agent 执行 |
| ready-for-human | ready-for-human | 需要人工实施或判断 |
| wontfix | wontfix | 明确不处理 |

工程 Skill 使用上表映射；阶段任务状态及业务批准遵循项目 CTRL，不由标签替代。
```

## 拟写入 docs/agents/domain.md

```markdown
# Domain docs

采用 single-context。探索领域术语或设计决策前，先读取 ARCHITECTURE 的相关模块、契约、字段责任与 §10 ADR，以及当前任务引用的已批准冻结契约；适用范围和批准状态按 AGENTS／PLANS 判定。

若根 GLOSSARY.md 存在，读取相关词条并使用其术语；若 docs/adr/ 后续确有文件，读取相关 ADR，并核对与 ARCHITECTURE 的迁移引用。当前不存在的文件无需补建。将来迁移术语／ADR 必须按项目变更控制保留 ID、关联和单一权威正文，不能让 Skill 配置另建冲突规范。

输出中的对象名称采用现有契约术语；遇到术语缺口或与 ADR 冲突，明确指出并按项目授权处理，不能静默改写已批准决定。
```

配置写入确认只接受本草案内容及创建缺失默认标签，不表示批准新业务语义、GATE-2 验收或 Git 提交／推送。

2026-10-21 审查修订：已落实杂字符清理及 Issue／正式 Spec 权威边界澄清；本次只更新草案，正式配置写入及缺失远端标签创建尚未执行。恢复交接见 `MVP-0.1.md` §8。
