from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from zoneinfo import ZoneInfo

DAILY_TARGET = timedelta(hours=7)
WEEKLY_TARGET = DAILY_TARGET * 5

SPANISH_WEEKDAYS = [
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
]

SPANISH_MONTHS = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def _format_duration(duration: timedelta) -> str:
    total_seconds = max(int(duration.total_seconds()), 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}h"


def _localize(iso_value: str, timezone_name: str) -> datetime:
    dt = datetime.fromisoformat(iso_value)
    return dt.astimezone(ZoneInfo(timezone_name))


def _day_label(dt: datetime) -> str:
    weekday = SPANISH_WEEKDAYS[dt.weekday()]
    month = SPANISH_MONTHS[dt.month - 1]
    return f"{weekday}, {dt.day} {month}"


def _week_title(week_start: datetime) -> str:
    week_end = week_start + timedelta(days=6)
    start_month = SPANISH_MONTHS[week_start.month - 1]
    end_month = SPANISH_MONTHS[week_end.month - 1]
    if week_start.month == week_end.month:
        return f"Semana {week_start.day}-{week_end.day} {start_month} ({week_start.isocalendar().year})"
    return (
        f"Semana {week_start.day} {start_month} - {week_end.day} {end_month} "
    )


def build_weeks_view(sessions: List[Dict[str, str]], timezone_name: str) -> List[Dict[str, object]]:
    now_local = datetime.now(ZoneInfo(timezone_name))
    grouped: Dict[str, Dict[str, object]] = {}

    for session in sessions:
        start_local = _localize(session["start_at"], timezone_name)
        end_local = (
            _localize(session["end_at"], timezone_name) if session["end_at"] else now_local
        )
        duration = end_local - start_local

        week_start = (start_local - timedelta(days=start_local.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_key = f"{week_start.isocalendar().year}-W{week_start.isocalendar().week:02d}"
        day_key = start_local.strftime("%Y-%m-%d")

        if week_key not in grouped:
            grouped[week_key] = {
                "week_key": week_key,
                "week_start": week_start,
                "week_title": _week_title(week_start),
                "total": timedelta(),
                "days": {},
            }

        days = grouped[week_key]["days"]
        if day_key not in days:
            days[day_key] = {
                "day_label": _day_label(start_local),
                "day_date": start_local.replace(hour=0, minute=0, second=0, microsecond=0),
                "total": timedelta(),
                "items": [],
            }

        grouped[week_key]["total"] += duration
        days[day_key]["total"] += duration
        days[day_key]["items"].append(
            {
                "start": start_local.strftime("%H:%M"),
                "end": end_local.strftime("%H:%M") if session["end_at"] else "En curso",
                "duration": _format_duration(duration),
                "is_open": not bool(session["end_at"]),
                "raw_start": start_local,
            }
        )

    weeks: List[Dict[str, object]] = []
    for week in sorted(grouped.values(), key=lambda value: value["week_start"], reverse=True):
        week_total: timedelta = week["total"]
        days = sorted(week["days"].values(), key=lambda d: d["day_date"], reverse=False)
        week_has_open = False
        week_open_duration: timedelta = timedelta()
        for day in days:
            day_total: timedelta = day["total"]
            day_has_open = any(item["is_open"] for item in day["items"])
            day_open_duration = timedelta()
            if day_has_open:
                week_has_open = True
                open_item = next(item for item in day["items"] if item["is_open"])
                day_open_duration = now_local - open_item["raw_start"]
                week_open_duration = day_open_duration
            day_closed_s = int((day_total - day_open_duration).total_seconds())
            day["total"] = _format_duration(day_total)
            day["closed_seconds"] = day_closed_s
            day["day_ok"] = day_total >= DAILY_TARGET
            day["has_open"] = day_has_open
            day["items"] = sorted(day["items"], key=lambda row: row["raw_start"])
        week_closed_s = int((week_total - week_open_duration).total_seconds())
        weeks.append(
            {
                "week_key": week["week_key"],
                "week_title": week["week_title"],
                "total": _format_duration(week_total),
                "closed_seconds": week_closed_s,
                "week_ok": week_total >= WEEKLY_TARGET,
                "has_open": week_has_open,
                "days": days,
            }
        )

    return weeks
