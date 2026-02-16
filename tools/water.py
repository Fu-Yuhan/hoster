"""工具：浇水控制"""

import sqlite3
from datetime import datetime

from ._registry  import ToolRegistry
from ._constants import DB_PATH, ZONE_PARAM


@ToolRegistry.register(
    name="water_zone",
    display_name="💧 执行浇水操作",
    description="对指定区域进行浇水，需指定水量（升）",
    parameters={
        "zone":           ZONE_PARAM,
        "amount_liters":  {"type": "number", "description": "浇水量（升）"},
    },
    required=["zone", "amount_liters"],
)
def water_zone(zone: str, amount_liters: float) -> dict:
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            "INSERT INTO logs VALUES(NULL,?,?,?,?)",
            (now.isoformat(), "浇水", f"{zone}区域 浇水 {amount_liters}L", "AI"),
        )
    return {
        "status":  "success",
        "message": f"已向{zone}区域浇水 {amount_liters} 升",
        "time":    now.strftime("%Y-%m-%d %H:%M:%S"),
    }