import os
import datetime as dt
from flask import Flask, jsonify, request

from entries_service.models import db, Entry
from entries_service.config import Config
from common.jwt import require_auth

def _parse_date(value):
    if not value:
        return dt.date.today()
    if isinstance(value, str):
        # oczekujemy formatu YYYY-MM-DD
        try:
            return dt.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD")
    if isinstance(value, (dt.date, dt.datetime)):
        return value if isinstance(value, dt.date) else value.date()
    raise ValueError("invalid date")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.get("/")
    def root():
        return {"service": "entries", "status": "ok", "version": "v1"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/entries")
    @require_auth
    def create_entry():
        data = request.get_json(force=True) or {}
        missing = [k for k in ["steps", "sleep_hours", "calories"] if k not in data]
        if missing:
            return jsonify({"detail": f"missing fields: {', '.join(missing)}"}), 400

        try:
            entry = Entry(
                user_id=int(request.user_id),
                date=_parse_date(data.get("date")),
                steps=int(data["steps"]),
                sleep_hours=float(data["sleep_hours"]),
                calories=int(data["calories"]),
                weight=float(data["weight"]) if data.get("weight") is not None else None,
            )
        except ValueError as e:
            return jsonify({"detail": str(e)}), 400

        db.session.add(entry)
        db.session.commit()

        # Tu w KROKU 3 dołożymy publish EntryCreated.
        return jsonify({
            "id": entry.id,
            "user_id": entry.user_id,
            "date": entry.date.isoformat(),
            "steps": entry.steps,
            "sleep_hours": entry.sleep_hours,
            "calories": entry.calories,
            "weight": entry.weight
        }), 201

    @app.get("/api/v1/entries")
    @require_auth
    def list_entries():
        q = Entry.query.filter_by(user_id=int(request.user_id)).order_by(Entry.id.desc()).all()
        return jsonify([{
            "id": e.id,
            "date": e.date.isoformat(),
            "steps": e.steps,
            "sleep_hours": e.sleep_hours,
            "calories": e.calories,
            "weight": e.weight
        } for e in q])

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8002)), debug=True)
