"""工具：获取指定区域某传感器的实时数据"""

import sqlite3
from datetime import datetime

from ._registry   import ToolRegistry
from ._constants  import DB_PATH, NAMES, UNITS, ZONE_PARAM, SENSOR_PARAM
from ._simulator  import sim


@ToolRegistry.register(
    name="get_current_sensor_data",
    display_name="📡 查询传感器数据",
    description="获取指定区域某个传感器的实时数据",
    parameters={
        "zone":        ZONE_PARAM,
        "sensor_type": SENSOR_PARAM,
    },
    required=["zone", "sensor_type"],
)
def get_current_sensor_data(zone: str, sensor_type: str) -> dict:
    now = datetime.now()
    val = sim(zone, sensor_type, now)
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO sensor_data VALUES(NULL,?,?,?,?)",
                  (now.isoformat(), zone, sensor_type, val))
    return {
        "zone":   zone,
        "sensor": NAMES[sensor_type],
        "value":  val,
        "unit":   UNITS[sensor_type],
        "time":   now.strftime("%Y-%m-%d %H:%M:%S"),
    }