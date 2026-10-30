# Environment And Discovery

## 解析插件根目录

随插件分发的入口为 `skills/jenkins-cli/scripts/jenkins-cli.sh`，通过 Bash 运行，不依赖文件的可执行位。

- **Claude Code**：先执行 `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT is not set}"`。
- **Codex**：取本次实际加载的 `SKILL.md` 的绝对路径，从其父目录向上两级得到插件根目录，并将该绝对路径赋给 `PLUGIN_ROOT`。不要照搬 Claude 的赋值，也不要从当前工作目录猜测安装位置。

使用已解析的根目录读取本地帮助：

```bash
bash "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/jenkins-cli/scripts/jenkins-cli.sh" --help
```

该调用不读取凭据、不要求 Java/JAR，也不连接 Jenkins。后续示例中的 `jenkins-cli` 均指此脚本或调用它的终端转发入口。

## 依赖与首次安装

支持 macOS/Linux，要求 Bash 3.2+、可运行的 Java，以及从目标 Jenkins 下载的官方 `jenkins-cli.jar`。Java 版本应与该客户端 JAR 的要求匹配，不随插件分发 Java 或 JAR。

1. 用 `command -v jenkins-cli` 检查现有入口；已有命令时先核对其行为，避免覆盖。
2. 用 `java -version` 检查 Java；无 Java 或版本不兼容时先安装匹配的运行时，也可通过 `JAVA_BIN` 指定。
3. 显式导出目标 `JENKINS_URL` 后，使用随包下载脚本从该服务的 `/jnlpJars/jenkins-cli.jar` 获取客户端（需要 `curl` 和 Java）：

```bash
: "${JENKINS_URL:?请先设置目标 Jenkins 地址}"
bash "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/jenkins-cli/scripts/download-client.sh"
```

该脚本不读取共享 Shell 配置，使用调用方显式导出的 `JENKINS_URL`、可选 `JENKINS_CLI_JAR` 和 `JAVA_BIN`；JAR 默认路径与 wrapper 一致。它在目标目录创建临时文件，用 Java 的 `-version` 验证下载结果，再原子替换正式文件。下载、校验失败或收到普通中断信号时清理临时文件，保留原有 JAR；已有文件只在完整下载并校验通过后替换。

若服务需要登录下载，可用已登录浏览器先下载到单独文件，用 Java 验证后再替换目标文件，不直接覆盖现有可用 JAR。

4. 准备下文的环境变量或本地配置文件，再做本地自检：

```bash
bash "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/jenkins-cli/scripts/jenkins-cli.sh" --check
```

`--check` 只检查 Java 能否启动、JAR 是否存在且可读、配置是否完整及连接模式是否有效，不验证 JAR 内容、服务连通性或账号权限。

## 终端命令与自动跟随更新

默认由 skill 解析当前插件根目录并直接运行随包脚本，无需额外安装终端命令。需要在终端直接输入 `jenkins-cli` 时，使用轻量转发入口，每次调用插件中的实际脚本；不再将 `jenkins-cli.sh` 复制到 PATH 目录。

### 本地源码插件

先从宿主的插件登记信息核实稳定的源码目录；Codex 可通过 `codex plugin list --marketplace sen-claude-hub --json` 查看对应插件的本地 `source.path`。将下面的路径替换为已核实的插件根目录，目录内应包含 `skills/jenkins-cli/scripts/jenkins-cli.sh`。该路径应指向持续维护的源码目录，不要填写 `cache/.../1.0.1` 这类版本化缓存路径，也不要直接把当前加载的 `PLUGIN_ROOT` 当成稳定路径。

已有 `jenkins-cli` 时，先检查其位置与内容；确认转发入口指向稳定源码目录或使用已核实的运行时安装记录后，可继续使用。旧脚本副本或固定旧缓存路径的入口应备份后再替换。以下示例遇到已有目标时会停止，不会覆盖它。

```bash
export JENKINS_PLUGIN_SOURCE_ROOT='/absolute/path/to/sen-claude-hub/plugins/jenkins-cli'
bash <<'INSTALL' && export PATH="$HOME/.local/bin:$PATH"
set +x
set -euo pipefail

plugin_script="${JENKINS_PLUGIN_SOURCE_ROOT:?Set the verified local source directory}/skills/jenkins-cli/scripts/jenkins-cli.sh"
command_path="${HOME:?HOME must be set}/.local/bin/jenkins-cli"
if [[ ! -f "$plugin_script" || ! -r "$plugin_script" ]]; then
  printf 'Jenkins CLI plugin script not found or not readable: %s\n' "$plugin_script" >&2
  exit 1
fi
if [[ -e "$command_path" || -L "$command_path" ]]; then
  printf 'Command already exists; inspect and back it up before replacement: %s\n' "$command_path" >&2
  exit 1
fi

install -d "$HOME/.local/bin"
(
  set -o noclobber
  {
    printf '#!/usr/bin/env bash\n\nset +x\nset -euo pipefail\n\n'
    printf 'plugin_script=%q\n' "$plugin_script"
    cat <<'LAUNCHER'
if [[ ! -f "$plugin_script" || ! -r "$plugin_script" ]]; then
  printf 'Jenkins CLI plugin script not found or not readable: %s\n' "$plugin_script" >&2
  exit 1
fi
exec bash "$plugin_script" "$@"
LAUNCHER
  } > "$command_path"
)
chmod 755 "$command_path"
INSTALL
```

