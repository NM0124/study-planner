# 📘 **PROJECT REPORT**

### **Title: Study Planner with Machine Learning**

---

# **1. Introduction**

“**Study Planner with Machine Learning**” is a full-stack intelligent timetable generator that helps students automatically create optimized study schedules.

It uses:

* User inputs (subjects, difficulty, importance, deadlines)
* Unavailable days
* ML-based predictions for study hours
* Smart heuristic scheduler
* Graphs & calendar visualizations
* Smart Rescheduling
* User login system + saved timetables
* PDF Export
* Light/Dark Theme

The goal is to eliminate manual planning and allow students to focus on studying instead of organizing.

---

# **2. Objectives**

The project aims to:

* Automate timetable generation
* Prioritize subjects smartly before deadlines
* Include ML for predictive study-hour allocation
* Provide a clean, interactive, modern UI
* Allow users to save, load, delete timetables
* Visualize workload using charts & calendars
* Prevent scheduling on unavailable days
* Adapt study sessions based on units remaining

---

# **3. Tech Stack Used**

Below is the technology list used in this project:

---

## **Frontend**

| Technology                  | Purpose                                            |
| --------------------------- | -------------------------------------------------- |
| **HTML5**                   | Base UI structure                                  |
| **CSS3**                    | Styling, dark/light theme, center layout, 3D cards |
| **JavaScript (Vanilla JS)** | Form handling, API calls, UI logic                 |
| **Chart.js**                | Bar & line charts for study vs free time           |
| **Flatpickr.js**            | Multi-date unavailable day selector                |
| **jsPDF**                   | Export styled timetable PDF                        |
| **Flexbox + 3D Cards**      | Modern centered UI                                 |

---

## **Backend**

| Technology           | Purpose                         |
| -------------------- | ------------------------------- |
| **Python 3 (Flask)** | Backend server, API routes      |
| **scikit-learn**     | Machine learning model          |
| **Joblib**           | Model saving/loading            |
| **MySQL**            | Persistent database storage     |
| **SQLAlchemy ORM**   | Models and database interaction |
| **JWT / Sessions**   | Login authentication system     |

---

## **Machine Learning**

| Component                        | Purpose                                                              |
| -------------------------------- | -------------------------------------------------------------------- |
| **Regression Model**             | Predicts study hours per unit                                        |
| **Auto-train on each timetable** | Model improves automatically                                         |
| **Features used**                | Difficulty, Importance, Units, Task Type (one-hot), Days to deadline |
| **Heuristics + ML Hybrid**       | Ensures accurate & stable schedule                                   |

---

# **4. System Architecture**

This project follows a clean 3-layer architecture:

### **1. Frontend UI**

* Inputs subjects
* Multi-date unavailable picker
* Displays timetable
* Line/Bar graphs
* Calendar visualization
* PDF Export
* Theme toggle
* Save/Delete schedule

### **2. Flask Backend**

* Receives user input
* Runs scheduler with ML
* Saves/loads timetables
* User login system

### **3. Machine Learning Layer**

* Learns from saved timetables
* Predicts required hours per unit
* Improves automatically

---

# **5. Features (Final Delivered)**

### ✅ **1. Login System (Register, Login, Dashboard, Logout)**

* Secure password hashing
* Save/load/delete timetables
* Personalized dashboard

### ✅ **2. Timetable Generation**

Based on:

* Difficulty
* Importance
* Deadline urgency
* Units remaining
* Unavailable dates
* ML predictions

### ✅ **3. Rescheduling Button**

* Generates fresh timetable variant
* Creates new randomized optimization path

### ✅ **4. Unavailable Dates (Multi Select)**

* Using Flatpickr.js
* Smart skip → **no subject assigned for unavailable days**

### ✅ **5. Graphs**

* Daily Study Hours vs Free Hours
* Auto-updates after each generation

### ✅ **6. Calendar Visualization**

* Busy days = Red
* Free days = Green
* Unavailable = Grey

### ✅ **7. PDF Export (Styled)**

* A4 layout
* Colored sections
* Grid-based design
* Auto break on long content

### ✅ **8. Dark/Light Mode**

* Auto-saved in LocalStorage
* 3D card animation support

### ✅ **9. Delete Saved Timetable**

* Dashboard shows list
* Click “Delete” → removes from MySQL

### ✅ **10. ML Auto-Training**

* Each saved timetable is added to the dataset
* Model retrains silently
* Gets smarter day by day

---

# **6. Scheduler Logic (Heuristic Hybrid)**

Scheduling logic includes:

### ✔ Deadline urgency prioritization

Subjects near deadlines get progressively more hours.

### ✔ ML-estimated hour prediction

Model predicts how much time each unit requires.

### ✔ Units-based scheduling

Study is divided into small chunks (units), not full subjects.

### ✔ Avoid back-to-back same subject

Encourages variety.

### ✔ Weekend restriction (optional)

User can tick “Limit weekends”.

### ✔ Unavailable day skipping

Subject hours = **0** on unavailable days.

### ✔ Balanced distribution

Hours spread across days, heavier subjects get more focus.

---

# **7. Database Design (MySQL)**

### **Tables:**

#### **users**

* id
* username
* email
* password_hash

#### **timetables**

* id
* user_id
* title
* generated_json
* created_at

All relationships handled via SQLAlchemy ORM.

---

# **8. Conclusion**

This project successfully delivers:

✔ Fully automated study-planner
✔ Smart scheduling using heuristics
✔ Beautiful UI with charts and calendar
✔ Login system + Save/Delete timetables
✔ PDF export
✔ Unavailable day handling
✔ ML auto-learning system
