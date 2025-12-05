import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from models import db, SessionHistory
from sqlalchemy import create_engine
from flask import current_app

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model.joblib")

def load_session_dataframe(app):
    with app.app_context():
        sessions = SessionHistory.query.all()
        rows = []
        for s in sessions:
            rows.append({
                "subject": s.subject,
                "actual_hours": s.actual_hours,
                "difficulty": s.difficulty or 3,
                "importance": s.importance or 3,
                "syllabus_size": s.syllabus_size or 1.0,
                "days_to_deadline": s.days_to_deadline if s.days_to_deadline is not None else 30,
                "task_type": s.task_type or "Other"
            })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        return df

def featurize(df):
    df = df.copy()
    task_df = pd.get_dummies(df["task_type"], prefix="task")
    X = pd.concat([
        df[["difficulty", "importance", "syllabus_size", "days_to_deadline"]],
        task_df
    ], axis=1)
    y = df["actual_hours"]
    return X, y

def train_and_save(app):
    df = load_session_dataframe(app)
    if df.empty:
        raise RuntimeError("No session history available for training.")

    X, y = featurize(df)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump({
        "model": model,
        "columns": X.columns.tolist()
    }, MODEL_PATH)
    return MODEL_PATH
