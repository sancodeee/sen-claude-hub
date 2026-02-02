import subprocess
import argparse
import os
import datetime
import sys
import time

# ================== 路径计算（解决相对路径问题） ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # scripts/ 目录
SKILL_DIR = os.path.dirname(SCRIPT_DIR)                           # agent-browser-integration-testing/

# 查找项目根目录（向上查找包含 .git 或 package.json 的目录）
def find_project_root(start_dir):
    current = start_dir
    for _ in range(5):  # 最多向上查找5层
        if os.path.exists(os.path.join(current, '.git')) or os.path.exists(os.path.join(current, 'package.json')):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # 到达根目录
            break
        current = parent
    return start_dir  # 找不到则返回起始目录

PROJECT_ROOT = find_project_root(SKILL_DIR)
TEMPLATE_PATH = os.path.join(SKILL_DIR, 'references', 'test_report_template.md')
REPORT_DIR = os.path.join(PROJECT_ROOT, 'testing-report')

os.makedirs(REPORT_DIR, exist_ok=True)

# ================== agent-browser 命令前缀 ==================
AGENT_BROWSER_CMD = ['agent-browser']

# ================== 检查 agent-browser 是否可用 ==================
def check_agent_browser_exists():
    try:
        result = subprocess.run(AGENT_BROWSER_CMD + ['--version'], capture_output=True, text=True, check=True)
        print(f"[INFO] agent-browser 版本：{result.stdout.strip()}")
    except Exception as e:
        print(f"[CRITICAL] agent-browser 未找到或不可用：{str(e)}")
        print("请安装：npm install -g @vercel-labs/agent-browser （或确认 PATH）")
        sys.exit(1)

check_agent_browser_exists()

# ================== 执行 agent-browser 命令（带重试） ==================
def run_agent_browser(args_list, timeout=60, retries=2):
    full_cmd = AGENT_BROWSER_CMD + args_list
    cmd_str = ' '.join(full_cmd)
    print(f"[EXEC] {cmd_str}")

    for attempt in range(retries + 1):
        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout, check=True)
            output = result.stdout.strip()
            print(f"[OK] {output[:200]}{'...' if len(output) > 200 else ''}")
            return output, True
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] 第 {attempt+1} 次尝试超时 ({timeout}s)")
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] 返回码 {e.returncode} | Stderr: {e.stderr.strip()[:200]}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")

        if attempt < retries:
            time.sleep(3)  # 等待重试
    return f"执行失败（尝试 {retries+1} 次）：{cmd_str}", False

# ================== 清空输入框（解决 type 追加问题） ==================
def clear_input(ref):
    js = f'document.querySelector("{ref}").value = "";'
    run_agent_browser(['eval', js])

# ================== 执行测试（分步调用真实语法） ==================
def perform_tests(url, operation):
    results = {}
    executed_commands = []
    ops = [operation.lower()] if operation.lower() != 'all' else ['create', 'read', 'update', 'delete']

    # 打开页面（所有操作共用）
    output, success = run_agent_browser(['open', url, '--wait'])
    executed_commands.append(f"open {url} --wait")
    if not success:
        return {}, [], executed_commands  # 页面打不开，直接结束

    for op in ops:
        status = 'Fail'
        details = ''
        op_commands = []

        if op == 'create':
            # 示例：假设页面有“新增”按钮和表单
            _, s1 = run_agent_browser(['click', '#add-button']); op_commands.append("click #add-button")
            clear_input('input[name="name"]')
            _, s2 = run_agent_browser(['type', 'input[name="name"]', 'Test Create']); op_commands.append("type input[name=\"name\"] Test Create")
            _, s3 = run_agent_browser(['press', 'Enter']); op_commands.append("press Enter")
            output, s4 = run_agent_browser(['snapshot'])  # 验证用快照
            status = 'Pass' if s1[1] and s2[1] and s3[1] and 'success' in output.lower() else 'Fail'
            details = output

        elif op == 'read':
            output, success = run_agent_browser(['eval', 'document.querySelector(".loan-result")?.textContent || ""'])
            status = 'Pass' if success and output.strip() else 'Fail'
            details = f"提取结果：{output}"

        elif op == 'update':
            _, s1 = run_agent_browser(['click', '#edit-btn']); op_commands.append("click #edit-btn")
            clear_input('input[name="amount"]')
            _, s2 = run_agent_browser(['type', 'input[name="amount"]', '200000']); op_commands.append("type ... 200000")
            _, s3 = run_agent_browser(['press', 'Enter']); op_commands.append("press Enter")
            status = 'Pass' if s1[1] and s2[1] and s3[1] else 'Fail'

        elif op == 'delete':
            _, s1 = run_agent_browser(['click', '#delete-btn']); op_commands.append("click #delete-btn")
            _, s2 = run_agent_browser(['press', 'Enter']); op_commands.append("press Enter")
            status = 'Pass' if s1[1] and s2[1] else 'Fail'

        results[op] = {'status': status, 'details': details, 'commands': op_commands}
        executed_commands.extend(op_commands)

    # 跳转检测
    jumps_output, _ = run_agent_browser(['eval', 'Array.from(document.querySelectorAll("a[href]")).map(a => a.href).join("\\n")'])
    jumps = [line.strip() for line in jumps_output.split('\n') if line.strip().startswith('http')][:3]

    return results, jumps, executed_commands

