import argparse
import datetime
import json
import os
import re
import subprocess
import time

# ================== 1. Configuration & Utils ==================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

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

class BrowserClient:
    """Encapsulates raw CLI interactions"""
    CMD = ['agent-browser']

    @staticmethod
    def run(args, timeout=60):
        full_cmd = BrowserClient.CMD + args
        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip(), result.returncode == 0
        except Exception as e:
            return str(e), False

    @staticmethod
    def eval(js_code):
        wrapped = f"""
        (function() {{
            try {{
                const result = {js_code};
                return JSON.stringify(result);
            }} catch(e) {{
                return JSON.stringify({{error: e.message}});
            }}
        }})()
        """
        output, success = BrowserClient.run(['eval', wrapped])
        if not success or not output: return None
        
        try:
            lines = output.strip().split('\n')
            for line in reversed(lines):
                if line.strip().startswith(('{', '[')):
                    return json.loads(line)
            return json.loads(output)
        except:
            return None

    @staticmethod
    def screenshot(name_prefix):
        ts = datetime.datetime.now().strftime("%H%M%S")
        filename = f"{name_prefix}_{ts}.png"
        path = os.path.join(REPORT_DIR, filename)
        BrowserClient.run(['screenshot', path])
        return path

# ================== 2. Feature Modules ==================

class Inspector:
    """Module for analyzing page DOM"""
    
    @staticmethod
    def analyze(url):
        print(f"[INSPECT] Opening {url}...")
        BrowserClient.run(['open', url, '--wait'])
        
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
                selector: (el.id ? '#' + el.id : (el.innerText ? "text=" + el.innerText.trim() : el.tagName.toLowerCase()))
            })),
            links: Array.from(document.querySelectorAll('a[href]')).slice(0, 10).map(el => ({
                text: el.innerText.trim(),
                href: el.href
            }))
        }
        """
        data = BrowserClient.eval(js)
        if not data: return {"error": "DOM analysis failed"}
        
        return {
            "title": data.get('title'),
            "url": data.get('url'),
            "elements": {
                "inputs": [f"[{i['type']}] id={i['id']} name={i['name']} label='{i['label']}'" for i in data.get('inputs', [])],
                "buttons": [f"[Button] text='{b['text']}' id={b['id']}" for b in data.get('buttons', [])]
            },
            "links": [l['href'] for l in data.get('links', [])]
        }

class Executor:
    """Module for executing step sequences"""

    @staticmethod
    def run_sequence(url, steps):
        print(f"[RUN] Opening {url}...")
        BrowserClient.run(['open', url, '--wait'])
        
        logs = []
        for i, step in enumerate(steps):
            act = step.get('action')
            tgt = step.get('target')
            val = step.get('value')
            
            entry = {"step": i+1, "action": act, "target": tgt, "status": "pending"}
            print(f"  Step {i+1}: {act} {tgt or ''}")
            
            try:
                if act == 'fill':
                    BrowserClient.run(['type', tgt, str(val)])
                    entry['status'] = 'success'
                    
                elif act == 'click':
                    if tgt and tgt.startswith('text='):
                        txt = tgt.replace('text=', '')
                        js_click = f"""
                        (function() {{
                            const el = Array.from(document.querySelectorAll('button, a, input'))
                                .find(e => e.innerText.includes('{txt}'));
                            if(el) {{ el.click(); return true; }}
                            return false;
                        }})()
                        """
                        if not BrowserClient.eval(js_click):
                            BrowserClient.run(['click', tgt]) 
                    else:
                        BrowserClient.run(['click', tgt])
                    entry['status'] = 'success'
                    
                elif act == 'wait':
                    time.sleep(int(val or 2))
                    entry['status'] = 'success'
                    
                elif act == 'screenshot':
                    path = BrowserClient.screenshot(f"step_{i+1}")
                    entry['status'] = 'success'
                    entry['file'] = path
                
                elif act == 'verify_text':
                    body_text, _ = BrowserClient.run(['eval', 'document.body.innerText'])
                    if val in body_text:
                        entry['status'] = 'success'
                    else:
                        entry['status'] = 'failed'
                        entry['error'] = f"Text '{val}' not found"

            except Exception as e:
                entry['status'] = 'error'
                entry['error'] = str(e)
            
            logs.append(entry)
            if entry['status'] in ['failed', 'error']: break
            
        return {"executed": len(logs), "logs": logs}

class HeuristicTester:
    """Module for auto-generating smoke tests"""

    @staticmethod
    def auto_run(url):
        data = Inspector.analyze(url)
        if "error" in data: return data
        
        steps = []
        steps.append({"action": "screenshot", "target": "initial"})
        
        # Safe access to nested structure
        elements = data.get('elements', {})
        if isinstance(elements, dict):
            inputs = elements.get('inputs', [])
            for inp in inputs[:3]:
                name_m = re.search(r"name=([^\s]+)", inp)
                target = f"[name='{name_m.group(1)}']" if name_m else ""
                if target:
                    steps.append({"action": "fill", "target": target, "value": "Test"})
            
            btns = elements.get('buttons', [])
            submit_btn = next((b for b in btns if any(k in b.lower() for k in ['submit', 'login', 'search'])), None)
            if submit_btn:
                txt_m = re.search(r"text='([^']+)'", submit_btn)
                if txt_m:
                    steps.append({"action": "click", "target": f"text={txt_m.group(1)}"})
        
        steps.append({"action": "wait", "value": 2})
        steps.append({"action": "screenshot", "target": "end"})
        
        return Executor.run_sequence(url, steps)

# ================== 3. Main CLI Entry ==================

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode', required=True)

    p_insp = subparsers.add_parser('inspect')
    p_insp.add_argument('--url', required=True)

    p_run = subparsers.add_parser('run')
    p_run.add_argument('--url', required=True)
    p_run.add_argument('--steps', required=True)

    p_auto = subparsers.add_parser('auto')
    p_auto.add_argument('--url', required=True)
    p_auto.add_argument('--operation', default='all')

    args = parser.parse_args()
    
    try:
        if args.mode == 'inspect':
            res = Inspector.analyze(args.url)
        elif args.mode == 'run':
            steps = json.loads(args.steps)
            res = Executor.run_sequence(args.url, steps)
        elif args.mode == 'auto':
            res = HeuristicTester.auto_run(args.url)
        else:
            res = {"error": "Unknown mode"}
    except Exception as e:
        res = {"error": str(e)}

    print("\n__JSON_START__")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print("__JSON_END__")
