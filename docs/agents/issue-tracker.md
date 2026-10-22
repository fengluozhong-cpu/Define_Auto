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