# ================== 生成报告 ==================
def generate_report(results, url, operation, jumps, executed_commands):
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] 模板文件缺失：{TEMPLATE_PATH}")
        return "报告模板文件不存在，无法生成报告。", None

    module_sections = ''
    total = len(results)
    passed = sum(1 for v in results.values() if v['status'] == 'Pass')
    failed = total - passed

    for op, data in results.items():
        module_sections += f"### {op.upper()} ({get_op_description(op)})\n"
        module_sections += f"- 状态：**{data['status']}**\n"
        module_sections += "- 执行命令：\n" + "\n".join(f"  - agent-browser {c}" for c in data['commands']) + "\n"
        module_sections += f"- 详情：{data['details'][:600]}{'...' if len(data['details']) > 600 else ''}\n\n"

    jumps_text = ""
    if jumps:
        jumps_text = "## 检测到跳转链接（需确认是否继续）\n" + "\n".join(f"- {u}" for u in jumps) + "\n"

    commands_text = "## 所有执行命令\n```bash\n" + "\n".join(executed_commands) + "\n```"

    # 先确定报告文件路径
    url_slug = "".join(c for c in url if c.isalnum() or c in '-_.')[:40]
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"test-{url_slug}-{ts}.md"
    path = os.path.join(REPORT_DIR, filename)
    report_path_display = os.path.abspath(path)

    report = template \
        .replace('{{URL}}', url) \
        .replace('{{OPERATIONS}}', operation.upper()) \
        .replace('{{DATE}}', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) \
        .replace('{{STATUS}}', '全部通过' if failed == 0 else f'失败 {failed}/{total}') \
        .replace('{{MODULE_SECTIONS}}', module_sections + jumps_text + commands_text) \
        .replace('{{TOTAL}}', str(total)) \
        .replace('{{PASSED}}', str(passed)) \
        .replace('{{FAILED}}', str(failed)) \
        .replace('{{REPORT_PATH}}', report_path_display)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[SAVE] 报告保存至：{path}")
    return report, path

def get_op_description(op):
    return {
        'create': '创建/新增',
        'read': '查询/读取',
        'update': '更新/修改',
        'delete': '删除'
    }.get(op, op)

# ================== 主程序 ==================
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--operation', default='all')
    args = parser.parse_args()

    print(f"[START] URL: {args.url} | 操作: {args.operation.upper()}")
    results, jumps, commands = perform_tests(args.url, args.operation)
    report, path = generate_report(results, args.url, args.operation, jumps, commands)

    if path:
        print(f"[DONE] 报告路径：{os.path.abspath(path)}")
        print("\n预览（前800字符）：")
        print(report[:800] + "..." if len(report) > 800 else report)
    else:
        print("[DONE] 未生成报告文件（模板缺失）")