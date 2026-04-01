from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from zoneinfo import ZoneInfo

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
        f"({week_start.isocalendar().year})"
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

        if week_key not in grouped:
            grouped[week_key] = {
                "week_key": week_key,
                "week_start": week_start,
                "week_title": _week_title(week_start),
                "total": timedelta(),
                "items": [],
            }

        grouped[week_key]["total"] += duration
        grouped[week_key]["items"].append(
            {
                "day_label": _day_label(start_local),
                "start": start_local.strftime("%H:%M"),
                "end": end_local.strftime("%H:%M") if session["end_at"] else "En curso",
                "duration": _format_duration(duration),
                "is_open": not bool(session["end_at"]),
            }
        )

    weeks: List[Dict[str, object]] = []
    for week in sorted(grouped.values(), key=lambda value: value["week_start"], reverse=True):
        items = sorted(week["items"], key=lambda row: row["start"], reverse=True)
        weeks.append(
            {
                "week_key": week["week_key"],
                "week_title": week["week_title"],
                "total": _format_duration(week["total"]),
                "items": items,
            }
        )

    return weeks
