import subprocess
import argparse
import os
import datetime
import json  # 可选，用于潜在的配置加载，如果 assets/config.json 有用

# ================== 路径配置 ==================
# 模板路径（相对 Skill 目录）
TEMPLATE_PATH = '../references/test_report_template.md'

# 报告输出目录（当前项目根目录下的 testing-report）
REPORT_DIR = 'testing-report'
os.makedirs(REPORT_DIR, exist_ok=True)  # 自动创建目录如果不存在

# ================== agent-browser 调用包装 ==================
def run_agent_browser(command):
    """
    使用 subprocess 调用 agent-browser CLI 命令。
    假设 agent-browser 是已安装的命令行工具。
    如果是 Python 库，可改为 import 并调用。
    """
    try:
        result = subprocess.run(['agent-browser'] + command.split(), capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing agent-browser: {e.stderr.strip()}"
    except FileNotFoundError:
        return "Error: agent-browser command not found. Please install it."

# ================== 执行测试 ==================
def perform_tests(url, operation):
    """
    使用 agent-browser 执行浏览器集成测试。
    支持 CRUD 操作：create/read/update/delete/all。
    优先使用 agent-browser，避免重型工具。
    返回按业务模块分组的结果（当前占位逻辑，可扩展为页面解析）。
    """
    results = {}
    ops = [operation.lower()] if operation.lower() != 'all' else ['create', 'read', 'update', 'delete']

    for op in ops:
        # 根据操作生成 agent-browser 命令（占位：需根据实际 agent-browser 语法调整）
        # 示例假设 agent-browser 支持 "navigate <url> <action> <params>"
        if op == 'create':
            cmd = f"navigate {url} click add-button fill form submit verify success"
        elif op == 'read':
            cmd = f"navigate {url} query api-endpoint extract data verify response"
        elif op == 'update':
            cmd = f"navigate {url} select item edit fill form submit verify updated"
        elif op == 'delete':
            cmd = f"navigate {url} select item delete confirm verify removed"
        else:
            cmd = f"navigate {url} perform {op} verify"

        result = run_agent_browser(cmd)
        status = 'Pass' if 'success' in result.lower() or 'verified' in result.lower() else 'Fail'
        results[op] = {'status': status, 'details': result}

    # 占位：检测跳转页面（从 agent-browser 输出中解析链接/按钮）
    # 实际中，可运行 "navigate {url} extract links buttons" 获取
    jumps_cmd = f"navigate {url} extract jumps"
    jumps_output = run_agent_browser(jumps_cmd)
    jumps = []  # 解析 jumps_output 为列表，例如 ['https://subpage.com']
    # 示例模拟
    if 'link' in jumps_output.lower():
        jumps = ['https://example.com/subpage']  # 替换为实际解析

    if jumps:
        # 在 Claude 环境中，通过对话提示用户
        print(f"检测到跳转页面：{', '.join(jumps)}")
        print("询问用户：是否继续测试这些跳转页面？（是/否）")
        # 实际逻辑：如果用户确认，可递归调用 perform_tests(new_url, operation)
        # 这里占位，不实现递归以避免无限循环

    # 占位：业务模块分组（从页面结构推断，例如通过 headings 或 URL 路径）
    # 实际可运行 "navigate {url} extract modules" 获取
    modules = {
        '用户管理模块': {k: v for k, v in results.items() if k in ['create', 'update', 'delete']},
        '查询模块': {k: v for k, v in results.items() if k == 'read'}
    } if len(ops) > 1 else {'核心模块': results}

    return modules, jumps

# ================== 生成报告 ==================
def generate_report(modules, url, operation, jumps):
    """
    使用固定模板生成报告。
    填充模块结果、统计、跳转信息。
    保存到 testing-report 目录，返回内容和路径。
    """
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    module_sections = ''
    total_tests = 0
    passed = 0
    failed = 0

    for module, results in modules.items():
        module_sections += f"## {module}\n\n"
        for op, res in results.items():
            total_tests += 1
            if res['status'] == 'Pass':
                passed += 1
            else:
                failed += 1
            module_sections += f"- **操作**：{op.upper()}（{get_op_description(op)}）\n"
            module_sections += f"  - **状态**：{res['status']}\n"
            module_sections += f"  - **详情**：{res['details'][:500]}{'...' if len(res['details']) > 500 else ''}\n\n"

    jumps_section = '\n## 检测到的跳转页面\n' if jumps else ''
    if jumps:
        jumps_section += '以下页面可能需要进一步测试（已询问用户）：\n'
        for jump in jumps:
            jumps_section += f"- {jump}\n"

    # 整体状态
    overall_status = '全部通过' if failed == 0 else f'部分失败（{failed} 个失败项）'

    # 替换模板占位符
    report_content = template.replace('{{URL}}', url)
    report_content = report_content.replace('{{OPERATIONS}}', operation.upper())
    report_content = report_content.replace('{{DATE}}', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_content = report_content.replace('{{STATUS}}', overall_status)
    report_content = report_content.replace('{{MODULE_SECTIONS}}', module_sections + jumps_section)
    report_content = report_content.replace('{{TOTAL}}', str(total_tests))
    report_content = report_content.replace('{{PASSED}}', str(passed))
    report_content = report_content.replace('{{FAILED}}', str(failed))

    # 生成文件名：包含 URL 简写 + 时间戳
    url_slug = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"test-report-{url_slug}-{timestamp}.md"
    output_path = os.path.join(REPORT_DIR, output_filename)

    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return report_content, output_path

# ================== 操作描述辅助函数 ==================
def get_op_description(op):
    """返回 CRUD 操作的中文描述"""
    descriptions = {
        'create': '创建/新增 API 或页面功能',
        'read': '查询/读取 API 或页面功能',
        'update': '更新/修改 API 或页面功能',
        'delete': '删除 API 或页面功能'
    }
    return descriptions.get(op, '未知操作')

# ================== 主入口 ==================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="浏览器集成测试脚本，使用 agent-browser 执行 CRUD 测试并生成报告。")
    parser.add_argument('--url', required=True, help="要测试的 URL")
    parser.add_argument('--operation', default='all', help="操作类型：create/read/update/delete/all")
    args = parser.parse_args()

    modules, jumps = perform_tests(args.url, args.operation)
    report_content, report_path = generate_report(modules, args.url, args.operation, jumps)

    print(f"测试报告已生成并保存到：{report_path}")
    print("\n报告内容预览（前 1000 字符）：")
    print(report_content[:1000] + "..." if len(report_content) > 1000 else report_content)