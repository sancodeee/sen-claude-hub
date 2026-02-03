import argparse
import datetime
import json
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

# ================== Configuration & Utils ==================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)


def find_project_root(start_dir: str) -> str:
    current = start_dir
    for _ in range(6):
        if os.path.exists(os.path.join(current, '.git')) or \
                os.path.exists(os.path.join(current, 'package.json')):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # reached root
            break
        current = parent
    return start_dir


PROJECT_ROOT = find_project_root(SKILL_DIR)
REPORT_DIR = os.path.join(PROJECT_ROOT, 'testing-report')
os.makedirs(REPORT_DIR, exist_ok=True)


class BrowserClient:
    """封装 agent-browser CLI 调用"""

    CMD = ['agent-browser']

    @staticmethod
    def run(args: List[str], timeout: int = 60) -> Tuple[str, bool]:
        full_cmd = BrowserClient.CMD + args
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.stdout.strip(), result.returncode == 0
        except subprocess.TimeoutExpired:
            return "Command timed out", False
        except Exception as e:
            return f"Subprocess error: {str(e)}", False

    @staticmethod
    def eval(js_code: str) -> Optional[Any]:
        wrapped = f"""
        (function() {{
            try {{
                const result = {js_code};
                return JSON.stringify({{success: true, data: result}});
            }} catch(e) {{
                return JSON.stringify({{success: false, error: e.message}});
            }}
        }})()
        """

        output, success = BrowserClient.run(['eval', wrapped])
        if not success or not output:
            return None

        # 更健壮地找最后一行有效的 JSON
        try:
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            for line in reversed(lines):
                if line.startswith(('{', '[')):
                    parsed = json.loads(line)
                    if isinstance(parsed, dict) and parsed.get('success'):
                        return parsed.get('data')
                    if 'error' in parsed:
                        print(f"[EVAL WARN] JS error: {parsed['error']}")
                    return None
            # 兜底尝试整段解析
            return json.loads(output)
        except json.JSONDecodeError:
            print(f"[EVAL FAIL] Invalid JSON output:\n{output[:300]}...")
            return None

    @staticmethod
    def screenshot(name_prefix: str = "step") -> str:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name_prefix}_{ts}.png"
        path = os.path.join(REPORT_DIR, filename)
        _, ok = BrowserClient.run(['screenshot', path])
        if not ok:
            print(f"[WARN] Screenshot failed: {path}")
        return path


# ================== Feature Modules ==================

class Inspector:
    @staticmethod
    def analyze(url: str) -> Dict:
        print(f"[INSPECT] Opening → {url}")
        BrowserClient.run(['open', url, '--wait'], timeout=90)

        js = """
        {
            title: document.title.trim(),
            url: window.location.href,
            inputs: Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select'))
                .map(el => ({
                    id: el.id || '',
                    name: el.name || '',
                    type: el.type || el.tagName.toLowerCase(),
                    placeholder: el.placeholder || '',
                    label: el.labels?.[0]?.innerText.trim() || '',
                })),
            buttons: Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"], .btn, [class*="button"]'))
                .map(el => ({
                    text: (el.innerText || el.value || '').trim(),
                    id: el.id || ''
                })),
            links: Array.from(document.querySelectorAll('a[href]')).slice(0,8)
                .map(el => ({ text: el.innerText.trim(), href: el.href }))
        }
        """

        data = BrowserClient.eval(js)
        if not isinstance(data, dict):
            return {"error": "Failed to analyze DOM"}

        inputs_summary = [
            f"[{i['type']}] id={i['id']} name={i['name']} label='{i['label']}' placeholder='{i['placeholder']}'"
            for i in data.get('inputs', [])
        ]

        buttons_summary = [
            f"[Button] text='{b['text']}' id={b['id']}"
            for b in data.get('buttons', [])
            if b['text']
        ]

        return {
            "title": data.get('title', ''),
            "url": data.get('url', url),
            "elements": {
                "inputs": inputs_summary,
                "buttons": buttons_summary,
            },
            "links": [l['href'] for l in data.get('links', [])]
        }


