# Troubleshooting

本页对应随插件分发的 `scripts/jenkins-cli.sh`。使用其他现有 wrapper 时，先核对其配置来源和实际行为。

## 入口或 Java 缺失

- `command -v jenkins-cli` 无结果：按 [环境与安装说明](environment-and-discovery.md) 解析插件根目录，先通过 `bash` 运行随包脚本，不猜测用户目录。
- `java not found or not usable`：安装与 JAR 兼容的 Java，或通过 `JAVA_BIN` 指定可用路径。
- Java 类版本不兼容：`--check` 不验证 JAR 内容，使用 `-version` 核实本地 JAR 能否运行，再调整 Java/JAR。

## 配置文件缺失或配置不生效

- `JENKINS_CLI_ENV_FILE not found or not readable`：显式指定的文件不存在或不可读；默认文件可以不存在。
- 调用方导出的配置优先于文件；显式导出的空认证变量不会被文件值覆盖。
- 只检查变量是否存在，不打印 Token 或整个配置文件；排查前核对 `JENKINS_CLI_ENV_FILE` 指向的可信本地文件。
- `JENKINS_CLI_ENV_FILE could not be loaded`：配置存在语法、执行错误或不兼容的变量属性，wrapper 已隐藏可能包含凭据的原始输出并停止。用户应在本地对照模板使用字符串赋值，去掉整数、数组或只读声明；不要将完整文件或原始错误粘贴到聊天中。

## 本地选项参数错误

- `Local options do not accept extra arguments`：`--help`、`-h`、`--check`、`-version` 须单独调用，例如把 `--check --verbose` 改为 `--check`。
- `Unknown local option`：不支持该 `--...` 选项，先查看 `--help`；参数错误退出码为 `2`，不会读取配置或连接服务端。

## 下载失败或 JAR 校验失败

`download-client.sh` 下载失败或 Java 本地校验失败时，会清理临时文件并保留原有目标。核对服务地址、网络及 Java/JAR 兼容性后重试；不要把登录页或半成品手动移到正式路径。

## JAR 缺失或不可读

错误：`jenkins-cli.jar not found or not readable; set JENKINS_CLI_JAR`。

检查 `JENKINS_CLI_JAR`；默认路径为 `$HOME/.local/share/jenkins/jenkins-cli.jar`。从目标 Jenkins 的 `/jnlpJars/jenkins-cli.jar` 获取客户端，再分别执行 `--check` 和 `-version`。

## 必要配置缺失

错误分别为：

- `JENKINS_URL is not set`
- `JENKINS_USER_ID is not set`
- `JENKINS_API_TOKEN is not set`

先核对调用方环境，再核对可信本地配置文件。不要在日志、回复或示例中回显认证值。

## 无效地址或连接模式

- `JENKINS_URL` 必须是带主机的 HTTP/HTTPS 地址，不在地址中携带认证串或空白。
- `JENKINS_CLI_MODE must be -webSocket or -http`：wrapper 不支持该连接模式，核对环境变量及配置文件。

## 帮助与版本误区

随包 wrapper 的 `--help` 是不需要依赖和认证的本地帮助；`help` 则从服务端读取命令说明：

```bash
jenkins-cli --help
jenkins-cli help
jenkins-cli help <command>
```

`version` 返回服务端版本；`-version` 查询本地 JAR。连接失败时优先用 `--check` 和 `-version` 分离本地依赖问题与服务端问题。
