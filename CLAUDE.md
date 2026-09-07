# Claude 工作入口

本项目使用 `playboy` Skill 维护跨会话、跨 Agent 的项目连续性。

开始有意义的项目工作前：
1. 使用 `playboy` Skill；
2. 阅读 `PROJECT.md`；
3. 阅读 `PROJECT_STATUS.md`；
4. 查看 `PROJECT_LOG.md` 的近期记录；
5. 如果项目使用 Git，检查当前状态并按需要查看近期历史；
6. 按 `playboy` Skill 做轻量状态一致性检查，只有发现明显矛盾时才继续追溯；
7. 再读取完成当前任务所需的实际项目文件。

形成自然检查点后，按 `playboy` Skill 维护状态、日志和安全的 Git 检查点。准备切换会话或 Agent 时，可显式调用 `$playboy handoff` 立即整理并落盘当前状态。

不要把项目长期事实、当前状态或工作历史堆积到本文件中。
