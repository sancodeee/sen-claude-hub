# Environment And Discovery

## 本机入口

- 本机 Jenkins CLI 包装命令是 `/Users/sen/bin/jenkins-cli`
- 日常使用统一写成 `jenkins-cli ...`
- 不建议在说明里直接展开底层 `java -jar ...`，除非需要解释 wrapper 行为

## 底层行为

`jenkins-cli` 是一个 shell wrapper，会转发到 Jenkins 官方 CLI JAR：

```bash
java -jar "$JENKINS_CLI_JAR" \
  -s "$JENKINS_URL" \
  "$JENKINS_CLI_MODE" \
  -auth "$JENKINS_USER_ID:$JENKINS_API_TOKEN" \
  "$@"
```

同时它会清理常见代理环境变量，避免代理影响连接。

## 必要环境变量

- `JENKINS_URL`
- `JENKINS_USER_ID`
- `JENKINS_API_TOKEN`

## 可选环境变量

- `JENKINS_CLI_JAR`
  - 默认值：`$HOME/.local/share/jenkins/jenkins-cli.jar`
- `JENKINS_CLI_MODE`
  - 默认值：`-webSocket`
  - 允许值只有：
    - `-webSocket`
    - `-http`

## 正确查看帮助

顶层帮助不要写成 `jenkins-cli --help`。本机 wrapper 的正确方式是：

```bash
jenkins-cli
jenkins-cli help
jenkins-cli help <command>
```

示例：

```bash
jenkins-cli help build
jenkins-cli help console
```

## 建议的最小自检顺序

只做只读检查时，建议顺序如下：

```bash
jenkins-cli version
jenkins-cli who-am-i
jenkins-cli help <command>
```

如果只是确认某个子命令是否存在，优先使用：

```bash
jenkins-cli help <command>
```
