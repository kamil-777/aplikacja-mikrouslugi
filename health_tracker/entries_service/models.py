from flask_sqlalchemy import SQLAlchemy
import datetime as dt

db = SQLAlchemy()

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=dt.date.today)
    steps = db.Column(db.Integer, nullable=False)
    sleep_hours = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float)
