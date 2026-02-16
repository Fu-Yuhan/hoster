"""工具注册中心 —— 装饰器自动收集 函数 / Schema / 显示名"""

import json
from typing import Any, Callable, Dict, List, Optional, Sequence


class ToolRegistry:
    """
    全局工具注册表（单例模式，纯类方法）。

    用法:
        @ToolRegistry.register(
            name="my_tool",
            display_name="🔧 我的工具",
            description="做某件事",
            parameters={"arg1": {"type": "string", "description": "..."}},
            required=["arg1"],
        )
        def my_tool(arg1: str) -> dict:
            return {"result": "ok"}
    """

    _entries: Dict[str, dict] = {}

    # ──────────── 注册 ────────────

    @classmethod
    def register(
        cls,
        *,
        name: str,
        display_name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[Sequence[str]] = None,
    ):
        """装饰器：将函数注册为可调用工具"""

        def decorator(fn: Callable) -> Callable:
            params_schema = {"type": "object", "properties": parameters}
            if required:
                params_schema["required"] = list(required)

            cls._entries[name] = {
                "fn": fn,
                "display_name": display_name,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": params_schema,
                    },
                },
            }
            return fn

        return decorator

    # ──────────── 查询 ────────────

    @classmethod
    def get_schemas(cls) -> List[dict]:
        """返回所有工具的 OpenAI function-calling schema 列表"""
        return [e["schema"] for e in cls._entries.values()]

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """返回 {tool_name: display_name} 映射"""
        return {k: e["display_name"] for k, e in cls._entries.items()}

    @classmethod
    def list_names(cls) -> List[str]:
        return list(cls._entries.keys())

    # ──────────── 调用 ────────────

    @classmethod
    def call(cls, name: str, args: dict) -> str:
        """统一调度入口，返回 JSON 字符串"""
        entry = cls._entries.get(name)
        if not entry:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        try:
            result = entry["fn"](**args)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)