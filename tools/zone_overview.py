"""工具：一次性获取某区域所有传感器当前读数"""

import sqlite3
from datetime import datetime

from ._registry   import ToolRegistry
from ._constants  import DB_PATH, SENSORS, NAMES, UNITS, ZONE_PARAM
from ._simulator  import sim


@ToolRegistry.register(
    name="get_zone_overview",
    display_name="📋 获取区域概览",
    description="一次性获取指定区域全部传感器（温度/湿度/CO₂/光照）的当前读数",
    parameters={"zone": ZONE_PARAM},
    required=["zone"],
)
def get_zone_overview(zone: str) -> dict:
    now = datetime.now()
    readings = {}
    with sqlite3.connect(DB_PATH) as c:
        for s in SENSORS:
            v = sim(zone, s, now)
            c.execute("INSERT INTO sensor_data VALUES(NULL,?,?,?,?)",
                      (now.isoformat(), zone, s, v))
            readings[NAMES[s]] = {"value": v, "unit": UNITS[s]}
    return {
        "zone": zone,
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "readings": readings,
    }