# -*- coding: utf-8 -*-
from flask import Flask
from notifications_service.config import Config
from notifications_service.models import db, Notification
from common.events import consume

def create_worker_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def on_goal_achieved(evt: dict):
    try:
        user_id = int(evt["user_id"])
        target_value = evt.get("target_value")
        gtype = evt.get("type")
    except Exception:
        print("notifications_worker: invalid event payload:", evt)
        return

    msg = f"Brawo! Osiagnales cel: {target_value} {gtype}."
    n = Notification(user_id=user_id, message=msg)
    db.session.add(n)
    db.session.commit()
    print(f"notifications_worker: created notification for user={user_id}")

if __name__ == "__main__":
    app = create_worker_app()
    with app.app_context():
        db.create_all()
        print("notifications_worker: consuming from RabbitMQ (binding: goal.achieved)")
        consume(queue="notifications", binding_keys=["goal.achieved"], handler=on_goal_achieved)
