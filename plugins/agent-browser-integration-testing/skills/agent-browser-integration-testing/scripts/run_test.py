import subprocess
import argparse
import os
import datetime
import sys

# ================== 路径配置 ==================
TEMPLATE_PATH = '../references/test_report_template.md'  # 相对 Skill 目录的模板路径
REPORT_DIR = 'testing-report'  # 项目根目录下的报告文件夹
os.makedirs(REPORT_DIR, exist_ok=True)  # 自动创建如果不存在

# ================== 强制检查 agent-browser 是否可用 ==================
def check_agent_browser_exists():
    """启动时检查 agent-browser CLI 是否存在于 PATH 中"""
    try:
        result = subprocess.run(['agent-browser', '--version'], capture_output=True, text=True, check=True)
        print(f"[INFO] agent-browser 版本：{result.stdout.strip()}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        error_msg = """
【CRITICAL ERROR】agent-browser 命令未找到或执行失败。
此 Skill 要求 agent-browser CLI 已安装并在 PATH 中。
请安装（示例命令）：
  npm install -g @vercel-labs/agent-browser
或参考官方文档：https://github.com/vercel-labs/agent-browser
"""
        print(error_msg)
        sys.exit(1)  # 立即退出，防止无工具继续

check_agent_browser_exists()  # 脚本启动即检查

# ================== agent-browser 调用函数 ==================
def run_agent_browser(command: str) -> str:
    """
    使用 subprocess 调用 agent-browser CLI，并记录详细日志。
    假设 agent-browser 支持类似 puppeteer 的命令（如 open, click, type 等）。
    """
    full_cmd = ['agent-browser'] + command.split()
    cmd_str = ' '.join(full_cmd)
    print(f"[EXEC] 执行命令：{cmd_str}")

    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        print(f"[OUTPUT] 输出（前200字符）：{output[:200]}{'...' if len(output) > 200 else ''}")
        return output
    except subprocess.CalledProcessError as e:
        err = f"agent-browser 执行失败：\n  命令：{cmd_str}\n  Stderr：{e.stderr.strip()}\n  Stdout：{e.stdout.strip()}"
        print(err)
        return err
    except Exception as e:
        err = f"调用 agent-browser 意外错误：{str(e)}"
        print(err)
        return err

# ================== 执行测试函数 ==================
def perform_tests(url: str, operation: str):
    """
    使用 agent-browser 执行集成测试。
    支持 CRUD 操作，并记录所有命令。
    业务模块分组：基于操作类型简单分组（可扩展为页面解析）。
    跳转检测：使用 agent-browser 提取链接。
    """
    results = {}
    ops = [operation.lower()] if operation.lower() != 'all' else ['create', 'read', 'update', 'delete']
    executed_commands = []  # 记录所有执行的 agent-browser 命令

    for op in ops:
        # 占位命令：必须根据实际 agent-browser 语法替换！
        # 假设语法：agent-browser open <url> --action <op> --verify
        # 请查阅 agent-browser --help 或文档，替换为真实命令
        if op == 'create':
            cmd = f"open {url} --wait --click '#add-button' --type 'input[name=\"data\"]' 'test value' --submit 'form' --verify 'success'"
        elif op == 'read':
            cmd = f"open {url} --wait --extract '.result-data' --verify 'contains expected'"
        elif op == 'update':
            cmd = f"open {url} --wait --click '#edit-button' --type 'input[name=\"edit\"]' 'new value' --submit --verify 'updated'"
        elif op == 'delete':
            cmd = f"open {url} --wait --click '#delete-button' --confirm --verify 'removed'"
        else:
            cmd = f"open {url} --wait --perform {op} --verify"

        executed_commands.append(cmd)
        result = run_agent_browser(cmd)
        status = 'Pass' if any(word in result.lower() for word in ['success', 'verified', 'ok']) else 'Fail'
        results[op] = {'status': status, 'details': result, 'command': cmd}

    # 跳转页面检测
    jumps_cmd = f"open {url} --wait --extract-links --filter 'button, a[href]'"
    executed_commands.append(jumps_cmd)
    jumps_output = run_agent_browser(jumps_cmd)
    jumps = []  # 解析输出为 URL 列表
    # 占位解析：假设输出是换行 URL，实际需调整
    lines = jumps_output.split('\n')
    jumps = [line.strip() for line in lines if line.strip().startswith('http')][:5]  # 取前5个避免过多

    if jumps:
        print(f"检测到跳转页面：{', '.join(jumps)}")
        print("【用户询问】是否继续测试这些跳转页面？（是/否）")
        # 在 Claude 对话中，这里会暂停等待用户响应；脚本不实现递归

    # 业务模块分组（示例：基于操作类型）
    modules = {
        '新增/修改/删除模块': {k: v for k, v in results.items() if k in ['create', 'update', 'delete']},
        '查询模块': {k: v for k, v in results.items() if k == 'read'}
    } if len(ops) > 1 else {'核心模块': results}

    return modules, jumps, executed_commands

# ================== 生成报告函数 ==================
def generate_report(modules, url, operation, jumps, executed_commands):
    """
    使用固定模板生成报告，包含模块结果、跳转、命令列表。
    保存到 testing-report 目录，返回内容和路径。
    """
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print("[ERROR] 模板文件缺失：{TEMPLATE_PATH}")
        return "报告模板缺失，无法生成报告。", None

    module_sections = ''
    total_tests = 0
    passed = 0
    failed = 0

    for module, res in modules.items():
        module_sections += f"## {module}\n\n"
        for op, data in res.items():
            total_tests += 1
            if data['status'] == 'Pass':
                passed += 1
            else:
                failed += 1
            module_sections += f"- **操作**：{op.upper()} ({get_op_description(op)})\n"
            module_sections += f"  - **状态**：{data['status']}\n"
            module_sections += f"  - **执行命令**：`agent-browser {data['command']}`\n"
            module_sections += f"  - **详情**：{data['details'][:500]}{'...' if len(data['details']) > 500 else ''}\n\n"

    jumps_section = '\n## 检测到的跳转页面\n' if jumps else ''
    if jumps:
        jumps_section += '以下页面可能需要进一步测试（已询问用户）：\n' + '\n'.join(f"- {jump}" for jump in jumps) + '\n'

    commands_section = '\n## 执行的 agent-browser 命令列表\n```\n' + '\n'.join(executed_commands) + '\n```'

    overall_status = '全部通过' if failed == 0 else f'部分失败（{failed} 个失败项）'

    report_content = template.replace('{{URL}}', url) \
        .replace('{{OPERATIONS}}', operation.upper()) \
        .replace('{{DATE}}', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) \
        .replace('{{STATUS}}', overall_status) \
        .replace('{{MODULE_SECTIONS}}', module_sections + jumps_section + commands_section) \
        .replace('{{TOTAL}}', str(total_tests)) \
        .replace('{{PASSED}}', str(passed)) \
        .replace('{{FAILED}}', str(failed))

    # 文件名：URL slug + 时间戳
    url_slug = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_')[:50]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"test-report-{url_slug}-{timestamp}.md"
    output_path = os.path.join(REPORT_DIR, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return report_content, output_path

# ================== 操作描述辅助 ==================
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
    parser = argparse.ArgumentParser(description="浏览器集成测试脚本：强制使用 agent-browser CLI 执行 CRUD 测试并生成报告。")
    parser.add_argument('--url', required=True, help="要测试的 URL，例如 https://example.com")
    parser.add_argument('--operation', default='all', help="操作类型：create/read/update/delete/all")
    args = parser.parse_args()

    print(f"[START] 测试 URL：{args.url}  操作：{args.operation.upper()}")
    modules, jumps, executed_commands = perform_tests(args.url, args.operation)
    report_content, report_path = generate_report(modules, args.url, args.operation, jumps, executed_commands)

    print(f"[DONE] 测试报告已生成并保存到：{os.path.abspath(report_path)}")
    print("\n报告内容预览（前 1000 字符）：")
    print(report_content[:1000] + "..." if len(report_content) > 1000 else report_content)