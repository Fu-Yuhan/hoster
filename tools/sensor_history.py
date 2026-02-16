"""工具：获取历史传感器数据（含统计）"""

import sqlite3
from datetime import datetime, timedelta

from ._registry   import ToolRegistry
from ._constants  import DB_PATH, NAMES, UNITS, ZONE_PARAM, SENSOR_PARAM
from ._simulator  import sim


@ToolRegistry.register(
    name="get_historical_sensor_data",
    display_name="📈 查询历史趋势",
    description="获取指定区域某个传感器过去 N 小时的历史数据（含最小/最大/平均值）",
    parameters={
        "zone":        ZONE_PARAM,
        "sensor_type": SENSOR_PARAM,
        "hours":       {"type": "number", "description": "过去多少小时"},
    },
    required=["zone", "sensor_type", "hours"],
)
def get_historical_sensor_data(zone: str, sensor_type: str, hours: float) -> dict:
    now   = datetime.now()
    start = now - timedelta(hours=hours)

    # 优先读数据库
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute(
            "SELECT ts, val FROM sensor_data "
            "WHERE zone=? AND type=? AND ts>=? ORDER BY ts",
            (zone, sensor_type, start.isoformat()),
        ).fetchall()

    if len(rows) >= 5:
        data = []
        for ts_str, val in rows:
            try:
                t = datetime.fromisoformat(ts_str)
                data.append({"time": t.strftime("%m-%d %H:%M"), "value": val})
            except Exception:
                continue
        source = "数据库"
    else:
        # 数据不足，模拟补充
        step = 30 if hours <= 24 else (60 if hours <= 168 else 180)
        data = [
            {
                "time":  (now - timedelta(minutes=i * step)).strftime("%m-%d %H:%M"),
                "value": sim(zone, sensor_type, now - timedelta(minutes=i * step)),
            }
            for i in range(int(hours * 60 / step), 0, -1)
        ]
        source = "模拟"

    vals = [d["value"] for d in data]
    return {
        "zone": zone, "sensor": NAMES[sensor_type], "unit": UNITS[sensor_type],
        "period": f"过去{hours}小时", "count": len(data),
        "min": min(vals), "max": max(vals),
        "avg": round(sum(vals) / len(vals), 1),
        "data_source": source,
        "data": data,
    }