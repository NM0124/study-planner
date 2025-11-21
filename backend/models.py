# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.id)

class Timetable(db.Model):
    __tablename__ = "timetables"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    variant = db.Column(db.String(64), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    data = db.Column(db.JSON, nullable=False)

    user = db.relationship("User", backref="timetables")

class SessionHistory(db.Model):
    """
    Stores actual study session data used for ML training.
    Each record represents one session (a continuous study of a subject).
    """
    __tablename__ = "session_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    actual_hours = db.Column(db.Float, nullable=False)     # what user actually spent
    difficulty = db.Column(db.Integer, nullable=True)
    importance = db.Column(db.Integer, nullable=True)
    syllabus_size = db.Column(db.Float, nullable=True)
    days_to_deadline = db.Column(db.Integer, nullable=True)
    task_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="sessions")