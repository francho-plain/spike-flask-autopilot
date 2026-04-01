import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, render_template, url_for

from repository.csv_store import CsvSessionStore
from services.time_tracking import build_weeks_view


def create_app() -> Flask:
    app = Flask(__name__)
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
            weeks=weeks,
            has_open_session=open_session is not None,
            open_since=(
                datetime.fromisoformat(open_session["start_at"])
                .astimezone(ZoneInfo(app.config["TIMEZONE"]))
                .strftime("%H:%M")
                if open_session
                else None
            ),
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
            store.end_open_session(now_utc)
            flash("Salida registrada", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
