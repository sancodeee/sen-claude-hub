# Dangerous Operations

本页收录高风险命令。  
这些命令默认不要执行，必须先提醒风险并获得明确确认。

## 删除 Job

查看用法：

```bash
jenkins-cli help delete-job
```

真实格式：

```bash
jenkins-cli delete-job <job>
jenkins-cli delete-job <job1> <job2>
```

风险：

- 会直接删除一个或多个 Job
- 删除前必须确认目标名称完全正确

## 安全重启

查看用法：

```bash
jenkins-cli help safe-restart
```

真实格式：

```bash
jenkins-cli safe-restart
jenkins-cli safe-restart -message "maintenance"
```

风险：

- 会让 Jenkins 进入安全重启流程
- 会影响整个平台，不是单个项目范围内的动作

## 立即重启

查看用法：

```bash
jenkins-cli help restart
```

真实格式：

```bash
jenkins-cli restart
```

风险：

- 会立即重启 Jenkins
- 比 `safe-restart` 风险更高
- 默认不自动执行

## 默认处理策略

- 用户未明确授权时，只解释命令，不执行
- 用户已明确授权时，仍需再次确认目标与影响范围
- 如果只是为了验证文档正确性，只运行 `help`，不要运行真实高风险命令
