# AI Study Planner 

An intelligent, ML-backed web application built for students to intelligently organize, automate, and construct customized study timetables. Built on top of Python, Flask, and scikit-learn, the application dynamically breaks down daily study hours in correlation to a subject's unique difficulty, importance, size, and deadline urgency.

## Core Features 
* **Automated Scheduling Engine**: Generates adaptive layouts accounting for daily hour limits, weekends off, or specific unavailable blackout dates.
* **Intelligent Prediction (ML)**: Uses a built-in `RandomForestRegressor` trained on rolling user-recorded data locally to assign the perfect amount of time to specific tasks.
* **Modern Interface**: Dual-themed (Pink & Blue) responsive 3D card layout, with CSS glassmorphism, native color-coded Calendar legends, and `Chart.js` integrations displaying free time ratios.
* **Dashboard Utilities**: PDF generation via `jsPDF`, saveable configurations, and dynamic session rescheduling.

## Built With 
* **Backend**: Python 3.14+, Flask
* **Database / Authentication**: Flask-SQLAlchemy (default SQLite), Flask-Login
* **Machine Learning**: Scikit-Learn, Pandas, Joblib
* **Frontend**: Vanilla HTML/JS, CSS3, Chart.js, Flatpickr

## Running Locally 

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your operating system.
```bash
python --version
```

### 2. Setup the Environment
Clone the repository and jump into the application folder:
```bash
git clone https://github.com/NM0124/study-planner.git
cd study-planner/backend
```

It's highly recommended to utilize a virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Architecture
The app seamlessly generates a fallback `studyplanner.db` locally—meaning no painful MySQL service configurations are instantly required.

```bash
python app.py
```

Host successfully initiated? Click properties around and test scheduling rules out at **http://127.0.0.1:5000**

## Project Structure 
- `backend/app.py`: Standard Flask entrypoint handling HTTP routing and model mapping.
- `backend/models.py`: SQLAlchemy schema.
- `backend/scheduler.py`: The brain that iteratively solves constraints and invokes the ML predictions.
- `backend/train_model.py`: Automates dataset loading mapped from user interaction points towards the `.joblib` model.
- `frontend/`: Stores templated HTML screens, customized UI themes (`style.css`), and main JS bindings.
