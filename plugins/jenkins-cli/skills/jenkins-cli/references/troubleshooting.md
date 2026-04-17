# Troubleshooting

本页只记录已从本机 `jenkins-cli` wrapper 验证过的错误与误区。

## jenkins-cli.jar not found

错误：

```text
jenkins-cli.jar not found: <path>
Download it from: $JENKINS_URL/jnlpJars/jenkins-cli.jar
```

含义：

- `JENKINS_CLI_JAR` 指向的文件不存在
- 如果未显式设置，默认路径是 `$HOME/.local/share/jenkins/jenkins-cli.jar`

## JENKINS_URL is not set

错误：

```text
JENKINS_URL is not set
```

含义：

- 未配置 Jenkins 服务地址

## JENKINS_USER_ID is not set

错误：

```text
JENKINS_USER_ID is not set
```

含义：

- 未配置 Jenkins 用户 ID

## JENKINS_API_TOKEN is not set

错误：

```text
JENKINS_API_TOKEN is not set
```

含义：

- 未配置 Jenkins API Token
- 不要在日志、回复或示例中回显这个值

## JENKINS_CLI_MODE must be -webSocket or -http

错误：

```text
JENKINS_CLI_MODE must be -webSocket or -http
```

含义：

- 传入了 wrapper 不支持的连接模式

## 帮助命令误区

本机 wrapper 不支持把 `--help` 当作顶层帮助入口。  
正确方式是：

```bash
jenkins-cli
jenkins-cli help
jenkins-cli help <command>
```

错误示例：

```bash
jenkins-cli --help
```