`printf %q` 将已核实的路径写为 Bash 字面量，支持目录名中的空格和特殊字符；转发入口通过 Bash 执行插件脚本，不要求源脚本具有可执行位，并保留参数、标准输入和退出码。

源码目录保持不变时，更新其中的脚本会在下一次调用立即生效，无需重新安装入口。这会使用当前源码内容，包括尚未提交的修改；不会自动执行 `git pull` 或下载插件版本。移动源码目录后需要重新配置入口，脚本缺失时会明确报错。

将 PATH 配置持久化到自己使用的 Shell 启动文件，已有 `$HOME/.local/bin` 配置时无需重复添加。重新打开终端或刷新命令缓存后，用 `command -v jenkins-cli` 确认入口位置，再执行 `--help`、`--check` 和 `-version`；服务端连通与认证按下文的只读连接自检验证。

迁移入口时保留现有 Java、`$HOME/.local/share/jenkins/jenkins-cli.jar` 和 `.jenkins-cli.env`，不复制或覆盖连接配置。安装依赖及写入用户目录属于准备环境操作，应在用户授权准备环境后执行。

### 版本化缓存安装

若宿主把插件安装在随版本变化的缓存目录，默认继续由 skill 每次解析当前插件根目录并运行随包脚本，不额外安装终端入口。

确需终端入口时，先核实宿主是否提供稳定入口或权威的运行时安装记录，并按该接口接入。本指南不提供跨宿主的缓存路径解析实现；未核实可用接口时，继续通过 skill 调用，或先准备持续维护的稳定本地源码目录，再使用上面的源码转发方案。不能把某个版本的缓存路径写死，也不能只按缓存目录名称排序来推断当前安装版本。

## 配置来源与优先级

服务端命令和 `--check` 需要：

- `JENKINS_URL`：HTTP/HTTPS 服务地址，不在 URL 中携带用户名或密码。
- `JENKINS_USER_ID`：用户 ID。
- `JENKINS_API_TOKEN`：API Token，仅在本地安全配置，不回显。

可选配置：

| 变量 | 默认值 / 作用 |
|---|---|
| `JENKINS_CLI_ENV_FILE` | `$HOME/.local/share/jenkins/.jenkins-cli.env`，可选的本地 Shell 配置；显式指定后文件必须存在且可读 |
| `JENKINS_CLI_JAR` | `$HOME/.local/share/jenkins/jenkins-cli.jar` |
| `JENKINS_CLI_MODE` | `-webSocket`，只允许 `-webSocket` 或 `-http` |
| `JAVA_BIN` | PATH 中的 `java`，也可指定 Java 可执行文件绝对路径 |

优先级为：调用方显式导出的环境变量 > 本地配置文件 > 默认值。必要认证变量显式设为空时仍按缺失报错，不回退使用文件中的凭据。

配置模板为 [jenkins-cli.env.example](../scripts/jenkins-cli.env.example)。仅在配置不存在时复制到上述默认位置，并设为 `600`，然后由用户在本地填写；已有配置应保留并审查。该文件通过 `source` 加载，只使用用户信任的本地文件，不加载下载的 Shell 内容。

配置使用普通字符串赋值或 `export NAME='value'`，不将上述变量声明为整数、数组、只读或其他特殊类型。加载及调用方覆盖恢复的输出和原始错误均不转发；加载失败或变量属性不兼容时，只返回固定诊断并停止，避免错误内容包含凭据。

wrapper 将认证变量导出给官方客户端，避免使用包含 Token 的 `-auth user:token` 参数；转发命令前会清理常见代理变量。参数、标准输入和客户端退出码保持不变。

## 帮助与版本

```bash
jenkins-cli --help           # wrapper 本地帮助，不连接服务
jenkins-cli -version         # 本地客户端 JAR 版本，不要求服务端认证配置
jenkins-cli --check          # 本地依赖和配置检查，不连接服务
jenkins-cli help             # 服务端可用命令，需要连接和认证
jenkins-cli help build
jenkins-cli help console
```

不带参数时转发到官方客户端的服务端帮助；不要使用未支持的 `--version`，也不要将 `version` 与 `-version` 混淆。

`--help`、`-h`、`--check` 和 `-version` 都是独立本地选项，不接受附加参数。附加参数或未知的 `--...` 选项会在读取配置、启动 Java 前以退出码 `2` 拒绝，不进入服务端转发流程。

## 只读连接自检

本地依赖就绪后，再检查服务端连接、身份及目标命令：

```bash
jenkins-cli version
jenkins-cli who-am-i
jenkins-cli help list-jobs
```

`version` 返回 Jenkins **服务端**版本，不能用来证明本地客户端版本。
