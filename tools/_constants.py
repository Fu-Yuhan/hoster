"""共享常量 & 可复用的 JSON Schema 片段"""

DB_PATH = "farm.db"

ZONES   = ["东北", "西北", "东南", "西南"]
SENSORS = ["temperature", "humidity", "co2", "light"]
UNITS   = {"temperature": "°C", "humidity": "%", "co2": "ppm", "light": "lux"}
NAMES   = {"temperature": "温度", "humidity": "湿度", "co2": "CO₂浓度", "light": "光照强度"}

# ── 可复用的参数 Schema 片段（工具文件直接引用） ──
ZONE_PARAM   = {"type": "string", "enum": ZONES,   "description": "区域：东北/西北/东南/西南"}
SENSOR_PARAM = {"type": "string", "enum": SENSORS, "description": "传感器：temperature/humidity/co2/light"}