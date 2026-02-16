"""传感器模拟引擎（时间趋势 + 区域偏移）& 后台定时采集线程"""

import math, random, sqlite3, threading
from datetime import datetime
from typing import Optional

from ._constants import DB_PATH, ZONES, SENSORS

# ═══════════════════ 模拟函数 ═══════════════════

_ZONE_OFFSET = {"东北": -2, "西北": -1, "东南": 1, "西南": 2}


def sim(zone: str, sensor: str, t: Optional[datetime] = None) -> float:
    """根据时间 + 区域生成仿真读数"""
    t = t or datetime.now()
    h = t.hour + t.minute / 60
    z = _ZONE_OFFSET[zone]

    if sensor == "temperature":
        base = 25 + 8 * math.sin((h - 8) * math.pi / 12)
        return round(base + z * 0.5 + random.gauss(0, 0.8), 1)

    if sensor == "humidity":
        base = 65 - 15 * math.sin((h - 8) * math.pi / 12)
        return round(max(0, min(100, base - z * 1.5 + random.gauss(0, 1.5))), 1)

    if sensor == "co2":
        base = 400 + 50 * math.cos((h - 2) * math.pi / 12)
        return round(base + z * 5 + random.gauss(0, 8), 1)

    # light
    raw = max(0, 50000 * math.sin((h - 6) * math.pi / 12)) if 6 <= h <= 18 else 0
    return round(max(0, raw + z * 1000 + random.gauss(0, 1500)))


# ═══════════════════ 后台采集线程 ═══════════════════

_started = False
_lock    = threading.Lock()
_stop    = threading.Event()


def _loop(interval: float):
    while not _stop.is_set():
        now = datetime.now()
        ts  = now.isoformat()
        rows = [(ts, z, s, sim(z, s, now)) for z in ZONES for s in SENSORS]
        try:
            with sqlite3.connect(DB_PATH) as c:
                c.executemany("INSERT INTO sensor_data VALUES(NULL,?,?,?,?)", rows)
        except Exception as e:
            print(f"[采集] 写入失败: {e}")
        _stop.wait(timeout=interval)


def start_collector(interval: float = 30.0):
    global _started
    with _lock:
        if _started:
            return
        _stop.clear()
        threading.Thread(target=_loop, args=(interval,),
                         name="SensorCollector", daemon=True).start()
        _started = True
        print(f"[采集] 已启动 (间隔 {interval}s, 每轮 {len(ZONES)*len(SENSORS)} 条)")


def stop_collector():
    global _started
    with _lock:
        if not _started:
            return
        _stop.set()
        _started = False
        print("[采集] 已停止")


def is_collector_running() -> bool:
    return _started