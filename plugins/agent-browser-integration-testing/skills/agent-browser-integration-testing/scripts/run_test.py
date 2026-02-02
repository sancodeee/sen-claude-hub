import subprocess
import argparse
import os
import datetime
import sys
import time
import json
import re

# ================== 配置与路径 ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))) 

def find_project_root(start_dir):
    current = start_dir
    for _ in range(5):
        if os.path.exists(os.path.join(current, '.git')) or os.path.exists(os.path.join(current, 'package.json')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return start_dir

PROJECT_ROOT = find_project_root(SKILL_DIR)
REPORT_DIR = os.path.join(PROJECT_ROOT, 'testing-report')
os.makedirs(REPORT_DIR, exist_ok=True)

AGENT_BROWSER_CMD = ['agent-browser']

# ================== 基础工具 ==================

def run_cmd(args, timeout=60):
    full_cmd = AGENT_BROWSER_CMD + args
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def safe_eval(js_code):
    wrapped_js = f"""
    (function() {{
        try {{
            const result = {js_code};
            return JSON.stringify(result);
        }} catch(e) {{
            return JSON.stringify({{error: e.message}});
        }}
    }})()
    """
    output, success = run_cmd(['eval', wrapped_js])
    if not success or not output: return None
    try:
        lines = output.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('{') or line.startswith('['):
                return json.loads(line)
        return json.loads(output)
    except:
        return None

# ================== 模式 1: Inspect (观察) ==================

def inspect_page(url):
    """打开页面并提取交互元素结构"""
    print(f"[INSPECT] Opening {url}...")
    run_cmd(['open', url, '--wait'])
    
    js = """
    {
        title: document.title,
        url: window.location.href,
        inputs: Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select')).map(el => ({
            id: el.id,
            name: el.name,
            type: el.type,
            placeholder: el.placeholder || '',
            label: el.labels && el.labels[0] ? el.labels[0].innerText : '',
            selector: (el.id ? '#' + el.id : (el.name ? '[name="' + el.name + '"]' : el.tagName.toLowerCase()))
        })),
        buttons: Array.from(document.querySelectorAll('button, input[type="submit"], a[class*="btn"], div[role="button"]')).map(el => ({
            text: el.innerText.trim() || el.value || '',
            id: el.id,
            class: el.className,
            selector: (el.id ? '#' + el.id : (el.innerText ? "text=" + el.innerText.trim() : el.tagName.toLowerCase()))
        })),
        links: Array.from(document.querySelectorAll('a[href]')).slice(0, 10).map(el => ({
            text: el.innerText.trim(),
            href: el.href
        }))
    }
    """
    data = safe_eval(js)
    if not data:
        return {"error": "Failed to inspect page"}
    
    summary = {
        "title": data.get('title'),
        "url": data.get('url'),
        "interactive_elements": {
            "inputs": [f"[{i['type']}] id={i['id']} name={i['name']} label='{i['label']}'" for i in data.get('inputs', [])],
            "buttons": [f"[Button] text='{b['text']}' id={b['id']}" for b in data.get('buttons', [])]
        },
        "links_sample": [l['href'] for l in data.get('links', [])]
    }
    return summary

# ================== 模式 2: Run Steps (执行) ==================

def run_steps(url, steps_json):
    """执行 AI 编排的步骤序列"""
    try:
        steps = json.loads(steps_json)
    except:
        return {"error": "Invalid JSON steps"}

    print(f"[RUN] Opening {url}...")
    run_cmd(['open', url, '--wait'])
    
    logs = []
    
    for i, step in enumerate(steps):
        action = step.get('action')
        target = step.get('target') 
        value = step.get('value')
        
        log_entry = {"step": i+1, "action": action, "target": target, "status": "pending"}
        print(f"  Step {i+1}: {action} {target} {value if value else ''}")
        
        try:
            if action == 'fill':
                run_cmd(['type', target, str(value)])
                log_entry['status'] = 'success'
                
            elif action == 'click':
                if target.startswith('text='):
                    txt = target.replace('text=', '')
                    js_click = f"""
                    (function() {{
                        const el = Array.from(document.querySelectorAll('button, a, input[type="submit"]'))
                            .find(e => e.innerText.includes('{txt}'));
                        if(el) {{ el.click(); return true; }}
                        return false;
                    }})()
                    """
                    res = safe_eval(js_click)
                    if not res: 
                        run_cmd(['click', target])
                else:
                    run_cmd(['click', target])
                log_entry['status'] = 'success'
                
            elif action == 'wait':
                time.sleep(int(value or 2))
                log_entry['status'] = 'success'
                
            elif action == 'screenshot':
                ts = datetime.datetime.now().strftime("%H%M%S")
                path = os.path.join(REPORT_DIR, f"step_{i+1}_{ts}.png")
                run_cmd(['screenshot', path])
                log_entry['status'] = 'success'
                log_entry['file'] = path

            elif action == 'verify_text':
                page_text, _ = run_cmd(['eval', 'document.body.innerText'])
                if value in page_text:
                    log_entry['status'] = 'success'
                else:
                    log_entry['status'] = 'failed'
                    log_entry['error'] = f"Text '{value}' not found"

            logs.append(log_entry)
            
        except Exception as e:
            log_entry['status'] = 'error'
            log_entry['error'] = str(e)
            logs.append(log_entry)
            break 

    return {"steps_executed": len(logs), "logs": logs}

# ================== 模式 3: Auto (原有一键模式) ==================

def run_auto(url):
    data = inspect_page(url)
    if "error" in data: return data
    
    steps = []
    steps.append({"action": "screenshot", "target": "initial", "value": ""})
    
    # 安全地获取嵌套字典
    interactive = data.get('interactive_elements')
    if isinstance(interactive, dict):
        inputs = interactive.get('inputs', [])
        btns = interactive.get('buttons', [])
        
        # 尝试填写
        for inp_str in inputs[:3]: 
            name_m = re.search(r"name=([^\s]+)", inp_str)
            id_m = re.search(r"id=([^\s]+)", inp_str)
            
            target = ""
            if name_m: target = f"[name='{name_m.group(1)}']"
            elif id_m: target = f"#{id_m.group(1)}"
            
            if target:
                steps.append({"action": "fill", "target": target, "value": "AutoTest"})
        
        # 尝试点击
        submit_btn = next((b for b in btns if any(k in b.lower() for k in ['submit', 'save', 'login', 'search'])), None)
        if submit_btn:
            txt_m = re.search(r"text='([^']+)'", submit_btn)
            if txt_m:
                steps.append({"action": "click", "target": f"text={txt_m.group(1)}"})
    
    steps.append({"action": "wait", "value": 2})
    steps.append({"action": "screenshot", "target": "after_action"})

    return run_steps(url, json.dumps(steps))

# ================== Entry Point ==================

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode', required=True)

    p_inspect = subparsers.add_parser('inspect')
    p_inspect.add_argument('--url', required=True)

    p_run = subparsers.add_parser('run')
    p_run.add_argument('--url', required=True)
    p_run.add_argument('--steps', required=True)

    p_auto = subparsers.add_parser('auto')
    p_auto.add_argument('--url', required=True)
    p_auto.add_argument('--operation', default='all')

    args = parser.parse_args()

    result = {}
    if args.mode == 'inspect':
        result = inspect_page(args.url)
    elif args.mode == 'run':
        result = run_steps(args.url, args.steps)
    elif args.mode == 'auto':
        result = run_auto(args.url)

    print("\n__JSON_START__")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("__JSON_END__")
