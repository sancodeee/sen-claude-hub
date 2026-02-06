# agent-browser 下拉框操作指南

> 本文档提供使用 agent-browser 处理网页下拉框的完整指南，区分原生下拉框和自定义下拉框组件的操作方法。

---

## 目录

1. [类型识别](#1-类型识别)
2. [原生下拉框操作](#2-原生下拉框操作)
3. [自定义下拉框操作](#3-自定义下拉框操作)
4. [命令对比与选择](#4-命令对比与选择)
5. [验证选中状态](#5-验证选中状态)
6. [完整示例脚本](#6-完整示例脚本)
7. [故障排查](#7-故障排查)

---

## 1. 类型识别

### 1.1 原生下拉框 (Native Select)

**特征：**
- HTML 元素为 `<select>` 和 `<option>`
- 在可访问性树 (a11y tree) 中可见
- snapshot 输出显示 `combobox` 和 `option`

**识别命令：**
```bash
agent-browser snapshot -i
# 输出示例：
# - combobox [ref=e8]
#   - option "Select State" [ref=e9] [selected]
#   - option "NSW" [ref=e10]
#   - option "VIC" [ref=e11]
```

### 1.2 自定义下拉框组件 (Custom Dropdown)

**特征：**
- 使用 `<div>`、`<span>` 等通用元素构建
- CSS Module 生成复杂类名（如 `dealerDropdownTrigger___PmdMH`）
- 下拉菜单初始状态可能隐藏
- snapshot 可能只显示触发器，不显示选项

**识别命令：**
```bash
# 查找 dropdown 相关的 class
agent-browser eval "document.querySelectorAll('[class*=\"dropdown\" i]').length"

# 检查特定元素是否存在
agent-browser eval "document.querySelector('.dealerDropdownTrigger___PmdMH') !== null"
```

---

## 2. 原生下拉框操作

### 2.1 操作步骤

```bash
# 步骤1：获取元素引用
agent-browser snapshot -i

# 步骤2：使用 select 命令选择选项
agent-browser select @e8 "NSW"

# 步骤3：验证选中
agent-browser get value @e8
```

### 2.2 核心命令

| 命令 | 说明 |
|------|------|
| `agent-browser select @e8 "NSW"` | 选择下拉框选项 |
| `agent-browser get value @e8` | 获取当前选中值 |

### 2.3 重要提示

```
不要直接点击 option 元素！
❌ agent-browser click @e10  <- 这会失败
✅ agent-browser select @e8 "NSW"  <- 正确做法
```

---

## 3. 自定义下拉框操作

### 3.1 核心原理

自定义下拉框需要**两步操作**：

```
步骤1：点击触发器 → 展开下拉菜单
步骤2：点击选项 → 完成选择
```

### 3.2 通用操作模板

```bash
# 步骤1：展开下拉框
agent-browser eval "document.querySelector('触发器选择器').click()"

# 步骤2：等待菜单展开（推荐）
agent-browser wait 500

# 步骤3：点击选项
agent-browser eval "document.querySelector('选项选择器').click()"
```

### 3.3 实际案例：Service Center 下拉框

```bash
# 完整操作流程
agent-browser eval "document.querySelector('.dealerDropdownTrigger___PmdMH').click()"
agent-browser wait 500
agent-browser eval "document.querySelector('.dealerDropdownItem___V_zGB').click()"
```

### 3.4 查找选择器的方法

```bash
# 查找包含特定文本的元素
agent-browser eval "Array.from(document.querySelectorAll('*')).find(el => el.textContent.includes('Service Center'))"

# 查找特定 class 模式
agent-browser eval "document.querySelectorAll('[class*=\"dropdown\"]')"

# 获取所有选项列表
agent-browser eval "Array.from(document.querySelectorAll('.dealerDropdownItemName___ZCEoM')).map(el => el.textContent)"
```

---

## 4. 命令对比与选择

### 4.1 命令对比表

| 命令 | 工作方式 | 需要snapshot | 适用场景 |
|------|----------|--------------|----------|
| `click @ref` | 通过ref点击 | 是 | 标准可访问元素 |
| `find ... click` | 语义定位 | 否 | 有清晰文本/role/label |
| `select @ref "value"` | 原生select专用 | 是 | 原生`<select>`元素 |
| `eval "js"` | 执行JavaScript | 否 | 自定义组件/复杂逻辑 |

### 4.2 为什么有时必须用 eval？

| 原因 | 说明 |
|------|------|
| 选项隐藏 | 自定义下拉框选项初始不在可访问性树中 |
| 无法获取ref | snapshot 无法获取隐藏元素的引用 |
| 缺少ARIA属性 | find 命令依赖可访问性属性，自定义组件可能缺失 |
| 绕过限制 | eval 直接访问完整 DOM，无上述限制 |

### 4.3 决策流程

```
需要操作下拉框
       │
       ▼
  执行 snapshot -i
       │
       ▼
  能看到 option 元素吗？
  ┌────┴────┐
  │         │
 YES        NO
  │         │
  ▼         ▼
原生下拉框  自定义下拉框
  │         │
  ▼         ▼
select 命令  eval 命令
```

---

## 5. 验证选中状态

### 5.1 原生下拉框验证

```bash
# 方法1：获取值
agent-browser get value @e8

# 方法2：重新 snapshot
agent-browser snapshot -i

# 方法3：JS 验证
agent-browser eval "document.querySelector('select').value"
agent-browser eval "document.querySelector('select').selectedIndex"
```

### 5.2 自定义下拉框验证

```bash
# 检查显示文本
agent-browser eval "document.querySelector('.dealerDropdownText___lBn04').textContent"

# 检查错误状态是否消除
agent-browser eval "document.querySelector('.dealerDropdownTrigger___PmdMH').classList.contains('inputError___aJO0i')"
# 返回 false 表示无错误
```

---

## 6. 完整示例脚本

### 6.1 原生下拉框脚本

```bash
#!/bin/bash
# 选择 State 为 NSW

agent-browser snapshot -i
agent-browser select @e8 "NSW"

# 验证（使用 --json 获取机器可读输出）
selected=$(agent-browser get value @e8 --json)
echo "选中值: $selected"

# 或者直接获取输出（不需要 --json 时）
agent-browser get value @e8
```

### 6.2 自定义下拉框脚本

```bash
#!/bin/bash
# 选择 Service Center

select_service_center() {
    local dealer_name="$1"

    # 1. 打开下拉框
    agent-browser eval "document.querySelector('.dealerDropdownTrigger___PmdMH').click()"
    sleep 0.5

    # 2. 点击选项
    agent-browser eval "
        Array.from(document.querySelectorAll('.dealerDropdownItemName___ZCEoM'))
            .find(el => el.textContent === '$dealer_name')
            .closest('.dealerDropdownItem___V_zGB')
            .click()
    "
    sleep 0.5

    # 3. 验证
    local selected=$(agent-browser eval "document.querySelector('.dealerDropdownText___lBn04').textContent")
    echo "已选中: $selected"

    if [ "$selected" = "$dealer_name" ]; then
        echo "✓ 选中成功"
        return 0
    else
        echo "✗ 选中失败"
        return 1
    fi
}

# 使用
select_service_center "Dealer-BYD-1"
```

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| 点击无反应 | 元素被遮挡 | 先滚动到元素 `scrollintoview @e1` |
| 选项找不到 | 菜单未展开 | 先点击触发器，等待菜单出现 |
| 选择后立即恢复 | 页面有验证逻辑 | 检查关联字段是否需要填写 |
| snapshot 看不到元素 | 元素隐藏或动态加载 | 使用 `wait` 或直接用 `eval` 查找 |
| Ref not found 错误 | 页面变化后 ref 失效 | 重新执行 `snapshot -i` 获取新 ref |

### 7.2 调试命令

```bash
# 检查元素是否存在
agent-browser eval "document.querySelector('.selector') !== null"

# 检查元素可见性（使用 is visible 命令）
agent-browser is visible @e1

# 或使用 JS 检查计算样式
agent-browser eval "window.getComputedStyle(document.querySelector('.selector')).display"

# 查看元素完整HTML
agent-browser eval "document.querySelector('.selector').outerHTML"

# 查看所有select元素
agent-browser eval "Array.from(document.querySelectorAll('select')).map((s,i) => \`[\${i}] \${s.value}\`)"

# 截图查看当前状态
agent-browser screenshot /tmp/debug.png

# 获取元素文本
agent-browser get text @e1
```

---

## 8. 快速参考

### 原生下拉框

```bash
agent-browser snapshot -i
agent-browser select @e8 "NSW"
agent-browser get value @e8
```

### 自定义下拉框

```bash
# 展开 → 选择 → 验证
agent-browser eval "document.querySelector('.trigger').click()"
agent-browser wait 500
agent-browser eval "document.querySelector('.option').click()"
agent-browser eval "document.querySelector('.display').textContent"
```

### 选择器查找

```bash
# 查找所有select
agent-browser eval "document.querySelectorAll('select')"

# 查找dropdown相关类
agent-browser eval "document.querySelectorAll('[class*=\"dropdown\"]')"

# 查找包含特定文本的元素
agent-browser eval "Array.from(document.querySelectorAll('*')).find(el => el.textContent.includes('目标文本'))"
```

---

## 9. 最佳实践

### 优先级顺序

```
1. select 命令    → 原生下拉框首选
2. find 命令      → 语义化，易维护
3. click @ref     → 简单直接
4. eval 命令      → 最灵活，但可读性较低
```

### 代码可读性建议

```bash
# 推荐：使用变量存储选择器
TRIGGER_SELECTOR=".dealerDropdownTrigger___PmdMH"
ITEM_SELECTOR=".dealerDropdownItem___V_zGB"
DEALER_NAME="Dealer-BYD-1"

agent-browser eval "document.querySelector('$TRIGGER_SELECTOR').click()"
agent-browser wait 500
agent-browser eval "document.querySelector('$ITEM_SELECTOR').click()"
```

---

## 10. 命令校验说明

本文档中使用的命令均已根据 agent-browser 官方文档（SKILL.md 和 snapshot-refs.md）进行校验。

### 已校验的核心命令

| 命令类别 | 官方语法 | 文档中使用 | 状态 |
|----------|----------|------------|------|
| Snapshot | `snapshot -i` | `snapshot -i` | ✓ |
| Select | `select @e1 "value"` | `select @e8 "NSW"` | ✓ |
| Click | `click @e1` | `click @e10` | ✓ |
| Fill | `fill @e2 "text"` | `fill @e3 "text"` | ✓ |
| Eval | `eval "js代码"` | `eval "document.querySelector...click()"` | ✓ |
| Wait | `wait 2000` | `wait 500` | ✓ |
| Get value | `get value @e1` | `get value @e8` | ✓ |
| Screenshot | `screenshot path.png` | `screenshot /tmp/debug.png` | ✓ |
| Find | `find text "X" click` | `find text "X" click` | ✓ |
| Is visible | `is visible @e1` | `is visible @e1` | ✓ |
| Scroll to view | `scrollintoview @e1` | `scrollintoview @e1` | ✓ |

### 官方文档参考

```bash
# 查看官方帮助
agent-browser --help
agent-browser <command> --help

# 核心命令速查
agent-browser snapshot -i       # 获取交互元素
agent-browser select @e1 "val"  # 选择下拉选项
agent-browser click @e1         # 点击元素
agent-browser fill @e1 "text"   # 填写输入
agent-browser eval "js"         # 执行JavaScript
agent-browser find text "X" click  # 语义定位点击
```
