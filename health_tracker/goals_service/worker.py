import os
from flask import Flask
from goals_service.config import Config
from goals_service.models import db, Goal
from common.events import consume, publish

def create_worker_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def on_entry_created(evt: dict):
    try:
        user_id = int(evt.get("user_id"))
        steps = int(evt.get("steps", 0))
    except Exception:
        print("goals_worker: invalid event payload:", evt)
        return

    # znajdź nieosiągnięte cele typu "steps"
    goals = Goal.query.filter_by(user_id=user_id, type="steps", is_achieved=False).all()
    if not goals:
        print(f"goals_worker: no pending goals for user={user_id}")
        return

    updated = False
    for g in goals:
        if steps >= g.target_value:
            g.is_achieved = True
            db.session.commit()
            updated = True
            print(f"goals_worker: goal {g.id} achieved for user={user_id} (target={g.target_value})")
            # wyślij event dalej
            publish("goal.achieved", {
                "user_id": user_id,
                "goal_id": g.id,
                "type": g.type,
                "target_value": g.target_value,
            })

    if not updated:
        print(f"goals_worker: entry did not achieve any goal for user={user_id}")

if __name__ == "__main__":
    app = create_worker_app()
    with app.app_context():
        db.create_all()  # na wszelki wypadek
        print("goals_worker: consuming from RabbitMQ (binding: entry.created)")
        consume(queue="goals", binding_keys=["entry.created"], handler=on_entry_created)
