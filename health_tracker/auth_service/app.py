from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import os

from common.jwt import create_access_token, require_auth
from .models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object("auth_service.config.Config")  # auth_service == nazwa pakietu (folderu)

    db.init_app(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Rejestracja
    @app.post("/api/v1/auth/register")
    def register():
        data = request.get_json(force=True)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return jsonify({"detail": "username, email, password required"}), 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({"detail": "user with username or email already exists"}), 409

        u = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(u); db.session.commit()
        return jsonify({"id": u.id, "username": u.username, "email": u.email}), 201

    # Logowanie → JWT
    @app.post("/api/v1/auth/login")
    def login():
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"detail": "username and password required"}), 400

        u = User.query.filter_by(username=username).first()
        if not u or not check_password_hash(u.password_hash, password):
            return jsonify({"detail": "invalid credentials"}), 401

        token = create_access_token(u.id, expires_minutes=30)
        return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": 1800})

    # Przykładowy endpoint wymagający autoryzacji
    @app.get("/api/v1/users/me")
    @require_auth
    def me():
        u = User.query.get_or_404(int(request.user_id))
        return jsonify({"id": u.id, "username": u.username, "email": u.email})

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8001)), debug=True)
