# 🎓 Student Career Recommendation System

An AI-powered web application that helps students identify suitable career paths based on their academic performance, technical skills, interests, and personal preferences. The system combines Machine Learning with a modern web interface to deliver personalized career recommendations along with learning roadmaps, college suggestions, and career insights.

---

# ✨ Features

## Authentication

* Secure JWT Authentication
* User Registration
* Login & Logout
* Forgot Password
* Refresh Token Support
* Password Encryption (bcrypt)

## Student Dashboard

* Personalized Student Profile
* Career Prediction using AI
* Top 3 Career Recommendations
* Confidence Score for Each Recommendation
* Career Roadmap
* Skill Improvement Suggestions
* Course Recommendations
* College Recommendations
* Salary & Market Demand Insights
* Career History
* Printable Career Report

## Admin Dashboard

* User Management
* Search Users
* Delete Users
* View Analytics
* Model Performance Metrics

## Teacher Dashboard

* Student Analytics
* Career Interest Distribution
* Recommendation Statistics

## Machine Learning

* Random Forest Classification
* Multiple Career Categories
* Confidence Probability Scores
* Model Performance Metrics

---

# 🏗️ Project Architecture

```
Browser (Next.js Frontend)
            │
            ▼
      FastAPI REST API
            │
            ▼
 Authentication Layer
            │
            ▼
 Machine Learning Engine
            │
            ▼
Student Career Dataset
```

---

# 📂 Project Structure

```
student-career-recommendation/
│
├── api.py
├── requirements.txt
├── users.json
├── prediction_history.json
├── student_career_dataset.csv
├── README.md
├── PROJECT_REPORT.md
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── profile/
│   │   ├── admin/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   │
│   ├── package.json
│   └── tsconfig.json
│
└── requirements.txt
```

---

# ⚙️ Prerequisites

Before running the project, make sure the following software is installed:

* Python 3.11 or later
* Node.js 20 or later
* npm
* Git

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/ABHISHEK98-byte/student-career-recommendation.git
cd student-career-recommendation
```

---

## 2. Create Virtual Environment

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

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

# ▶️ Running the Project

## Option 1 (Recommended)

If your project supports a combined startup:

```bash
npm run dev
```

---

## Option 2 (Manual)

### Start Backend

```bash
python -m uvicorn api:app --reload --port 5000
```

Backend URL

```
http://localhost:5000
```

---

### Start Frontend

Open another terminal:

```bash
cd frontend
npm run dev
```

Frontend URL

```
http://localhost:3000
```

---

# 🔐 Demo Accounts

| Role    | Username | Password   |
| ------- | -------- | ---------- |
| Student | student  | test123    |
| Teacher | teacher  | teacher123 |
| Admin   | admin    | admin123   |

---

# 🌐 API Endpoints

| Method | Endpoint         | Description         |
| ------ | ---------------- | ------------------- |
| POST   | /signup          | Register User       |
| POST   | /login           | Login               |
| POST   | /forgot-password | Password Reset      |
| POST   | /refresh         | Refresh Token       |
| GET    | /me              | User Profile        |
| PUT    | /me              | Update Profile      |
| POST   | /predict         | Career Prediction   |
| GET    | /history         | Prediction History  |
| GET    | /report          | Printable Report    |
| GET    | /admin/users     | User Management     |
| GET    | /admin/analytics | Dashboard Analytics |
| GET    | /model/metrics   | ML Model Metrics    |

---

# 📊 Machine Learning Model

| Property         | Value                      |
| ---------------- | -------------------------- |
| Algorithm        | Random Forest              |
| Task             | Multi-Class Classification |
| Dataset          | Student Career Dataset     |
| Output           | Career Recommendation      |
| Confidence Score | Supported                  |

---

# 🛡️ Security

* JWT Authentication
* Password Hashing (bcrypt)
* Refresh Tokens
* Input Validation
* Role-Based Authorization
* API Rate Limiting

---

# 🚀 Deployment

## Frontend

Deploy using:

* Vercel

## Backend

Deploy using:

* Render
* Railway
* Azure
* AWS EC2

---

# 🔧 Troubleshooting

## Backend Not Starting

```bash
pip install -r requirements.txt
python -m uvicorn api:app --reload
```

## Frontend Not Starting

```bash
cd frontend
npm install
npm run dev
```

---

# 📈 Future Enhancements

* Resume Analyzer
* AI Career Chatbot
* Live Job Market Integration
* Interview Preparation
* Resume Builder
* Skill Gap Analysis
* Email Notifications
* Cloud Database Support

---

# 📄 License

This project is intended for educational and learning purposes.

---

# 👤 Repository

Maintained by **ABHISHEK98-byte**

GitHub Repository:

https://github.com/ABHISHEK98-byte/student-career-recommendation
