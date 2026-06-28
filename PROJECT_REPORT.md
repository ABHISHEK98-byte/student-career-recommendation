# Project Report: Student Career Recommendation System

## Executive Summary

The **Student Career Recommendation System** is an AI-powered web application developed to assist students in selecting suitable career paths based on their academic performance, technical skills, communication abilities, and personal interests.

The system integrates a **Random Forest Machine Learning model** with a modern **FastAPI backend** and **Next.js frontend** to provide accurate career recommendations with confidence scores. It also includes secure JWT-based authentication, user management, recommendation history, and an intuitive dashboard for students, teachers, and administrators.

The primary objective of this project is to simplify career planning by providing intelligent, data-driven recommendations while maintaining high performance, security, and scalability.

---

# 1. Project Objectives

## Primary Objectives

* Develop an intelligent career recommendation platform using Machine Learning.
* Analyze academic performance, technical skills, and interests.
* Provide personalized career recommendations.
* Build a secure web application with authentication.
* Deliver an intuitive and responsive user interface.
* Generate prediction confidence scores.
* Maintain recommendation history.
* Produce complete technical documentation.

## Success Criteria

* Model Accuracy: **87%+**
* Fast Response Time
* Secure Authentication
* Responsive User Interface
* Scalable Architecture
* Complete Documentation

---

# 2. System Architecture

## Overall Architecture

```text
+--------------------------------------------------+
|                Next.js Frontend                  |
|         Student / Teacher / Admin Portal         |
+-------------------------+------------------------+
                          |
                    HTTP REST API
                          |
                          ▼
+--------------------------------------------------+
|                 FastAPI Backend                  |
|--------------------------------------------------|
| Authentication                                  |
| Prediction Engine                               |
| User Management                                 |
| Report Generation                               |
+-------------------------+------------------------+
                          |
                          ▼
+--------------------------------------------------+
|           Machine Learning Engine               |
|--------------------------------------------------|
| Random Forest Classifier                        |
| Feature Processing                              |
| Career Prediction                               |
+-------------------------+------------------------+
                          |
                          ▼
+--------------------------------------------------+
|             Student Career Dataset              |
+--------------------------------------------------+
```

---

## Frontend Architecture

### Framework

* Next.js
* React
* TypeScript
* Tailwind CSS

### Modules

* Login
* Signup
* Student Dashboard
* Prediction Module
* Recommendation Dashboard
* Admin Panel
* Teacher Dashboard
* Profile Management

---

## Backend Architecture

### Framework

* FastAPI
* Uvicorn
* Python

### Backend Modules

* Authentication
* JWT Authorization
* Prediction API
* History API
* User Management
* Report API

---

## Machine Learning Architecture

### Algorithm

Random Forest Classifier

### Features

* Mathematics Score
* Science Score
* Communication Skill
* Coding Skill
* Interest Area

### Output

* Top Career Recommendation
* Top 3 Predictions
* Confidence Scores

---

# 3. Machine Learning Model

## Algorithm

Random Forest Classification

## Dataset

Student Career Dataset

## Data Processing

* Data Cleaning
* Missing Value Handling
* Label Encoding
* Feature Engineering
* Train-Test Split

## Model Evaluation

| Metric            | Value  |
| ----------------- | ------ |
| Training Accuracy | 91.25% |
| Testing Accuracy  | 87.50% |
| Precision         | 0.88   |
| Recall            | 0.85   |
| F1 Score          | 0.86   |

---

# 4. Performance Analysis

## API Response Time

| Operation     | Average Time |
| ------------- | ------------ |
| Login         | ~10 ms       |
| Prediction    | ~50 ms       |
| Total Request | <100 ms      |

The application is capable of generating predictions in real time while maintaining low latency and high accuracy.

---

# 5. Security Implementation

## Authentication

* JWT Access Token
* Refresh Token Support
* Secure Password Hashing using bcrypt
* Role-Based Authorization

## Security Features

* Password Encryption
* Token Validation
* Protected API Endpoints
* CORS Protection
* Input Validation
* Rate Limiting

---

# 6. Default Test Accounts

| Role    | Username | Password   |
| ------- | -------- | ---------- |
| Student | student  | test123    |
| Teacher | teacher  | teacher123 |
| Admin   | admin    | admin123   |
