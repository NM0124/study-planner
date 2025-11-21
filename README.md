# AI Study Planner (Flask + MySQL + Docker)

Full project (ZIP-ready) for the AI Study Planner web app.
Includes both local development instructions and a Dockerized stack.

---

![Uploading image.png…]()

## Quick choices
- Local run (Python + system MySQL) — easy for testing
- Docker run (MySQL + phpMyAdmin + Flask) — recommended for reproducible dev

---

## 1) Prepare
1. Copy `.env.example` -> `.env` and adjust values if needed.
2. If using Docker, keep DB_HOST as `mysql` in .env (that's the docker service name).
3. If using local MySQL, set DB_HOST to `localhost` and create the database manually.

---

## 2) Local setup (without Docker)
1. Create MySQL database:
   ```sql
   CREATE DATABASE studyplanner;
   CREATE USER 'studyuser'@'localhost' IDENTIFIED BY 'study_pass';
   GRANT ALL PRIVILEGES ON studyplanner.* TO 'studyuser'@'localhost';
   FLUSH PRIVILEGES;
