---
name: byd-vehicle-scrape
description: BYD 车型数据爬取与 SQL 转换技能。从 bydhaberfield.com.au 网站爬取车型配置和价格数据，生成 JSON 文件，再转换为 MySQL INSERT SQL 语句。 Use this skill when the user needs to scrape BYD vehicle data, wants to generate SQL for vehicle configurations, or mentions tasks like "爬取 Atto2 数据" or "生成车辆 SQL".
---

# BYD 车型数据爬取流程

## 概述

此技能用于从 BYD 澳大利亚官网爬取车型配置和价格数据，并将数据转换为 MySQL INSERT SQL 语句。适用于需要将 BYD 车辆数据导入数据库的场景。

> **⚠️ 重要：执行目录**
>
> **务必在用户当前工作目录下执行脚本命令，不要在 skill 安装目录下执行！**
>
> 脚本会将输出文件写入 `process.cwd()`（当前工作目录）。如果错误地在 skill 安装目录执行，输出文件会写入 skill 目录，导致：
> - 用户难以找到生成的文件
> - skill 升级时可能丢失数据
>
> **正确做法**：使用 `cd` 切换到用户工作目录后，再执行脚本命令。

## 工作流程

```
用户请求 → 爬取指定车型 → 生成 JSON 文件 → 转换为 SQL 文件 → 输出路径
```

## 支持的车型

| 车型 | 类型 | 车身类型 | 座位数 |
|------|------|----------|--------|
| Atto 1 | Electric | Hatchback | 5 |
| Atto 2 | Electric | SUV | 5 |
| Atto 3 | Electric | SUV | 5 |
| Dolphin | Electric | Hatchback | 5 |
| Seal | Electric | Sedan | 5 |
| M6 | Electric | Sedan | 5 |
| Shark | Electric | Sedan | 5 |

## Step 1: 爬取车型数据

### 用法

> **执行前确认**：确保当前目录是用户工作目录（运行 `pwd` 确认），输出将写入 `./byd-output/json/`

```bash
# 爬取单个车型（在用户工作目录下执行）
node ~/.claude/skills/byd-vehicle-scrape/scripts/scrape-byd-variant-details.js --model="Atto 2"

# 爬取多个车型（逗号分隔）
node ~/.claude/skills/byd-vehicle-scrape/scripts/scrape-byd-variant-details.js --model="Atto 2,Atto 3"

# 爬取所有车型
node ~/.claude/skills/byd-vehicle-scrape/scripts/scrape-byd-variant-details.js
```

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | 全部 | 指定车型名称，多个用逗号分隔 |
| `--delay` | 500 | 请求间延迟 (ms) |
| `--retries` | 3 | 失败重试次数 |
| `--timeout` | 60000 | 页面加载超时 (ms) |
| `--help` | - | 显示帮助信息 |

### 输出

JSON 文件保存到**用户工作目录**下的 `byd-output/json/` 目录，命名格式：
- 单车型: `byd-variant-details_{车型名}_{时间戳}.json`
- 多车型: `byd-variant-details_{车型数}models_{时间戳}.json`
- 全部: `byd-variant-details_all_{时间戳}.json`

## Step 2: 生成 SQL 语句

### 用法

> **执行前确认**：确保当前目录是用户工作目录，且已存在 `./byd-output/json/` 目录

```bash
# 使用默认文件（最新的 JSON 文件）
node ~/.claude/skills/byd-vehicle-scrape/scripts/generate_sql.mjs

# 指定输入文件
node ~/.claude/skills/byd-vehicle-scrape/scripts/generate_sql.mjs byd-variant-details_atto-2_2026-03-13_10-30-00.json
```

### 输出

SQL 文件保存到**用户工作目录**下的 `byd-output/sql/` 目录，命名格式：
`insert_statements_{车型标识}_{时间戳}.sql`

### 生成的 SQL 内容

SQL 文件包含：
- `START TRANSACTION` / `COMMIT` 事务包装
- `loan_vehicle_configs` 表的 INSERT 语句（车型配置信息）
- `loan_vehicle_prices` 表的 INSERT 语句（所有价格组合）

## 完整示例：爬取 Atto 2 并生成 SQL

```bash
# 确保在用户工作目录下执行（例如：/Users/sen/projects/my-project）
pwd  # 确认当前目录

# 1. 爬取 Atto 2 车型数据（输出到 ./byd-output/json/）
node ~/.claude/skills/byd-vehicle-scrape/scripts/scrape-byd-variant-details.js --model="Atto 2"

# 2. 生成 SQL（使用刚刚生成的 JSON 文件，输出到 ./byd-output/sql/）
node ~/.claude/skills/byd-vehicle-scrape/scripts/generate_sql.mjs byd-variant-details_atto-2_2026-03-13_10-30-00.json

# 3. 查看输出文件
ls -la ./byd-output/json/
ls -la ./byd-output/sql/
```

## 脚本资源

### scripts/scrape-byd-variant-details.js
Playwright 爬虫脚本，负责：
- 使用无头浏览器访问 BYD 配置页面
- 提取车型变体、颜色、轮毂、内饰、配件信息
- 计算所有价格组合（含政府费用、促销优惠）
- 输出结构化 JSON 数据

### scripts/generate_sql.mjs
SQL 生成脚本，负责：
- 读取爬取的 JSON 文件
- 生成 `loan_vehicle_configs` 表的 INSERT 语句
- 生成 `loan_vehicle_prices` 表的 INSERT 语句（批量插入）
- 自动推断品牌、格式化日期、转义 SQL 字符串

## 数据库表结构参考

### loan_vehicle_configs
存储车型配置汇总信息，包括车型名称、类型、座位数、变体数量、颜色/轮毂/内饰选项、价格范围等。

### loan_vehicle_prices
存储每个价格组合的详细信息，包括变体、颜色、轮毂、内饰的价格，以及印花税、上牌费、交强险、经销商交车费、促销优惠等。

## 注意事项

1. **执行目录（最重要）**: 脚本**必须在用户工作目录下执行**，输出文件会写入当前工作目录的 `byd-output/` 子目录。执行前请确认 `pwd` 返回的是用户期望的工作目录。
2. **Playwright 依赖**: 爬虫脚本需要安装 Playwright，首次使用需运行 `npx playwright install chromium`
3. **网络要求**: 需要能够访问 bydhaberfield.com.au 网站
4. **爬取时间**: 完整爬取所有车型约需 10-30 分钟，取决于网络状况
5. **SQL 执行**: 生成的 SQL 文件可直接在 MySQL 中执行，会自动开启事务保证数据一致性
