# Safe Operations

本页只收录已验证、常用、低风险的查询类命令。  
如果用户只是想了解怎么用，优先从这里选择命令，不要跳到变更类或高风险类命令。

## 版本与身份

查看 Jenkins CLI 版本：

```bash
jenkins-cli version
```

查看当前认证身份与权限：

```bash
jenkins-cli who-am-i
```

适用场景：

- 确认当前连接是否可用
- 确认当前账号是谁
- 排查“为什么命令没权限”

## 查看 Job 列表

查看根目录下的 Job：

```bash
jenkins-cli list-jobs
```

查看某个 View 或 Item Group 下的 Job：

```bash
jenkins-cli list-jobs <name>
```

适用场景：

- 查有哪些任务
- 确认 Job 名称是否正确

## 查看插件

查看所有已安装插件：

```bash
jenkins-cli list-plugins
```

查看指定插件：

```bash
jenkins-cli list-plugins <name>
```

适用场景：

- 确认插件是否安装
- 排查某个功能依赖的插件是否存在

## 导出 Job XML

导出某个 Job 的 XML 配置到标准输出：

```bash
jenkins-cli get-job <job>
```

适用场景：

- 审查现有 Job 配置
- 为后续 `update-job` 准备基线 XML

## 查看控制台日志

查看某个 Job 最近一次构建的控制台输出：

```bash
jenkins-cli console <job>
```

查看指定构建号的控制台输出：

```bash
jenkins-cli console <job> <build>
```

持续跟随进行中的输出：

```bash
jenkins-cli console <job> <build> -f
```

只看最后 N 行：

```bash
jenkins-cli console <job> <build> -n 200
```

适用场景：

- 看失败日志
- 跟踪正在运行的构建输出
- 快速查看尾部日志

## 关于 build 命令

`build` 命令本身存在且参数已验证，但它会真实触发 Job，属于变更类操作。  
查看参数说明时使用：

```bash
jenkins-cli help build
```

不要在未获明确授权时执行：

```bash
jenkins-cli build <job>
```
