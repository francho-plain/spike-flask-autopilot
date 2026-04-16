import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, render_template, request, url_for

from repository.csv_store import CsvSessionStore
from services.time_tracking import DAILY_TARGET, WEEKLY_TARGET, build_weeks_view


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["PAGE_TITLE"] = os.getenv("PAGE_TITLE", "Time tracking")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["TIMEZONE"] = os.getenv("TZ", "Europe/Madrid")
    app.config["CSV_PATH"] = os.getenv("CSV_PATH", "data/sessions.csv")

    store = CsvSessionStore(app.config["CSV_PATH"])

    @app.get("/")
    def index():
        sessions = store.get_all_sessions()
        weeks = build_weeks_view(sessions, app.config["TIMEZONE"])
        open_session = store.get_open_session()
        return render_template(
            "index.html",
            page_title=app.config["PAGE_TITLE"],
            weeks=weeks,
            has_open_session=open_session is not None,
            open_since=(
                datetime.fromisoformat(open_session["start_at"])
                .astimezone(ZoneInfo(app.config["TIMEZONE"]))
                .strftime("%H:%M")
                if open_session
                else None
            ),
            open_start_iso=(open_session["start_at"] if open_session else None),
            weekly_target_s=int(WEEKLY_TARGET.total_seconds()),
            daily_target_s=int(DAILY_TARGET.total_seconds()),
        )

    @app.post("/enter")
    def enter():
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            store.start_session(now_utc)
            flash("Entrada registrada", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    @app.post("/leave")
    def leave():
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            corrected_hours_raw = request.form.get("corrected_hours", "").strip()
            corrected_minutes_raw = request.form.get("corrected_minutes", "").strip()
            if corrected_hours_raw or corrected_minutes_raw:
                open_session = store.get_open_session()
                if open_session is None:
                    raise ValueError("No hay sesión abierta para cerrar")

                try:
                    corrected_hours = int(corrected_hours_raw or "0")
                    corrected_minutes = int(corrected_minutes_raw or "0")
                except ValueError as exc:
                    raise ValueError("El ajuste de horas o minutos no es válido") from exc

                if corrected_hours < 0 or corrected_minutes < 0 or corrected_minutes > 59:
                    raise ValueError("El ajuste de horas o minutos no es válido")

                total_seconds = corrected_hours * 3600 + corrected_minutes * 60
                if total_seconds <= 0:
                    raise ValueError("El ajuste debe ser mayor que cero")

                start_at = datetime.fromisoformat(open_session["start_at"])
                corrected_end_at = start_at + timedelta(seconds=total_seconds)

                if corrected_end_at > datetime.now(timezone.utc):
                    raise ValueError("El ajuste no puede superar la hora actual")

                store.end_open_session(corrected_end_at.isoformat())
            else:
                store.end_open_session(now_utc)
            flash("Salida registrada", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
