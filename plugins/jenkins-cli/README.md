# Jenkins CLI

供 Claude Code 和 Codex 使用的 Jenkins CLI 技能，包含风险分级指引及随包 Bash wrapper。

## 首次使用

依赖 Bash 3.2+、与目标 Jenkins CLI JAR 兼容的 Java，以及从目标服务 `/jnlpJars/jenkins-cli.jar` 下载的官方客户端。插件不包含 Java、JAR 或认证凭据。

安装插件后，按 [环境准备与安装说明](skills/jenkins-cli/references/environment-and-discovery.md) 解析实际插件根目录、准备依赖和配置。默认直接通过 Bash 运行随包脚本，无需复制脚本或额外安装终端命令；不依赖作者机器上的路径。

随包的 `download-client.sh` 将 JAR 下载到临时文件，校验后再替换；失败时保留原有文件。wrapper 会隐藏配置加载的原始输出，并在参数错误时拒绝把本地选项转发给服务器。

在本插件目录内可直接查看帮助：

```bash
bash skills/jenkins-cli/scripts/jenkins-cli.sh --help
```

`--check` 只检查本地依赖与配置；`-version` 查询本地客户端版本；`version` 查询服务端版本。构建、修改、删除及重启须满足技能中的授权要求，Shell 调用仍由宿主权限控制。

## 终端命令自动跟随更新

需要在终端直接运行 `jenkins-cli` 时，按 [自动转发安装说明](skills/jenkins-cli/references/environment-and-discovery.md#终端命令与自动跟随更新) 创建轻量入口，不复制插件脚本：

- **本地源码插件**：入口调用已核实的稳定源码目录，脚本修改会在下一次调用生效，包括未提交的修改；不自动拉取源码。源码目录移动后需重新配置入口。
- **版本化缓存安装**：默认由 skill 解析当前插件根目录；只有核实宿主提供稳定入口或权威运行时安装记录后，才配置终端入口。没有可用接口时继续通过 skill 调用，或使用稳定本地源码方案，不固定到某个版本的缓存路径。

已有命令先检查、备份，再迁移；现有 Java、JAR 和连接配置继续保留。详细安装示例包含路径校验、已有入口保护及验证步骤。

## 验证

```bash
python3 -m unittest discover -s skills/jenkins-cli/tests -v
bash -n skills/jenkins-cli/scripts/jenkins-cli.sh
bash -n skills/jenkins-cli/scripts/download-client.sh
```

测试使用临时文件和替代 Java 进程，不连接真实 Jenkins。
