import os
from flask import Flask, jsonify, request
from goals_service.config import Config
from goals_service.models import db, Goal
from common.jwt import require_auth

ALLOWED_TYPES = {"steps", "calories", "sleep", "weight"}

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.get("/")
    def root():
        return {"service": "goals", "status": "ok", "version": "v1"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/goals")
    @require_auth
    def create_goal():
        data = request.get_json(force=True) or {}
        gtype = data.get("type")
        target = data.get("target_value")

        if gtype not in ALLOWED_TYPES:
            return jsonify({"detail": f"type must be one of {sorted(ALLOWED_TYPES)}"}), 400
        try:
            target = float(target)
        except (TypeError, ValueError):
            return jsonify({"detail": "target_value must be a number"}), 400

        goal = Goal(user_id=int(request.user_id), type=gtype, target_value=target)
        db.session.add(goal)
        db.session.commit()
        return jsonify({
            "id": goal.id, "type": goal.type, "target_value": goal.target_value,
            "is_achieved": goal.is_achieved
        }), 201

    @app.get("/api/v1/goals")
    @require_auth
    def list_goals():
        goals = Goal.query.filter_by(user_id=int(request.user_id)).order_by(Goal.id.desc()).all()
        return jsonify([{
            "id": g.id, "type": g.type, "target_value": g.target_value,
            "is_achieved": g.is_achieved, "created_at": g.created_at.isoformat()
        } for g in goals])

    @app.delete("/api/v1/goals/<int:goal_id>")
    @require_auth
    def delete_goal(goal_id: int):
        g = Goal.query.filter_by(id=goal_id, user_id=int(request.user_id)).first()
        if not g:
            return jsonify({"detail": "goal not found"}), 404
        db.session.delete(g)
        db.session.commit()
        return "", 204

    # (opcjonalnie) Ręczny toggle osiągnięcia – tylko na czas dev/testów
    @app.patch("/api/v1/goals/<int:goal_id>")
    @require_auth
    def patch_goal(goal_id: int):
        g = Goal.query.filter_by(id=goal_id, user_id=int(request.user_id)).first()
        if not g:
            return jsonify({"detail": "goal not found"}), 404
        payload = request.get_json(force=True) or {}
        if "is_achieved" in payload:
            g.is_achieved = bool(payload["is_achieved"])
            db.session.commit()
        return jsonify({"id": g.id, "is_achieved": g.is_achieved})

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8003)), debug=True)
