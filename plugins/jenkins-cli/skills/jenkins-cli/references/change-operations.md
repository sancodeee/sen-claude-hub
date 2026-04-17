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
```

已验证参数：

- `-c`
- `-f`
- `-p`
- `-s`
- `-v`
- `-w`

使用原则：

- 这是变更操作，会真实触发其他项目的 Job
- 默认只说明命令，不自动执行
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

常见安全流程：

```bash
jenkins-cli get-job <job> > current-config.xml
# 审查并修改 XML
jenkins-cli update-job <job> < current-config.xml
```

说明：

- `update-job` 是 `get-job` 的反向操作
- 修改前优先先导出现有 XML，再审查差异
