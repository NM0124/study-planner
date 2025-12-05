import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Timetable
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from scheduler import create_timetable
import json
import traceback
from train_model import train_and_save
from models import SessionHistory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "frontend", "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "frontend", "static")
)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-please-change")
DB_USER = os.environ.get("DB_USER", "studyuser")
DB_PASS = os.environ.get("DB_PASS", "study_pass")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "studyplanner")

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

def record_generated_timetable_as_sessions(user, timetable: dict, subjects_meta: list):

    try:
    
        meta_by_name = {}
        for s in subjects_meta:
            name = str(s.get("name","")).strip()
            if not name:
                continue
            meta_by_name[name] = {
                "difficulty": int(s.get("difficulty") or 3),
                "importance": int(s.get("importance") or 3),
                "syllabus_size": float(s.get("syllabus_size") or 1.0),
                "deadline": s.get("deadline"),
                "task_type": s.get("task_type") or "Other"
            }

        rows = []
    
        for date_str, slots in timetable.items():
        
            try:
                day_date = datetime.fromisoformat(date_str).date()
            except Exception:
                try:
                    day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    day_date = None

            for slot in slots:
                subj_name = slot.get("subject")
                hours = float(slot.get("hours", 0.0) or 0.0)
                if hours <= 0:
                    continue
                meta = meta_by_name.get(subj_name, {})
        
                days_to_deadline = None
                if meta.get("deadline") and day_date:
                    try:
                        dl = datetime.fromisoformat(meta["deadline"]).date()
                    except Exception:
                        try:
                            dl = datetime.strptime(meta["deadline"], "%Y-%m-%d").date()
                        except Exception:
                            dl = None
                    if dl:
                        days_to_deadline = max(0, (dl - day_date).days)

                sh = SessionHistory(
                    user_id = user.id if hasattr(user, "id") else user,
                    subject = subj_name,
                    actual_hours = hours,
                    difficulty = meta.get("difficulty"),
                    importance = meta.get("importance"),
                    syllabus_size = meta.get("syllabus_size"),
                    days_to_deadline = days_to_deadline,
                    task_type = meta.get("task_type")
                )
                rows.append(sh)

        if rows:
            db.session.bulk_save_objects(rows)
            db.session.commit()
            return True, len(rows)
        return False, 0
    except Exception as e:
        db.session.rollback()
        app.logger.error("Failed to record generated timetable sessions: %s", e)
        app.logger.error(traceback.format_exc())
        return False, 0


@app.route("/")
def root():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/dashboard")
@login_required
def dashboard():
    tts = Timetable.query.filter_by(user_id=current_user.id).order_by(Timetable.created_at.desc()).all()
    items = []
    for t in tts:
        items.append({
            "id": t.id,
            "title": t.title or f"Timetable #{t.id}",
            "created_at": t.created_at.isoformat(),
        })
    return render_template("dashboard.html", timetables=items, name=current_user.name)


