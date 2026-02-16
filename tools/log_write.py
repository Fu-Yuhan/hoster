"""工具：写入操作日志"""

import sqlite3
from datetime import datetime

from ._registry  import ToolRegistry
from ._constants import DB_PATH


@ToolRegistry.register(
    name="write_log",
    display_name="📝 写入操作日志",
    description="向系统日志写入一条操作记录",
    parameters={
        "operation_type": {"type": "string", "description": "操作类型，如：施肥、巡检、告警"},
        "details":        {"type": "string", "description": "操作详情"},
    },
    required=["operation_type", "details"],
)
def write_log(operation_type: str, details: str) -> dict:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            "INSERT INTO logs VALUES(NULL,?,?,?,?)",
            (datetime.now().isoformat(), operation_type, details, "AI"),
        )
    return {"status": "success", "message": "日志已写入"}