# Agent Browser 安装指南

本文档详细说明如何在不同平台上安装 `agent-browser` CLI 工具。

> 官方仓库: [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)

## 系统要求

| 平台 | 支持状态 | 架构 |
|------|----------|------|
| macOS | 完全支持 | ARM64 (Apple Silicon)、x64 (Intel) |
| Linux | 完全支持 | ARM64、x64 |
| Windows | 完全支持 | x64 |

**前置要求**:
- Node.js 18+ 或更高版本
- npm（通常随 Node.js 一起安装）

## 方法一：通过 npm 安装（推荐）

这是最简单快速的安装方式，适用于所有平台。

### 1. 全局安装 agent-browser

```bash
# 推荐使用
npm install -g agent-browser
```

或者使用其他包管理器：

```bash
# 使用 pnpm
pnpm add -g agent-browser

# 使用 yarn
yarn global add agent-browser
```

### 2. 下载 Chromium 浏览器

安装完成后，需要下载 Chromium 浏览器（agent-browser 的浏览器引擎）：

```bash
agent-browser install
```

这将下载约 684MB 的 Chromium 浏览器到本地。下载进度会显示在终端中。

### 3. 验证安装

```bash
agent-browser --help
```

如果输出了命令帮助信息，说明安装成功！

```bash
agent-browser open example.com
```

如果能够成功打开浏览器并访问页面，说明安装完全正常。

## 方法二：从源代码安装

适用于需要自定义构建或参与开发的用户。

### 1. 克隆仓库

```bash
git clone https://github.com/vercel-labs/agent-browser
cd agent-browser
```

### 2. 安装依赖并构建

```bash
pnpm install
pnpm build
pnpm build:native   # 需要 Rust 工具链 (https://rustup.rs)
pnpm link --global  # 使 agent-browser 全局可用
```

### 3. 下载 Chromium

```bash
agent-browser install
```

## Linux 特殊说明

在 Linux 系统上，除了 Chromium，还需要安装系统依赖。

### 自动安装系统依赖

```bash
agent-browser install --with-deps
```

这会自动安装所有必需的系统库。

### 手动安装系统依赖

如果自动安装失败，可以手动安装：

```bash
npx playwright install-deps chromium
```

### 常见 Linux 发行版安装命令

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install -y \
    nss \
    nspr \
    atk \
    at-spi2-atk \
    cups-libs \
    libdrm \
    libxkbcommon \
    libXcomposite \
    libXdamage \
    libXfixes \
    libXrandr \
    mesa-libgbm \
    alsa-lib
```

## Windows 特殊说明

在 Windows 上安装时，请注意以下几点：

1. **使用 PowerShell 或 Git Bash** 执行安装命令
2. 如果提示"命令不存在"，确保 Node.js 已正确安装并添加到 PATH
3. 可能需要以管理员身份运行终端

```powershell
# PowerShell 示例
npm install -g agent-browser
agent-browser install
```

## macOS 特殊说明

在 macOS 上，如果遇到权限问题：

```bash
# 如果 Homebrew 安装路径不在 PATH 中
export PATH="/opt/homebrew/bin:$PATH"  # Apple Silicon
# 或
export PATH="/usr/local/bin:$PATH"      # Intel

npm install -g agent-browser
agent-browser install
```

## 故障排除

### 命令未找到

```bash
# 检查 npm 全局路径
npm config get prefix

# 将全局路径添加到 PATH (示例)
export PATH="$PATH:$(npm config get prefix)/bin"

# 或永久添加到 shell 配置文件 (~/.zshrc 或 ~/.bashrc)
echo 'export PATH="$PATH:$(npm config get prefix)/bin"' >> ~/.zshrc
source ~/.zshrc
```

### Chromium 下载失败

如果网络问题导致 Chromium 下载失败，可以：

1. 使用代理
2. 手动下载 Chromium 并指定路径
3. 使用自定义浏览器可执行文件

```bash
# 使用自定义 Chrome/Chromium
AGENT_BROWSER_EXECUTABLE_PATH=/path/to/chrome agent-browser open example.com
```

### 权限错误

```bash
# Linux/macOS: 使用 sudo (不推荐，仅在必要时)
sudo npm install -g agent-browser --unsafe-perm=true
```

## 卸载

```bash
npm uninstall -g agent-browser
```

手动删除 Chromium 和配置数据：

```bash
# macOS/Linux
rm -rf ~/.agent-browser

# Windows
rmdir /s %USERPROFILE%\.agent-browser
```

## 更新

```bash
npm update -g agent-browser
```

## 下一步

安装完成后，请查看：
- [SKILL.md](../SKILL.md) - 核心工作流和命令列表
- [REPORT_GUIDE.md](./REPORT_GUIDE.md) - 测试报告格式规范

快速测试：

```bash
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser close
```

## 更多资源

- 官方文档: https://github.com/vercel-labs/agent-browser
- 官方网站: https://agent-browser.dev
- 问题反馈: https://github.com/vercel-labs/agent-browser/issues
