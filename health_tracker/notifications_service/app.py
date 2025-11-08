import os
from flask import Flask, jsonify, request
from notifications_service.config import Config
from notifications_service.models import db, Notification
from common.jwt import require_auth

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.get("/")
    def root():
        return {"service": "notifications", "status": "ok", "version": "v1"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/notifications")
    @require_auth
    def list_notifications():
        items = Notification.query.filter_by(user_id=int(request.user_id))\
                                  .order_by(Notification.created_at.desc()).all()
        return jsonify([{
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        } for n in items])

    @app.patch("/api/v1/notifications/<int:n_id>")
    @require_auth
    def patch_notification(n_id: int):
        n = Notification.query.filter_by(id=n_id, user_id=int(request.user_id)).first()
        if not n:
            return jsonify({"detail": "not found"}), 404
        payload = request.get_json(force=True) or {}
        if "is_read" in payload:
            n.is_read = bool(payload["is_read"])
            db.session.commit()
        return jsonify({"id": n.id, "is_read": n.is_read})

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8004)), debug=True)