@app.route("/planner")
@login_required
def planner():
    return render_template("planner.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    data = request.form
    name = data.get("name","").strip()
    email = data.get("email","").strip().lower()
    password = data.get("password","")
    if not name or not email or not password:
        flash("Please fill all fields","danger")
        return redirect(url_for("register"))
    if User.query.filter_by(email=email).first():
        flash("Email already registered","danger")
        return redirect(url_for("register"))
    hashed = generate_password_hash(password)
    user = User(name=name,email=email,password_hash=hashed)
    db.session.add(user); db.session.commit()
    flash("Account created. Please log in.","success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    data = request.form
    email = data.get("email","").strip().lower()
    password = data.get("password","")
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid credentials","danger")
        return redirect(url_for("login"))
    login_user(user)
    flash("Logged in","success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out","info")
    return redirect(url_for("login"))

@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    body = request.get_json() or {}
    subjects = body.get("subjects", [])
    daily_hours = float(body.get("daily_hours", 5))
    schedule_type = body.get("schedule_type", "daily")
    raw_unavail = body.get("unavailable_dates", [])
    unavailable_dates = []
    for d in raw_unavail:
        try:
            dt = datetime.fromisoformat(d).date()
            dt = dt + timedelta(days=1)
            unavailable_dates.append(dt.isoformat())
        except:
            unavailable_dates.append(d)
    variant = body.get("variant", None)
    limit_weekends = bool(body.get("limit_weekends", False))

    for s in subjects:
        if not s.get("deadline"):
            return jsonify({"error":"deadline missing for one or more subjects"}), 400

    timetable = create_timetable(
        subjects=subjects,
        daily_hours=daily_hours,
        schedule_type=schedule_type,
        unavailable_dates=unavailable_dates,
        variant=variant,
        limit_weekends=limit_weekends
    )

    try:
        recorded, nrows = record_generated_timetable_as_sessions(current_user, timetable, subjects)
        app.logger.info("AutoML: recorded %s generated session rows", nrows if recorded else 0)
    except Exception as e:
        app.logger.error("AutoML: failed to record generated sessions: %s", e)
        app.logger.error(traceback.format_exc())

    try:
        train_path = train_and_save(app)
        app.logger.info("AutoML: trained model at %s", train_path)
        model_trained = True
    except Exception as e:
        app.logger.error("AutoML: training failed: %s", e)
        app.logger.error(traceback.format_exc())
        model_trained = False

    return jsonify({"timetable": timetable, "variant": variant, "model_trained": model_trained})


@app.route("/api/reschedule", methods=["POST"])
@login_required
def api_reschedule():
    body = request.get_json() or {}
    subjects = body.get("subjects", [])
    daily_hours = float(body.get("daily_hours", 5))
    schedule_type = body.get("schedule_type", "daily")
    raw_unavail = body.get("unavailable_dates", [])
    unavailable_dates = []
    for d in raw_unavail:
        try:
            dt = datetime.fromisoformat(d).date()
            dt = dt + timedelta(days=1)
            unavailable_dates.append(dt.isoformat())
        except:
            unavailable_dates.append(d)
    limit_weekends = bool(body.get("limit_weekends", False))

    for s in subjects:
        if not s.get("deadline"):
            return jsonify({"error":"deadline missing for one or more subjects"}), 400

    variant = int(datetime.now().timestamp() * 1000)
    timetable = create_timetable(
        subjects=subjects,
        daily_hours=daily_hours,
        schedule_type=schedule_type,
        unavailable_dates=unavailable_dates,
        variant=variant,
        limit_weekends=limit_weekends
    )

    try:
        recorded, nrows = record_generated_timetable_as_sessions(current_user, timetable, subjects)
        app.logger.info("AutoML (reschedule): recorded %s generated session rows", nrows if recorded else 0)
    except Exception as e:
        app.logger.error("AutoML (reschedule): failed to record generated sessions: %s", e)
        app.logger.error(traceback.format_exc())

    try:
        train_path = train_and_save(app)
        app.logger.info("AutoML (reschedule): trained model at %s", train_path)
        model_trained = True
    except Exception as e:
        app.logger.error("AutoML (reschedule): training failed: %s", e)
        app.logger.error(traceback.format_exc())
        model_trained = False

    return jsonify({"timetable": timetable, "variant": variant, "model_trained": model_trained})


@app.route("/api/save_timetable", methods=["POST"])
@login_required
def api_save_timetable():
    body = request.get_json() or {}
    title = body.get("title", "")
    timetable_data = body.get("timetable") or {}
    variant = str(body.get("variant", ""))
    tt = Timetable(user_id=current_user.id, title=title, variant=variant, data=timetable_data)
    db.session.add(tt); db.session.commit()
    return jsonify({"status":"ok","timetable_id": tt.id})


@app.route("/api/load_timetable/<int:tt_id>", methods=["GET"])
@login_required
def api_load_timetable(tt_id):
    tt = Timetable.query.filter_by(id=tt_id, user_id=current_user.id).first_or_404()
    return jsonify({"timetable": tt.data, "title": tt.title, "created_at": tt.created_at.isoformat()})


@app.route("/api/delete_timetable/<int:tt_id>", methods=["POST"])
@login_required
def api_delete_timetable(tt_id):
    tt = Timetable.query.filter_by(id=tt_id, user_id=current_user.id).first()
    if not tt:
        return jsonify({"status":"error","message":"not found"}), 404
    db.session.delete(tt); db.session.commit()
    return jsonify({"status":"ok"})

import os, joblib
from train_model import train_and_save
from models import SessionHistory

MODEL_FILE = os.path.join(os.path.dirname(__file__), "ml_model.joblib")

@app.route("/api/record_session", methods=["POST"])
@login_required
def api_record_session():
    """
    Record a study session (to build training data).
    Expected JSON:
    {
      "subject": "Mathematics",
      "actual_hours": 1.25,
      "difficulty": 4,
      "importance": 5,
      "syllabus_size": 10,
      "days_to_deadline": 7,
      "task_type": "Exam"
    }
    """
    body = request.get_json() or {}
    subject = body.get("subject")
    actual_hours = float(body.get("actual_hours", 0))
    if not subject or actual_hours <= 0:
        return jsonify({"status":"error","message":"subject and positive actual_hours required"}), 400

    sh = SessionHistory(
        user_id=current_user.id,
        subject=subject,
        actual_hours=actual_hours,
        difficulty=body.get("difficulty"),
        importance=body.get("importance"),
        syllabus_size=body.get("syllabus_size"),
        days_to_deadline=body.get("days_to_deadline"),
        task_type=body.get("task_type")
    )
    db.session.add(sh)
    db.session.commit()
    return jsonify({"status":"ok","id": sh.id})

@app.route("/api/train_model", methods=["POST"])
@login_required
def api_train_model():
    """
    Trigger model training. You may want to protect this endpoint (admin-only)
    in production. For now it's available to logged-in users.
    """
    try:
        path = train_and_save(app)
        return jsonify({"status":"ok","model_path": path})
    except Exception as e:
        return jsonify({"status":"error","message": str(e)}), 500

@app.route("/delete_timetable/<int:tid>")
@login_required
def delete_timetable(tid):
    tt = Timetable.query.filter_by(id=tid, user_id=current_user.id).first()
    if not tt:
        flash("Timetable not found", "danger")
        return redirect("/dashboard")

    db.session.delete(tt)
    db.session.commit()
    flash("Timetable deleted", "success")
    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True)
