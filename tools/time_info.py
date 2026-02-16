"""工具：获取当前时间 & 农事建议"""

from datetime import datetime

from ._registry import ToolRegistry

_PERIODS = [
    ( 5,  7, "清晨",     "适合巡田、查看露水情况"),
    ( 7,  9, "早晨",     "适合施肥、喷药（风小、蒸发少）"),
    ( 9, 11, "上午",     "光照渐强，注意观察作物状态"),
    (11, 13, "中午",     "高温时段，避免浇水和喷药"),
    (13, 15, "下午早段", "温度最高，注意遮阳和通风"),
    (15, 17, "下午",     "温度回落，可恢复田间作业"),
    (17, 19, "傍晚",     "适合浇水（蒸发少、夜间吸收好）"),
    (19, 21, "晚间",     "检查灌溉设备和夜间防护"),
]

_SEASONS = [
    ({3, 4, 5},   "春季", "春耕播种期，注意倒春寒"),
    ({6, 7, 8},   "夏季", "生长旺季，注意防暑、防涝、病虫害"),
    ({9, 10, 11}, "秋季", "收获季节，注意适时采收"),
    ({12, 1, 2},  "冬季", "休耕/大棚管理期，注意防冻保温"),
]

_WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@ToolRegistry.register(
    name="get_current_time",
    display_name="🕐 获取当前时间",
    description=(
        "获取当前日期、时间、星期、季节，以及对应的农事建议提示。"
        "当用户询问现在几点、今天几号、什么季节等时间相关问题时使用。"
    ),
    parameters={
        "timezone": {
            "type": "string",
            "description": "时区名称，默认 Asia/Shanghai",
            "default": "Asia/Shanghai",
        },
    },
)
def get_current_time(timezone: str = "Asia/Shanghai") -> dict:
    now = datetime.now()
    h, m = now.hour, now.month

    period, farm_hint = "夜间", "作物休息期，注意低温防护"
    for lo, hi, p, hint in _PERIODS:
        if lo <= h < hi:
            period, farm_hint = p, hint
            break

    season, season_hint = "冬季", "休耕/大棚管理期，注意防冻保温"
    for months, s, sh in _SEASONS:
        if m in months:
            season, season_hint = s, sh
            break

    return {
        "date":          now.strftime("%Y年%m月%d日"),
        "time":          now.strftime("%H:%M:%S"),
        "weekday":       _WEEKDAYS[now.weekday()],
        "period":        period,
        "season":        season,
        "datetime_full": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp":     int(now.timestamp()),
        "farm_hint":     farm_hint,
        "season_hint":   season_hint,
        "timezone":      timezone,
    }