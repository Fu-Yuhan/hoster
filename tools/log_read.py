"""工具：读取操作日志"""

import sqlite3
from typing import Optional

from ._registry  import ToolRegistry
from ._constants import DB_PATH


@ToolRegistry.register(
    name="read_logs",
    display_name="📖 读取操作日志",
    description="查询系统操作日志，可按类型筛选",
    parameters={
        "limit":          {"type": "integer", "description": "返回条数，默认 10"},
        "operation_type": {"type": "string",  "description": "按操作类型筛选（可选）"},
    },
)
def read_logs(limit: int = 10, operation_type: Optional[str] = None) -> dict:
    with sqlite3.connect(DB_PATH) as c:
        if operation_type:
            rows = c.execute(
                "SELECT ts,op,detail,who FROM logs "
                "WHERE op=? ORDER BY id DESC LIMIT ?",
                (operation_type, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT ts,op,detail,who FROM logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    return {
        "count": len(rows),
        "logs": [
            {"time": r[0], "type": r[1], "detail": r[2], "operator": r[3]}
            for r in rows
        ],
    }