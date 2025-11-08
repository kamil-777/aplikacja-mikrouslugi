import os, functools, datetime as dt, jwt
from flask import request, jsonify

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_please")
JWT_ALGO = "HS256"

def create_access_token(sub: int, expires_minutes: int = 30) -> str:
    now = dt.datetime.utcnow()
    payload = {"sub": sub, "iat": now, "exp": now + dt.timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])

def require_auth(view):
    """Dekorator do zabezpieczania endpointów — ustawia request.user_id."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"detail": "Missing Bearer token"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except Exception:
            return jsonify({"detail": "Invalid or expired token"}), 401
        request.user_id = int(payload["sub"])
        return view(*args, **kwargs)
    return wrapper
