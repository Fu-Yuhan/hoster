"""AI智慧农业 —— 工具模块
传感器模拟（含时间趋势 + 区域偏移）、浇水控制、日志读写
新增工具只需：① 写函数  ② 加 TOOL_DEFS  ③ 加 _FN
"""

import sqlite3, json, math, random
from datetime import datetime, timedelta

# ═══════════════════ 常量 ═══════════════════

DB = "farm.db"
ZONES = ["东北", "西北", "东南", "西南"]
SENSORS = ["temperature", "humidity", "co2", "light"]
UNITS = {"temperature": "°C", "humidity": "%", "co2": "ppm", "light": "lux"}
NAMES = {"temperature": "温度", "humidity": "湿度", "co2": "CO₂浓度", "light": "光照强度"}

# ═══════════════════ 数据库 ═══════════════════

def init_db():
    with sqlite3.connect(DB) as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY, ts TEXT, zone TEXT, type TEXT, val REAL
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY, ts TEXT, op TEXT, detail TEXT, who TEXT DEFAULT 'AI'
            );
        """)

# ═══════════════════ 传感器模拟 ═══════════════════
# 温度/光照 白天高夜间低；湿度与温度反相；CO₂ 夜间略高
# 四个区域有固定偏移，模拟朝向差异

def _sim(zone: str, s: str, t: datetime | None = None) -> float:
    t = t or datetime.now()
    h = t.hour + t.minute / 60                               # 0‑24 小时（浮点）
    z = {"东北": -2, "西北": -1, "东南": 1, "西南": 2}[zone]  # 区域偏移

    if s == "temperature":
        # 正弦峰值在 14 时，谷值在 2 时
        base = 25 + 8 * math.sin((h - 8) * math.pi / 12)
        return round(base + z * 0.5 + random.gauss(0, 0.8), 1)

    if s == "humidity":
        base = 65 - 15 * math.sin((h - 8) * math.pi / 12)
        return round(max(0, min(100, base - z * 1.5 + random.gauss(0, 1.5))), 1)

    if s == "co2":
        base = 400 + 50 * math.cos((h - 2) * math.pi / 12)
        return round(base + z * 5 + random.gauss(0, 8), 1)

    # light — 6:00‑18:00 有光照，正午最强
    raw = max(0, 50000 * math.sin((h - 6) * math.pi / 12)) if 6 <= h <= 18 else 0
    return round(max(0, raw + z * 1000 + random.gauss(0, 1500)))

# ═══════════════════ 工具实现 ═══════════════════

def get_current_sensor_data(zone: str, sensor_type: str) -> dict:
    """获取实时读数并存入数据库"""
    now = datetime.now()
    v = _sim(zone, sensor_type, now)
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO sensor_data VALUES(NULL,?,?,?,?)",
                  (now.isoformat(), zone, sensor_type, v))
    return {"zone": zone, "sensor": NAMES[sensor_type],
            "value": v, "unit": UNITS[sensor_type],
            "time": now.strftime("%Y-%m-%d %H:%M:%S")}


def get_historical_sensor_data(zone: str, sensor_type: str, hours: float) -> dict:
    """生成过去 N 小时的模拟历史数据，自动调节采样间隔"""
    now = datetime.now()
    interval = 30 if hours <= 24 else (60 if hours <= 168 else 180)  # 分钟
    data = []
    for i in range(int(hours * 60 / interval), 0, -1):
        ts = now - timedelta(minutes=i * interval)
        data.append({"time": ts.strftime("%m-%d %H:%M"),
                      "value": _sim(zone, sensor_type, ts)})
    vals = [d["value"] for d in data]
    return {"zone": zone, "sensor": NAMES[sensor_type], "unit": UNITS[sensor_type],
            "period": f"过去{hours}小时", "count": len(data),
            "min": min(vals), "max": max(vals),
            "avg": round(sum(vals) / len(vals), 1),
            "data": data}


def get_zone_overview(zone: str) -> dict:
    """一次性获取某区域所有传感器当前读数"""
    now = datetime.now()
    readings = {}
    with sqlite3.connect(DB) as c:
        for s in SENSORS:
            v = _sim(zone, s, now)
            c.execute("INSERT INTO sensor_data VALUES(NULL,?,?,?,?)",
                      (now.isoformat(), zone, s, v))
            readings[NAMES[s]] = {"value": v, "unit": UNITS[s]}
    return {"zone": zone,
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "readings": readings}


def water_zone(zone: str, amount_liters: float) -> dict:
    """执行浇水并自动写入日志"""
    now = datetime.now()
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO logs VALUES(NULL,?,?,?,?)",
                  (now.isoformat(), "浇水",
                   f"{zone}区域 浇水 {amount_liters}L", "AI"))
    return {"status": "success",
            "message": f"已向{zone}区域浇水 {amount_liters} 升",
            "time": now.strftime("%Y-%m-%d %H:%M:%S")}


def write_log(operation_type: str, details: str) -> dict:
    """手动写入一条日志"""
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO logs VALUES(NULL,?,?,?,?)",
                  (datetime.now().isoformat(), operation_type, details, "AI"))
    return {"status": "success", "message": "日志已写入"}


def read_logs(limit: int = 10, operation_type: str | None = None) -> dict:
    """查询最近的日志，可按类型筛选"""
    with sqlite3.connect(DB) as c:
        if operation_type:
            rows = c.execute(
                "SELECT ts,op,detail,who FROM logs "
                "WHERE op=? ORDER BY id DESC LIMIT ?",
                (operation_type, limit)).fetchall()
        else:
            rows = c.execute(
                "SELECT ts,op,detail,who FROM logs "
                "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"count": len(rows),
            "logs": [{"time": r[0], "type": r[1],
                      "detail": r[2], "operator": r[3]} for r in rows]}

# ═══════════════════ OpenAI Tool 定义 ═══════════════════

def _t(name, desc, props, req=None):
    """快捷构造 tool definition"""
    p = {"type": "object", "properties": props}
    if req:
        p["required"] = req
    return {"type": "function",
            "function": {"name": name, "description": desc, "parameters": p}}

_Z = {"type": "string", "enum": ZONES, "description": "区域：东北/西北/东南/西南"}
_S = {"type": "string", "enum": SENSORS,
      "description": "传感器类型：temperature/humidity/co2/light"}

TOOL_DEFS = [
    _t("get_current_sensor_data",
       "获取指定区域某个传感器的实时数据",
       {"zone": _Z, "sensor_type": _S},
       ["zone", "sensor_type"]),

    _t("get_historical_sensor_data",
       "获取指定区域某个传感器过去 N 小时的历史数据（含最小/最大/平均值）",
       {"zone": _Z, "sensor_type": _S,
        "hours": {"type": "number", "description": "过去多少小时"}},
       ["zone", "sensor_type", "hours"]),

    _t("get_zone_overview",
       "一次性获取指定区域全部传感器（温度/湿度/CO₂/光照）的当前读数",
       {"zone": _Z},
       ["zone"]),

    _t("water_zone",
       "对指定区域进行浇水，需指定水量（升）",
       {"zone": _Z,
        "amount_liters": {"type": "number", "description": "浇水量（升）"}},
       ["zone", "amount_liters"]),

    _t("write_log",
       "向系统日志写入一条操作记录",
       {"operation_type": {"type": "string", "description": "操作类型，如：施肥、巡检、告警"},
        "details":        {"type": "string", "description": "操作详情"}},
       ["operation_type", "details"]),

    _t("read_logs",
       "查询系统操作日志，可按类型筛选",
       {"limit":          {"type": "integer", "description": "返回条数，默认 10"},
        "operation_type": {"type": "string",  "description": "按操作类型筛选（可选）"}}),
]

# ═══════════════════ 统一调度 ═══════════════════

_FN = {f.__name__: f for f in [
    get_current_sensor_data, get_historical_sensor_data,
    get_zone_overview, water_zone, write_log, read_logs,
]}

def call_tool(name: str, args: dict) -> str:
    """按名称执行工具，返回 JSON 字符串"""
    fn = _FN.get(name)
    if not fn:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
    try:
        return json.dumps(fn(**args), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)