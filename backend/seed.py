from app import app
from models import db, User, Subject
from datetime import date, timedelta

with app.app_context():
    print("Creating tables if not present...")
    db.create_all()

    existing = User.query.filter_by(email="student@example.com").first()
    if existing:
        print("Demo user already exists, skipping.")
    else:
        user = User(name="Test Student", email="student@example.com")
        db.session.add(user)
        db.session.commit()

        subjects = [
            {"name": "Mathematics", "difficulty": 5, "importance": 5, "syllabus_size": 10,
             "deadline": date.today() + timedelta(days=7)},
            {"name": "DBMS", "difficulty": 3, "importance": 4, "syllabus_size": 6,
             "deadline": date.today() + timedelta(days=21)},
            {"name": "Operating Systems", "difficulty": 4, "importance": 4, "syllabus_size": 8,
             "deadline": date.today() + timedelta(days=14)},
            {"name": "Python", "difficulty": 2, "importance": 3, "syllabus_size": 4,
             "deadline": date.today() + timedelta(days=30)}
        ]

        for s in subjects:
            subj = Subject(
                user_id=user.id,
                name=s["name"],
                difficulty=s["difficulty"],
                importance=s["importance"],
                syllabus_size=s["syllabus_size"],
                deadline=s["deadline"]
            )
            db.session.add(subj)

        db.session.commit()
        print("Seed data inserted successfully!")
