# Change Operations

本页只说明已验证的变更类命令和真实调用方式。  
默认不要执行，除非用户明确授权，并且目标 Job 与影响范围已经确认。

## 触发构建

查看用法：

```bash
jenkins-cli help build
```

已验证的命令格式：

```bash
jenkins-cli build <job>
jenkins-cli build <job> -w
jenkins-cli build <job> -s
jenkins-cli build <job> -s -v
jenkins-cli build <job> -p key=value
jenkins-cli build <job> -c
jenkins-cli build <job> -f
jenkins-cli build <job> -f -v
```

参数语义与中断行为：

| 参数 | 行为 |
|---|---|
| 无等待参数 | 提交构建请求后返回；退出成功不等于构建成功 |
| `-w` | 只等到构建开始，不等构建完成 |
| `-f` | 等到构建完成并返回构建结果；客户端中断不传给构建，中断时客户端退出码为 `125` |
| `-s` | 同步等待构建完成；客户端中断会传给构建，可能导致构建被取消 |
| `-v` | 输出构建日志，与 `-f` 或 `-s` 配合使用 |
| `-p key=value` | 传递构建参数，可按命令帮助重复指定 |
| `-c` | 检查 SCM 变更，无变更时不触发构建 |

用户需要等待结果并观察日志、且停止观察后构建仍应继续时，使用 `-f -v`。只有用户明确需要客户端中断同时取消构建时才选择 `-s`，并说明中断风险。代理超时可能结束客户端，不应默认使用 `-s`。

以上语义参考 [Jenkins 官方 CLI 文档](https://www.jenkins.io/doc/book/managing/cli/#build)，执行前仍核对目标服务的 `help build`。

使用原则：

- 这是变更操作，会真实触发其他项目的 Job
- 用户只咨询用法时说明命令；已明确授权且目标、参数、等待方式和影响范围齐备时，在授权范围内执行，不重复索要授权
- 执行前至少确认 Job 名称、参数、等待方式和影响范围

## 创建 Job

查看用法：

```bash
jenkins-cli help create-job
```

真实模式是从标准输入读取 XML：

```bash
jenkins-cli create-job <name> < config.xml
```

说明：

- `create-job` 读取 stdin 中的 Job 配置 XML
- 不存在“直接传 JSON”或“内联 key=value 创建 Job”的模式

## 更新 Job

查看用法：

```bash
jenkins-cli help update-job
```

真实模式同样是从标准输入读取 XML：

```bash
jenkins-cli update-job <job> < config.xml
```

每次变更使用独立目录，保留只读原始备份，在工作副本上编辑。以下示例先设置已确认的 Job 全名；准备命令失败时停止，不继续提交：

```bash
JENKINS_CHANGE_JOB='folder/job-name'
JENKINS_CHANGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/jenkins-job-change.XXXXXX")"
(
  set -e
  umask 077
  jenkins-cli get-job "$JENKINS_CHANGE_JOB" > "$JENKINS_CHANGE_DIR/before.xml"
  chmod 400 "$JENKINS_CHANGE_DIR/before.xml"
  cp "$JENKINS_CHANGE_DIR/before.xml" "$JENKINS_CHANGE_DIR/after.xml"
  chmod 600 "$JENKINS_CHANGE_DIR/after.xml"
)
```

只编辑 `after.xml`，不覆盖 `before.xml`；记录 Job 全名和备份目录，保留该目录用于回滚。提交前查看差异：

```bash
diff -u "$JENKINS_CHANGE_DIR/before.xml" "$JENKINS_CHANGE_DIR/after.xml"
```

`diff` 退出码 `0` 表示无差异，`1` 表示存在差异，其他值表示检查失败。差异须在已有授权范围内；如果目标、差异或影响范围改变，再确认变化部分。若 Job 在导出后被他人修改，重新导出并审查，避免覆盖后续变更。

已有有效授权且目标与差异核对完成后，提交工作副本：

```bash
jenkins-cli update-job "$JENKINS_CHANGE_JOB" < "$JENKINS_CHANGE_DIR/after.xml"
```

提交后重新读取 Job 配置，核对预期字段。需要恢复修改前配置时，使用保留的原始备份：

```bash
jenkins-cli update-job "$JENKINS_CHANGE_JOB" < "$JENKINS_CHANGE_DIR/before.xml"
```

回滚也是配置变更：先核对当前配置及已有授权是否覆盖本次回滚，避免覆盖他人后续变更；已有授权覆盖且范围未变时不重复确认，未覆盖时补充回滚授权。
