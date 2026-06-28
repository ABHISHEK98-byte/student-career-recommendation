# Student Career Recommendation System

An AI-powered career guidance project that recommends suitable career paths to students based on academic performance, skills, and interests.

## Final project features

- Login, signup, and forgot-password reset
- Access token + refresh token authentication flow
- Editable user profile
- FastAPI backend with local JSON storage
- Next.js dashboard frontend
- Random Forest classifier for career prediction
- Top 3 career recommendations with confidence scores
- Career roadmap for each recommendation
- Course suggestions and college suggestions
- Personalized course/college filtering using location, budget, and target score
- Skill improvement tips for weak areas
- Career market insights (salary range, demand, exams, years-to-enter, skill gap score)
- Searchable and filterable saved prediction history
- Printable report and share workflow
- Admin panel with user search and delete
- Teacher dashboard for class-level interest/recommendation insights
- Comparison tables plus bar, pie, and line-style charts
- Rate limiting + stronger password policy + admin model-metrics endpoint

## Project structure

```text
student-career-recommendation/
|-- api.py
|-- users.json
|-- prediction_history.json
|-- student_career_dataset.csv
|-- requirements.txt
|-- README.md
|-- frontend/

|   |-- app/
|   |   |-- page.tsx
|   |   |-- login/page.tsx
|   |   |-- profile/page.tsx
|   |   |-- admin/page.tsx
|   |   |-- layout.tsx
|   |   `-- globals.css
|   `-- package.json
```

## Run the project

### One-command start (recommended)

```powershell
cd C:\Users\Shivraj\student-career-recommendation
pip install -r requirements.txt
npm install
npm run dev
```

### Open in browser

```text
http://localhost:3000
```

### Manual start (alternative: 2 terminals)

Terminal 1 (backend):
```powershell
cd C:\Users\Shivraj\student-career-recommendation
python -m uvicorn api:app --reload --port 5000
```

Terminal 2 (frontend):
```powershell
cd C:\Users\Shivraj\student-career-recommendation\frontend
npm install
npm run dev
```

## Demo accounts

- `student / test123`
- `admin / admin123`
- `teacher / teacher123`

## Main API endpoints

- `POST /login`
- `POST /signup`
- `POST /forgot-password`
- `POST /refresh`
- `GET /me`
- `PUT /me`
- `GET /history`
- `GET /report`
- `GET /admin/users`
- `GET /admin/analytics` (admin + teacher)
- `GET /model/metrics` (admin only)
- `DELETE /admin/users/{username}`
- `POST /predict`

## Deployment notes

### Frontend

- Recommended: Vercel
- Set `NEXT_PUBLIC_API_BASE_URL` to your deployed backend URL

### Backend

- Recommended: Render, Railway, or a VM
- Make sure `users.json`, `prediction_history.json`, and dataset files are present

## Notes

- `app.py` is a legacy placeholder and is not part of the active frontend + backend flow.
- Current report export opens a printable report window from backend report data.
- Live market signal mode can be controlled via `.env`:
  - Create `.env` in project root (you can copy from `.env.example`)
  - Set `CAREER_LIVE_MARKET_ENABLED=true` for live job signals
  - Set `CAREER_LIVE_MARKET_ENABLED=false` to force local fallback only