class Executor:
    @staticmethod
    def run_sequence(url: str, steps: List[Dict]) -> Dict:
        print(f"[EXEC] Opening → {url}")
        BrowserClient.run(['open', url, '--wait'], timeout=90)

        logs: List[Dict] = []
        for idx, step in enumerate(steps, 1):
            action = step.get('action')
            target = step.get('target')
            value = step.get('value')

            entry = {
                "step": idx,
                "action": action,
                "target": target,
                "value": value,
                "status": "pending"
            }
            print(f"  → {idx:2d} | {action:<10} {target or ''}")

            try:
                if action == 'fill':
                    if not target or not value:
                        raise ValueError("fill needs target & value")
                    BrowserClient.run(['type', target, str(value)])
                    entry["status"] = "success"

                elif action == 'click':
                    if not target:
                        raise ValueError("click needs target")
                    if target.startswith('text='):
                        txt = target[5:].strip()
                        js = f"""
                        Array.from(document.querySelectorAll('button,a,input,div[role]'))
                            .find(e => e.innerText.trim().includes(`{txt}`))?.click()
                        """
                        BrowserClient.eval(js)  # 优先尝试 JS 点击
                    else:
                        BrowserClient.run(['click', target])
                    entry["status"] = "success"

                elif action == 'wait':
                    seconds = float(value or 2)
                    time.sleep(seconds)
                    entry["status"] = "success"

                elif action == 'screenshot':
                    path = BrowserClient.screenshot(f"step_{idx}")
                    entry.update({"status": "success", "file": path})

                elif action == 'verify_text':
                    if not value:
                        raise ValueError("verify_text needs value")
                    body, _ = BrowserClient.run(['eval', 'document.body.innerText'])
                    entry["status"] = "success" if value in body else "failed"
                    if entry["status"] == "failed":
                        entry["error"] = f"Text '{value}' not found in body"

                else:
                    entry["status"] = "skipped"
                    entry["error"] = f"Unknown action: {action}"

            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)

            logs.append(entry)

            if entry["status"] in ("error", "failed"):
                print(f"  !! Step {idx} failed → stopping")
                break

        return {"executed": len(logs), "logs": logs}


class HeuristicTester:
    @staticmethod
    def auto_run(url: str) -> Dict:
        print("[AUTO] Analyzing page...")
        analysis = Inspector.analyze(url)
        if "error" in analysis:
            return analysis

        steps = [{"action": "screenshot", "target": "initial"}]

        # 自动填充前几个 input
        for inp_str in analysis["elements"]["inputs"][:3]:
            m = re.search(r"name=([^\s\]]+)", inp_str)
            if m:
                name = m.group(1)
                steps.append({"action": "fill", "target": f"[name=\"{name}\"]", "value": "TestInput"})

        # 寻找可能的提交按钮
        for btn_str in analysis["elements"]["buttons"]:
            text = ""
            m = re.search(r"text='([^']+)'", btn_str)
            if m:
                text = m.group(1).lower()
            if any(word in text for word in ['submit', 'login', 'sign in', 'search', 'go', 'send']):
                steps.append({"action": "click", "target": f"text={text}"})
                break

        steps.extend([
            {"action": "wait", "value": 3},
            {"action": "screenshot", "target": "final"}
        ])

        return Executor.run_sequence(url, steps)


# ================== CLI Entry ==================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Browser automation & testing helper")
    subparsers = parser.add_subparsers(dest='mode', required=True)

    p = subparsers.add_parser('inspect', help="Analyze page DOM")
    p.add_argument('--url', required=True)

    p = subparsers.add_parser('run', help="Execute step sequence")
    p.add_argument('--url', required=True)
    p.add_argument('--steps', required=True, help="JSON string of steps array")

    p = subparsers.add_parser('auto', help="Auto-generated smoke test")
    p.add_argument('--url', required=True)

    args = parser.parse_args()

    result: Dict = {"error": "Unknown mode"}

    try:
        if args.mode == 'inspect':
            result = Inspector.analyze(args.url)
        elif args.mode == 'run':
            steps = json.loads(args.steps)
            if not isinstance(steps, list):
                raise ValueError("--steps must be a JSON array")
            result = Executor.run_sequence(args.url, steps)
        elif args.mode == 'auto':
            result = HeuristicTester.auto_run(args.url)
    except json.JSONDecodeError as e:
        result = {"error": f"Invalid JSON in --steps: {e}"}
    except Exception as e:
        result = {"error": f"Runtime error: {str(e)}"}

    print("\n__JSON_START__")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("__JSON_END__")
