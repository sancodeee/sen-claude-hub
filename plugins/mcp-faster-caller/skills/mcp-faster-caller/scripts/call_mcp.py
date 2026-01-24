#!/usr/bin/env python3
# coding: utf-8
"""
MCP 统一调用解析器
把用户简短指令转成结构化 MCP 调用

版本: 2.2 - 高性能优化，移除配置文件支持，双语别名映射
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Union

# 轻量级日志配置
logger = logging.getLogger(__name__)
if os.getenv('MCP_FAST_CALLER_DEBUG'):
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        force=True  # 确保配置生效
    )

# MCP别名映射（双语支持）
MCP_MAP: Dict[str, str] = {
    # GitHub & 代码仓库
    "gh": "github",
    "github": "github",
    "gitlab": "zread",
    "gitee": "zread",
    "repo": "zread",
    "repository": "zread",
    "开源仓库": "zread",
    "代码仓库": "zread",
    # 数据库
    "db": "mysql",
    "database": "mysql",
    "sql": "mysql",
    "mysql": "mysql",
    "查库": "mysql",
    "查询数据库": "mysql",
    "数据库": "mysql",
    # 浏览器测试
    "browser": "playwright",
    "web": "playwright",
    "web page": "playwright",
    "chrome": "chrome-devtools",
    "firefox": "playwright",
    "edge": "playwright",
    "safari": "playwright",
    "浏览器": "playwright",
    "浏览器测试": "playwright",
    "谷歌浏览器": "chrome-devtools",
    "谷歌浏览器测试": "chrome-devtools",
    # 搜索
    "search": "web-search-prime",
    "搜索": "web-search-prime",
    # 网页读取
    "read web": "web-reader",
    "web-reader": "web-reader",
    "web reader": "web-reader",
    "网页读取": "web-reader",
    "读取网页": "web-reader",
    # 视觉理解
    "picture": "zai-mcp-server",
    "image": "zai-mcp-server",
    "photo": "zai-mcp-server",
    "illustration": "zai-mcp-server",
    "查看图片": "zai-mcp-server",
    "图片": "zai-mcp-server",
    "图像": "zai-mcp-server",
    "视觉": "zai-mcp-server",
    # API文档
    "API docs": "context7",
    "API documentation": "context7",
    "API": "context7",
    "API文档": "context7",
    # PDF 读取
    "pdf": "pdf-reader",
    "pdf-reader": "pdf-reader",
    "pdf reader": "pdf-reader",
    "读取pdf": "pdf-reader",
    "pdf读取": "pdf-reader",
    "pdf解析": "pdf-reader",
    "解析pdf": "pdf-reader"
}


def get_mcp_map() -> Dict[str, str]:
    """获取MCP映射表"""
    return MCP_MAP


class MCPParserError(Exception):
    """MCP 解析错误"""
    pass


def validate_input(text: str) -> str:
    """清理和验证输入"""
    if not isinstance(text, str):
        raise MCPParserError("输入必须是字符串")

    text = text.strip()
    if not text:
        raise MCPParserError("指令为空")

    # 检查长度限制
    if len(text) > 1000:
        raise MCPParserError("指令过长（最大1000字符）")

    return text


def parse_arguments(args_str: str) -> Union[str, Dict[str, Any]]:
    """智能参数解析，支持普通字符串、JSON和命名参数格式"""
    args_str = args_str.strip()
    if not args_str:
        return ""

    # 快速检查JSON格式
    if args_str.startswith('{') and args_str.endswith('}'):
        try:
            return json.loads(args_str)
        except json.JSONDecodeError:
            pass  # 回退到字符串处理

    # 快速检查命名参数格式
    if '=' in args_str:
        # 简单的key=value解析
        result = {}
        for pair in args_str.split():
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 移除引号
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"')) or
                    (value.startswith("'") and value.endswith("'"))
                ):
                    value = value[1:-1]
                result[key] = value
        if result:
            return result

    return args_str


def parse_mcp_call(text: str) -> Dict[str, Any]:
    """
    增强版 MCP 调用指令解析

    支持格式：
    - 传统格式: alias command args
    - JSON参数: alias command {"key": "value"}
    - 命名参数: alias command key1=value1 key2=value2

    Args:
        text: 用户输入的指令字符串

    Returns:
        包含解析结果的字典

    Raises:
        MCPParserError: 解析失败时抛出
    """
    try:
        text = validate_input(text)

        # 快速分割指令
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            raise MCPParserError(
                "格式错误: alias command [arguments]\n"
                "支持格式:\n"
                "  普通参数: alias command arg1 arg2\n"
                "  JSON参数: alias command {\"key\": \"value\"}\n"
                "  命名参数: alias command key=value\n"
                "示例: gh list-repos owner=username"
            )

        alias = parts[0].lower()
        command = parts[1].strip()
        args_str = parts[2].strip() if len(parts) > 2 else ""

        # 快速验证别名
        mcp_map = get_mcp_map()
        server = mcp_map.get(alias)
        if not server:
            available_aliases = sorted(mcp_map.keys())
            raise MCPParserError(
                f"未知别名 '{alias}'\n"
                f"可用别名: {', '.join(available_aliases[:8])}{'...' if len(available_aliases) > 8 else ''}"
            )

        # 验证命令
        if not command:
            raise MCPParserError("命令不能为空")

        # 解析参数
        parsed_args = parse_arguments(args_str)

        return {
            "server": server,
            "command": command,
            "arguments": parsed_args,
            "original": text,
            "alias": alias,
            "format": "json" if isinstance(parsed_args, dict) else "string"
        }

    except MCPParserError:
        raise
    except Exception as e:
        raise MCPParserError(f"解析失败: {str(e)}")


def show_help() -> None:
    """显示增强版帮助信息"""
    mcp_map = get_mcp_map()

    # 按类别分组别名
    categories = {
        "代码仓库": ["gh", "github", "gitlab", "gitee", "repo", "repository"],
        "数据库": ["db", "database", "sql", "mysql"],
        "浏览器": ["browser", "web", "chrome", "firefox", "edge", "safari"],
        "搜索": ["search"],
        "网页读取": ["read web", "web-reader"],
        "图像分析": ["image", "picture", "photo", "illustration"],
        "API文档": ["API docs", "API documentation", "API"],
        "PDF读取": ["pdf", "pdf-reader", "pdf reader"]
    }

    print("MCP Fast Caller v2.2 - 高性能 MCP 调用解析器")
    print()
    print("🚀 用法:")
    print('    python3 call_mcp.py "alias command [arguments]"')
    print()
    print("📝 支持的参数格式:")
    print("    普通参数: alias command arg1 arg2")
    print('    JSON参数: alias command {"key": "value", "key2": "value2"}')
    print('    命名参数: alias command key1=value1 key2="quoted value"')
    print()
    print(" 💡 示例:")
    print('     # 传统格式')
    print('     python3 call_mcp.py "gh list-repos owner=username"')
    print()
    print('     # JSON参数')
    print('''     python3 call_mcp.py 'gh search-code {"query": "test", "language": "python"}' ''')
    print()
    print('     # 命名参数')
    print('     python3 call_mcp.py "browser screenshot width=1920 height=1080"')
    print()
    print(f"📋 可用别名 ({len(mcp_map)} 个):")

    for category, aliases in categories.items():
        available_in_category = [alias for alias in aliases if alias in mcp_map]
        if available_in_category:
            server = mcp_map.get(available_in_category[0], "unknown")
            print(f"    {category}: {', '.join(available_in_category)} -> {server}")

    # 显示其他未分类的别名
    categorized = set()
    for cat_aliases in categories.values():
        categorized.update(cat_aliases)

    other_aliases = [alias for alias in sorted(mcp_map.keys()) if alias not in categorized]
    if other_aliases:
        print(f"    其他: {', '.join(other_aliases[:5])}{'...' if len(other_aliases) > 5 else ''}")

    print()
    print("⚙️  配置:")
    print("    MCP_FAST_CALLER_DEBUG=1  启用调试模式")
    print()
    print("📖 更多信息: references/mcp_aliases.md")


def main():
    """主函数"""
    try:
        # 检查帮助请求
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            return

        # 获取输入
        if len(sys.argv) > 1:
            instruction = " ".join(sys.argv[1:])
        else:
            instruction = sys.stdin.read().strip()

        # 解析指令
        result = parse_mcp_call(instruction)

        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except MCPParserError as e:
        error_result = {"error": str(e)}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(130)
    except Exception as e:
        error_result = {"error": f"意外错误: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        logger.error(f"意外错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
