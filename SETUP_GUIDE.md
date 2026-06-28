# 🚀 Complete Project Setup Guide

# Student Career Recommendation System Using AI

This guide explains how to install, configure, and run the **Student Career Recommendation System** on a local machine.

---

# 📋 Project Overview

The Student Career Recommendation System is an AI-powered web application that recommends suitable career paths based on a student's academic performance, technical skills, interests, and preferences.

---

# ✅ Features

* AI-based Career Recommendation using Random Forest
* FastAPI REST API Backend
* Next.js Frontend
* JWT Authentication
* Student Dashboard
* Teacher Dashboard
* Admin Dashboard
* Career Roadmaps
* Course Recommendations
* College Suggestions
* Prediction History
* Printable Reports
* Secure Password Hashing
* Responsive User Interface

---

# 💻 System Requirements

| Software | Version |
| -------- | ------- |
| Python   | 3.11+   |
| Node.js  | 20+     |
| npm      | Latest  |
| Git      | Latest  |

---

# 📥 Installation

## Step 1 — Clone Repository

```bash
git clone https://github.com/ABHISHEK98-byte/student-career-recommendation.git
cd student-career-recommendation
```

---

## Step 2 — Create Virtual Environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Step 3 — Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

# ▶️ Running the Application

## Backend

```bash
python -m uvicorn api:app --reload --port 5000
```

Backend URL

```
http://localhost:5000
```

Swagger API Documentation

```
http://localhost:5000/docs
```

---

## Frontend

Open another terminal.

```bash
cd frontend
npm run dev
```

Frontend URL

```
http://localhost:3000
```

---

# 🔐 Demo Credentials

| Role    | Username | Password   |
| ------- | -------- | ---------- |
| Student | student  | test123    |
| Teacher | teacher  | teacher123 |
| Admin   | admin    | admin123   |

---

# 🧠 Using the Application

1. Login using a demo account.
2. Enter student academic details.
3. Select skills and interests.
4. Click **Predict Career**.
5. View:

   * Top 3 Career Recommendations
   * Confidence Scores
   * Career Roadmap
   * Recommended Courses
   * Suggested Colleges

---

# 📁 Project Structure

```text
student-career-recommendation/
├── api.py
├── requirements.txt
├── users.json
├── prediction_history.json
├── student_career_dataset.csv
├── README.md
├── SETUP_GUIDE.md
├── PROJECT_REPORT.md
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
└── .env.example
```

---

# 🌐 API Endpoints

| Method | Endpoint         |
| ------ | ---------------- |
| POST   | /signup          |
| POST   | /login           |
| POST   | /forgot-password |
| POST   | /refresh         |
| GET    | /me              |
| PUT    | /me              |
| POST   | /predict         |
| GET    | /history         |
| GET    | /report          |
| GET    | /admin/users     |
| GET    | /admin/analytics |
| GET    | /model/metrics   |

---

# 🛠 Troubleshooting

## Backend Issues

```bash
pip install -r requirements.txt
python -m uvicorn api:app --reload
```

## Frontend Issues

```bash
cd frontend
npm install
npm run dev
```

## Verify Installation

```bash
python --version
node --version
npm --version
```

---

# 📊 Technologies Used

| Layer            | Technology                   |
| ---------------- | ---------------------------- |
| Frontend         | Next.js, React, Tailwind CSS |
| Backend          | FastAPI, Uvicorn             |
| Machine Learning | Scikit-learn, Pandas, NumPy  |
| Authentication   | JWT, bcrypt                  |
| Data Storage     | JSON & CSV                   |

---

# 📌 Project Status

* ✅ Development Completed
* ✅ Authentication Implemented
* ✅ Machine Learning Integrated
* ✅ Frontend Completed
* ✅ Backend Completed
* ✅ API Documentation Available
* ✅ Production Ready

---

# 📞 Support

If you encounter any issues:

1. Check the README.md documentation.
2. Verify Python and Node.js versions.
3. Ensure all dependencies are installed.
4. Restart both backend and frontend services.

---

**Version:** 1.0.0

**Repository:** https://github.com/ABHISHEK98-byte/student-career-recommendation
