from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import Lock
from urllib.parse import quote_plus
from urllib.request import urlopen

import numpy as np
import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score


DATA_PATH = Path(__file__).with_name("student_career_dataset.csv")
USERS_PATH = Path(__file__).with_name("users.json")
HISTORY_PATH = Path(__file__).with_name("prediction_history.json")
ENV_PATH = Path(__file__).with_name(".env")


def load_local_env() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

app = FastAPI(
    title="Student Career Recommendation System",
    version="4.0.0",
    description="AI-powered student career guidance API with authentication, editable profiles, forgot-password reset, filterable history, admin tools, printable report support, and richer career guidance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=3, max_length=30)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, hyphens, or underscores")
        return normalized


class SignupRequest(LoginRequest):
    full_name: str = Field(min_length=2, max_length=60)


class ForgotPasswordRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    full_name: str = Field(min_length=2, max_length=60)
    new_password: str = Field(min_length=3, max_length=30)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=60)
    current_password: str = Field(min_length=3, max_length=30)
    new_password: str | None = Field(default=None, min_length=3, max_length=30)


class DeleteUserResponse(BaseModel):
    deleted: bool
    username: str


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in_seconds: int
    username: str
    full_name: str
    role: str


class PredictRequest(BaseModel):
    maths: int = Field(ge=0, le=100)
    science: int = Field(ge=0, le=100)
    communication: str
    coding: str
    interest: str
    preferred_location: str | None = Field(default=None, max_length=60)
    budget_level: str | None = Field(default=None, max_length=20)
    target_score: int | None = Field(default=None, ge=0, le=100)

    @field_validator("communication", "coding", "interest")
    @classmethod
    def normalize_strings(cls, value: str) -> str:
        return value.strip()


class CareerPrediction(BaseModel):
    career: str
    confidence: float
    match_label: str
    reason: str
    roadmap: list[str]
    courses: list[str]
    colleges: list[str]
    skill_tips: list[str]
    salary_range_inr_lpa: str
    future_demand: str
    key_exams: list[str]
    estimated_years_to_enter: str
    skill_gap_score: int
    live_market: dict[str, str | int | list[str]]


class ProfileSummary(BaseModel):
    average_score: float
    academic_band: str
    profile_type: str
    strengths: list[str]
    development_areas: list[str]
    suggested_pathway: str


class FeatureInsight(BaseModel):
    feature: str
    importance: float


class PredictResponse(BaseModel):
    accuracy: float
    generated_at: str
    profile_summary: ProfileSummary
    feature_insights: list[FeatureInsight]
    predictions: list[CareerPrediction]


class OptionsResponse(BaseModel):
    communication_levels: list[str]
    coding_levels: list[str]
    interest_areas: list[str]
    careers: list[str]
    model_accuracy: float
    total_records: int
    top_careers: list[dict[str, int | str]]


class HistoryEntry(BaseModel):
    id: str
    created_at: str
    form: PredictRequest
    top_career: str
    top_confidence: float
    predictions: list[CareerPrediction]
    profile_summary: ProfileSummary


class ProfileResponse(BaseModel):
    username: str
    full_name: str
    role: str
    created_at: str
    total_predictions: int
    latest_recommendation: str | None


class AdminUserSummary(BaseModel):
    username: str
    full_name: str
    role: str
    created_at: str
    total_predictions: int


class AdminUsersResponse(BaseModel):
    users: list[AdminUserSummary]


class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_predictions: int
    role_counts: list[dict[str, int | str]]
    interest_counts: list[dict[str, int | str]]
    top_recommendations: list[dict[str, int | str]]


class ReportResponse(BaseModel):
    profile: ProfileResponse
    recent_history: list[HistoryEntry]
    generated_at: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ModelMetricsResponse(BaseModel):
    accuracy: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    cv_accuracy_mean: float
    cv_accuracy_std: float
    confusion_matrix: list[list[int]]


DEFAULT_USERS = {
    "student": {
        "username": "student",
        "full_name": "Demo Student",
        "role": "student",
        "password_hash": "",
        "created_at": "2026-01-01T00:00:00+00:00",
    },
    "admin": {
        "username": "admin",
        "full_name": "System Admin",
        "role": "admin",
        "password_hash": "",
        "created_at": "2026-01-01T00:00:00+00:00",
    },
    "teacher": {
        "username": "teacher",
        "full_name": "Demo Teacher",
        "role": "teacher",
        "password_hash": "",
        "created_at": "2026-01-01T00:00:00+00:00",
    },
}

DOMAIN_GUIDANCE = {
    "AI": {
        "roadmap": [
            "Strengthen programming in Python and core problem solving.",
            "Build statistics and machine learning fundamentals.",
            "Create portfolio projects using datasets and model deployment.",
        ],
        "courses": [
            "B.Tech CSE with AI specialization",
            "BCA with Data Science electives",
            "Python, SQL, Machine Learning certification",
        ],
        "colleges": [
            "IITs and NITs",
            "IIIT Hyderabad or IIIT Bangalore",
            "Private universities with AI or Data Science tracks",
        ],
        "skill_tips": [
            "Practice coding challenges weekly.",
            "Work on Kaggle-style datasets.",
            "Learn Git, APIs, and project documentation.",
        ],
    },
    "Business": {
        "roadmap": [
            "Develop communication, planning, and market understanding.",
            "Learn finance, analytics, and presentation skills.",
            "Gain internship or live project exposure in sales or strategy.",
        ],
        "courses": [
            "BBA or B.Com",
            "Digital Marketing certification",
            "Business Analytics or Excel certification",
        ],
        "colleges": [
            "Delhi University affiliated colleges",
            "Christ University",
            "Top BBA or commerce institutes in your state",
        ],
        "skill_tips": [
            "Improve presentations and negotiation.",
            "Study case studies and market trends.",
            "Build spreadsheet and reporting confidence.",
        ],
    },
    "Design": {
        "roadmap": [
            "Build design fundamentals in layout, color, and user experience.",
            "Create a portfolio with branding, UI, or graphic projects.",
            "Learn tools and present your work professionally.",
        ],
        "courses": [
            "B.Des or design diploma",
            "UI/UX certification",
            "Graphic design and portfolio development course",
        ],
        "colleges": [
            "NID or design-focused institutes",
            "MIT Institute of Design",
            "Strong private colleges with design studios",
        ],
        "skill_tips": [
            "Practice Figma, Canva, and Adobe tools.",
            "Study design systems and portfolios.",
            "Take feedback regularly and iterate on work.",
        ],
    },
}

CAREER_SPECIFIC_OVERRIDES = {
    "Data Scientist": {
        "courses": ["Data Science bootcamp", "Machine Learning specialization", "SQL and Python for analytics"],
        "skill_tips": ["Master Python notebooks.", "Study data cleaning and visualization.", "Present insights clearly."],
    },
    "Software Engineer": {
        "courses": ["DSA and system design", "Full-stack web development", "Object-oriented programming"],
        "skill_tips": ["Write projects end-to-end.", "Practice debugging.", "Learn deployment basics."],
    },
    "Graphic Designer": {
        "courses": ["Graphic design tools mastery", "Brand identity design", "Visual storytelling"],
        "skill_tips": ["Build before-and-after portfolio pieces.", "Study typography.", "Practice client briefs."],
    },
}

raw_data = pd.read_csv(DATA_PATH)
display_data = raw_data.copy()

le_comm = LabelEncoder()
le_coding = LabelEncoder()
le_interest = LabelEncoder()
le_career = LabelEncoder()

encoded_data = raw_data.copy()
encoded_data["Communication"] = le_comm.fit_transform(raw_data["Communication"])
encoded_data["Coding"] = le_coding.fit_transform(raw_data["Coding"])
encoded_data["Interest"] = le_interest.fit_transform(raw_data["Interest"])
encoded_data["Career"] = le_career.fit_transform(raw_data["Career"])

X = encoded_data.drop("Career", axis=1)
y = encoded_data["Career"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
y_test_pred = model.predict(X_test)
precision_weighted = precision_score(y_test, y_test_pred, average="weighted", zero_division=0)
recall_weighted = recall_score(y_test, y_test_pred, average="weighted", zero_division=0)
f1_weighted = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)
cv_scores = cross_val_score(model, X, y, cv=5)
conf_matrix = confusion_matrix(y_test, y_test_pred)

feature_names = ["Maths", "Science", "Communication", "Coding", "Interest"]
top_career_counts = Counter(display_data["Career"]).most_common(5)


ACCESS_TOKEN_TTL_SECONDS = 60 * 60 * 24
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7
PASSWORD_MIN_LENGTH = 8
RATE_LIMIT_MAX_REQUESTS = 40
RATE_LIMIT_WINDOW_SECONDS = 60
REQUEST_LOG: dict[str, deque[float]] = defaultdict(deque)
REQUEST_LOCK = Lock()

CAREER_MARKET_DATA = {
    "Data Scientist": {"salary": "8-28", "demand": "Very High", "exams": ["JEE Main", "GATE (optional)", "NIELIT certifications"], "years": "3-5"},
    "Software Engineer": {"salary": "6-24", "demand": "Very High", "exams": ["JEE Main", "coding assessments", "GATE (optional)"], "years": "3-4"},
    "Graphic Designer": {"salary": "3-12", "demand": "Medium", "exams": ["NID DAT", "UCEED", "portfolio interview"], "years": "2-4"},
    "default": {"salary": "4-15", "demand": "Medium", "exams": ["Domain entrance exams", "aptitude tests"], "years": "3-5"},
}

BUDGET_COLLEGE_FILTERS = {
    "low": ["Government", "State", "Public"],
    "medium": ["Government", "State", "Private"],
    "high": ["IIT", "IIIT", "Private", "International"],
}

LIVE_MARKET_ENABLED = os.getenv("CAREER_LIVE_MARKET_ENABLED", "true").strip().lower() == "true"
LIVE_MARKET_CACHE_TTL_SECONDS = 60 * 30
LIVE_MARKET_CACHE: dict[str, dict] = {}
LIVE_MARKET_LOCK = Lock()
CAREER_SEARCH_HINTS = {
    "Data Scientist": "data scientist",
    "Software Engineer": "software engineer",
    "Graphic Designer": "graphic designer",
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if not any(ch.isupper() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include at least one uppercase letter")
    if not any(ch.islower() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include at least one lowercase letter")
    if not any(ch.isdigit() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include at least one number")


def issue_token(username: str, token_type: str, ttl_seconds: int) -> str:
    expires_at = int((datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).timestamp())
    return f"student-career-token:{token_type}:{username}:{expires_at}"


def parse_token(token: str) -> tuple[str, str, int]:
    parts = token.split(":")
    if len(parts) == 2 and parts[0] == "student-career-token":
        username = parts[1].strip().lower()
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
        return "access", username, int(datetime.now(timezone.utc).timestamp()) + ACCESS_TOKEN_TTL_SECONDS

    if len(parts) != 4 or parts[0] != "student-career-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
    token_type = parts[1]
    username = parts[2].strip().lower()
    try:
        expires_at = int(parts[3])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token") from exc
    if datetime.now(timezone.utc).timestamp() > expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return token_type, username, expires_at


def enforce_rate_limit(request: Request, bucket: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{bucket}:{client_ip}"
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    with REQUEST_LOCK:
        queue = REQUEST_LOG[key]
        while queue and queue[0] < window_start:
            queue.popleft()
        if len(queue) >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many requests. Please retry after a minute.")
        queue.append(now)


def seed_users_file() -> None:
    seeded_users = json.loads(json.dumps(DEFAULT_USERS))
    seeded_users["student"]["password_hash"] = hash_password("test123")
    seeded_users["admin"]["password_hash"] = hash_password("admin123")
    seeded_users["teacher"]["password_hash"] = hash_password("teacher123")
    USERS_PATH.write_text(json.dumps(seeded_users, indent=2), encoding="utf-8")


def read_users() -> dict[str, dict[str, str]]:
    if not USERS_PATH.exists():
        seed_users_file()
    users = json.loads(USERS_PATH.read_text(encoding="utf-8"))
    updated = False

    for username, user in users.items():
        default_user = DEFAULT_USERS.get(username, {})

        if "username" not in user:
            user["username"] = username
            updated = True
        if "full_name" not in user:
            user["full_name"] = default_user.get("full_name", username.title())
            updated = True
        if "role" not in user:
            user["role"] = default_user.get("role", "student")
            updated = True
        if "created_at" not in user:
            user["created_at"] = default_user.get("created_at", datetime.now(timezone.utc).isoformat())
            updated = True

    if updated:
        write_users(users)

    return users


def write_users(users: dict[str, dict[str, str]]) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def get_user(username: str) -> dict[str, str] | None:
    return read_users().get(username)


def read_history() -> dict[str, list[dict]]:
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text(json.dumps({}, indent=2), encoding="utf-8")
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


def write_history(history: dict[str, list[dict]]) -> None:
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")


def require_token(authorization: str | None, expected_type: str = "access") -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")

    token = authorization.removeprefix("Bearer ").strip()
    token_type, username, _ = parse_token(token)
    if token_type != expected_type or not username or get_user(username) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
    return username


def require_admin(username: str) -> None:
    user = get_user(username)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def require_staff(username: str) -> None:
    user = get_user(username)
    if not user or user.get("role") not in {"admin", "teacher"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")


def get_match_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "Excellent fit"
    if confidence >= 0.55:
        return "Strong fit"
    if confidence >= 0.35:
        return "Good option"
    return "Emerging option"


def build_profile_summary(request: PredictRequest) -> ProfileSummary:
    average_score = round((request.maths + request.science) / 2, 1)

    if average_score >= 85:
        academic_band = "Outstanding"
    elif average_score >= 70:
        academic_band = "Strong"
    elif average_score >= 55:
        academic_band = "Developing"
    else:
        academic_band = "Foundation"

    strengths: list[str] = []
    development_areas: list[str] = []

    if request.maths >= 75:
        strengths.append("Strong quantitative ability")
    else:
        development_areas.append("Improve analytical problem-solving")

    if request.science >= 75:
        strengths.append("Good scientific reasoning")
    else:
        development_areas.append("Strengthen concept clarity in science")

    if request.communication == "High":
        strengths.append("Confident communication skills")
    elif request.communication == "Low":
        development_areas.append("Practice presentation and speaking skills")

    if request.coding == "Yes":
        strengths.append("Comfortable with technical and coding tasks")
    else:
        development_areas.append("Explore basic digital and coding literacy")

    if request.interest == "AI":
        profile_type = "Technology-oriented learner"
        suggested_pathway = "Focus on programming, statistics, and project-based AI practice."
    elif request.interest == "Business":
        profile_type = "Business and leadership learner"
        suggested_pathway = "Build communication, decision-making, and market analysis skills."
    else:
        profile_type = "Creative and design learner"
        suggested_pathway = "Strengthen design tools, portfolio work, and visual communication."

    if not strengths:
        strengths.append("Clear interest direction identified")
    if not development_areas:
        development_areas.append("Keep building consistency through practical projects")

    return ProfileSummary(
        average_score=average_score,
        academic_band=academic_band,
        profile_type=profile_type,
        strengths=strengths,
        development_areas=development_areas,
        suggested_pathway=suggested_pathway,
    )


def build_reason_for_career(career: str, request: PredictRequest) -> str:
    interest = request.interest.lower()
    if interest == "ai":
        return f"{career} aligns with your AI interest, academic profile, and technical inclination."
    if interest == "business":
        return f"{career} suits your business interest and benefits from communication and decision-making skills."
    return f"{career} matches your design interest and rewards creative communication and applied skills."


def build_career_guidance(career: str, request: PredictRequest) -> dict[str, list[str]]:
    base = DOMAIN_GUIDANCE.get(request.interest, DOMAIN_GUIDANCE["AI"])
    override = CAREER_SPECIFIC_OVERRIDES.get(career, {})
    courses = override.get("courses", base["courses"])
    skill_tips = override.get("skill_tips", base["skill_tips"])

    roadmap = list(base["roadmap"])
    if request.coding == "No" and request.interest == "AI":
        roadmap.insert(0, "Start with basic programming and digital literacy before advanced AI concepts.")

    return {
        "roadmap": roadmap,
        "courses": courses,
        "colleges": list(base["colleges"]),
        "skill_tips": skill_tips,
    }


def build_market_insights(career: str, request: PredictRequest) -> dict[str, str | list[str] | int]:
    market = CAREER_MARKET_DATA.get(career, CAREER_MARKET_DATA["default"])
    baseline = int(round((request.maths + request.science) / 2))
    target = request.target_score if request.target_score is not None else 85
    skill_gap_score = max(0, min(100, target - baseline))
    return {
        "salary_range_inr_lpa": f"{market['salary']} LPA",
        "future_demand": str(market["demand"]),
        "key_exams": list(market["exams"]),
        "estimated_years_to_enter": str(market["years"]),
        "skill_gap_score": skill_gap_score,
    }


def apply_preference_filters(courses: list[str], colleges: list[str], request: PredictRequest) -> tuple[list[str], list[str]]:
    filtered_colleges = list(colleges)
    if request.budget_level:
        budget = request.budget_level.strip().lower()
        hints = BUDGET_COLLEGE_FILTERS.get(budget, [])
        if hints:
            filtered = [college for college in filtered_colleges if any(hint.lower() in college.lower() for hint in hints)]
            if filtered:
                filtered_colleges = filtered

    if request.preferred_location:
        location = request.preferred_location.strip()
        filtered_colleges = [f"{college} ({location})" for college in filtered_colleges]

    personalized_courses = list(courses)
    if request.target_score is not None and request.target_score >= 85:
        personalized_courses.insert(0, "Advanced honors / competitive exam prep track")
    elif request.target_score is not None and request.target_score <= 60:
        personalized_courses.insert(0, "Foundation + bridge modules for core concepts")

    return personalized_courses, filtered_colleges


def get_live_market_signal(career: str) -> dict[str, str | int | list[str]]:
    fallback = {
        "source": "local-fallback",
        "status": "offline",
        "job_count": 0,
        "sample_roles": [career],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    if not LIVE_MARKET_ENABLED:
        return fallback

    now_ts = datetime.now(timezone.utc).timestamp()
    with LIVE_MARKET_LOCK:
        cached = LIVE_MARKET_CACHE.get(career)
        if cached and now_ts - cached["timestamp"] < LIVE_MARKET_CACHE_TTL_SECONDS:
            return cached["value"]

    keyword = CAREER_SEARCH_HINTS.get(career, career)
    api_url = f"https://remotive.com/api/remote-jobs?search={quote_plus(keyword)}&limit=20"
    try:
        with urlopen(api_url, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        sample_roles: list[str] = []
        for job in jobs[:3]:
            title = str(job.get("title", "")).strip()
            company = str(job.get("company_name", "")).strip()
            if title and company:
                sample_roles.append(f"{title} at {company}")
            elif title:
                sample_roles.append(title)
        value = {
            "source": "remotive",
            "status": "live",
            "job_count": len(jobs),
            "sample_roles": sample_roles or [keyword.title()],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        value = fallback

    with LIVE_MARKET_LOCK:
        LIVE_MARKET_CACHE[career] = {"timestamp": now_ts, "value": value}
    return value


def build_token_response(user: dict[str, str]) -> TokenResponse:
    return TokenResponse(
        access_token=issue_token(user["username"], "access", ACCESS_TOKEN_TTL_SECONDS),
        refresh_token=issue_token(user["username"], "refresh", REFRESH_TOKEN_TTL_SECONDS),
        token_type="bearer",
        expires_in_seconds=ACCESS_TOKEN_TTL_SECONDS,
        username=user["username"],
        full_name=user["full_name"],
        role=user.get("role", "student"),
    )


def build_profile_response(username: str) -> ProfileResponse:
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    history = read_history().get(username, [])
    latest_recommendation = history[0]["top_career"] if history else None

    return ProfileResponse(
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=user["created_at"],
        total_predictions=len(history),
        latest_recommendation=latest_recommendation,
    )


def build_history_entry(request: PredictRequest, response: PredictResponse) -> HistoryEntry:
    top_prediction = response.predictions[0]
    return HistoryEntry(
        id=f"pred-{datetime.now(timezone.utc).timestamp()}",
        created_at=response.generated_at,
        form=request,
        top_career=top_prediction.career,
        top_confidence=top_prediction.confidence,
        predictions=response.predictions,
        profile_summary=response.profile_summary,
    )


def hydrate_history_entry(item: dict) -> HistoryEntry:
    form_data = item.get("form", {})
    form = PredictRequest(
        maths=form_data.get("maths", 0),
        science=form_data.get("science", 0),
        communication=form_data.get("communication", "Medium"),
        coding=form_data.get("coding", "No"),
        interest=form_data.get("interest", "AI"),
    )

    hydrated_predictions: list[CareerPrediction] = []
    for raw_prediction in item.get("predictions", []):
        career = str(raw_prediction.get("career", "Unknown Career"))
        confidence = float(raw_prediction.get("confidence", 0.0))
        guidance = build_career_guidance(career, form)
        market_insights = build_market_insights(career, form)
        live_market = get_live_market_signal(career)
        courses, colleges = apply_preference_filters(guidance["courses"], guidance["colleges"], form)

        hydrated_predictions.append(
            CareerPrediction(
                career=career,
                confidence=confidence,
                match_label=raw_prediction.get("match_label", get_match_label(confidence)),
                reason=raw_prediction.get("reason", build_reason_for_career(career, form)),
                roadmap=raw_prediction.get("roadmap", guidance["roadmap"]),
                courses=raw_prediction.get("courses", courses),
                colleges=raw_prediction.get("colleges", colleges),
                skill_tips=raw_prediction.get("skill_tips", guidance["skill_tips"]),
                salary_range_inr_lpa=raw_prediction.get("salary_range_inr_lpa", market_insights["salary_range_inr_lpa"]),
                future_demand=raw_prediction.get("future_demand", market_insights["future_demand"]),
                key_exams=raw_prediction.get("key_exams", market_insights["key_exams"]),
                estimated_years_to_enter=raw_prediction.get("estimated_years_to_enter", market_insights["estimated_years_to_enter"]),
                skill_gap_score=int(raw_prediction.get("skill_gap_score", market_insights["skill_gap_score"])),
                live_market=raw_prediction.get("live_market", live_market),
            )
        )

    if hydrated_predictions:
        top_prediction = hydrated_predictions[0]
    else:
        market_insights = build_market_insights(str(item.get("top_career", "Unknown Career")), form)
        live_market = get_live_market_signal(str(item.get("top_career", "Unknown Career")))
        fallback_guidance = build_career_guidance(str(item.get("top_career", "Unknown Career")), form)
        fallback_courses, fallback_colleges = apply_preference_filters(
            fallback_guidance["courses"], fallback_guidance["colleges"], form
        )
        top_prediction = CareerPrediction(
            career=item.get("top_career", "Unknown Career"),
            confidence=float(item.get("top_confidence", 0.0)),
            match_label=get_match_label(float(item.get("top_confidence", 0.0))),
            reason=build_reason_for_career(str(item.get("top_career", "Unknown Career")), form),
            roadmap=fallback_guidance["roadmap"],
            courses=fallback_courses,
            colleges=fallback_colleges,
            skill_tips=fallback_guidance["skill_tips"],
            salary_range_inr_lpa=str(market_insights["salary_range_inr_lpa"]),
            future_demand=str(market_insights["future_demand"]),
            key_exams=list(market_insights["key_exams"]),
            estimated_years_to_enter=str(market_insights["estimated_years_to_enter"]),
            skill_gap_score=int(market_insights["skill_gap_score"]),
            live_market=live_market,
        )
        hydrated_predictions = [top_prediction]

    profile_summary_data = item.get("profile_summary", {})
    profile_summary = ProfileSummary(
        average_score=float(profile_summary_data.get("average_score", round((form.maths + form.science) / 2, 1))),
        academic_band=profile_summary_data.get("academic_band", build_profile_summary(form).academic_band),
        profile_type=profile_summary_data.get("profile_type", build_profile_summary(form).profile_type),
        strengths=profile_summary_data.get("strengths", build_profile_summary(form).strengths),
        development_areas=profile_summary_data.get("development_areas", build_profile_summary(form).development_areas),
        suggested_pathway=profile_summary_data.get("suggested_pathway", build_profile_summary(form).suggested_pathway),
    )

    return HistoryEntry(
        id=str(item.get("id", f"pred-{datetime.now(timezone.utc).timestamp()}")),
        created_at=str(item.get("created_at", datetime.now(timezone.utc).isoformat())),
        form=form,
        top_career=str(item.get("top_career", top_prediction.career)),
        top_confidence=float(item.get("top_confidence", top_prediction.confidence)),
        predictions=hydrated_predictions,
        profile_summary=profile_summary,
    )


@app.get("/")
def read_root():
    return {"message": "Student Career Recommendation API is running.", "version": app.version, "docs": "/docs"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": True,
        "dataset_records": int(len(display_data)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/options", response_model=OptionsResponse)
def get_options():
    return OptionsResponse(
        communication_levels=sorted(display_data["Communication"].unique().tolist()),
        coding_levels=sorted(display_data["Coding"].unique().tolist()),
        interest_areas=sorted(display_data["Interest"].unique().tolist()),
        careers=sorted(display_data["Career"].unique().tolist()),
        model_accuracy=float(accuracy),
        total_records=int(len(display_data)),
        top_careers=[{"career": str(career), "count": int(count)} for career, count in top_career_counts],
    )


@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request):
    enforce_rate_limit(http_request, "login")
    user = get_user(request.username)
    if not user or user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return build_token_response(user)


@app.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, http_request: Request):
    enforce_rate_limit(http_request, "signup")
    validate_password_strength(request.password)
    users = read_users()
    if request.username in users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    users[request.username] = {
        "username": request.username,
        "full_name": request.full_name.strip(),
        "role": "student",
        "password_hash": hash_password(request.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_users(users)
    return build_token_response(users[request.username])


@app.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, http_request: Request):
    enforce_rate_limit(http_request, "forgot-password")
    validate_password_strength(request.new_password)
    users = read_users()
    user = users.get(request.username)
    if not user or user["full_name"].strip().lower() != request.full_name.strip().lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User verification failed")

    user["password_hash"] = hash_password(request.new_password)
    write_users(users)
    return MessageResponse(message="Password reset successful. You can log in with the new password.")


@app.get("/me", response_model=ProfileResponse)
def get_my_profile(authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    return build_profile_response(username)


@app.put("/me", response_model=TokenResponse)
def update_my_profile(request: UpdateProfileRequest, authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    users = read_users()
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["password_hash"] != hash_password(request.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    user["full_name"] = request.full_name.strip()
    if request.new_password:
        validate_password_strength(request.new_password)
        user["password_hash"] = hash_password(request.new_password)
    write_users(users)
    return build_token_response(user)


@app.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest):
    token_type, username, _ = parse_token(request.refresh_token.strip())
    if token_type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return build_token_response(user)


@app.get("/history", response_model=list[HistoryEntry])
def get_my_history(
    authorization: str | None = Header(default=None),
    search: str = Query(default=""),
    interest: str = Query(default=""),
):
    username = require_token(authorization)
    entries = [hydrate_history_entry(item) for item in read_history().get(username, [])]

    if search.strip():
        query = search.strip().lower()
        entries = [
            entry
            for entry in entries
            if query in entry.top_career.lower()
            or any(query in prediction.career.lower() for prediction in entry.predictions)
        ]

    if interest.strip():
        interest_query = interest.strip().lower()
        entries = [entry for entry in entries if entry.form.interest.lower() == interest_query]

    return entries


@app.delete("/history", response_model=MessageResponse)
def clear_my_history(authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    history = read_history()
    history[username] = []
    write_history(history)
    return MessageResponse(message="Recent activity cleared successfully.")


@app.get("/report", response_model=ReportResponse)
def get_my_report(authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    history = [hydrate_history_entry(item) for item in read_history().get(username, [])[:10]]
    return ReportResponse(
        profile=build_profile_response(username),
        recent_history=history,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/admin/users", response_model=AdminUsersResponse)
def get_admin_users(
    authorization: str | None = Header(default=None),
    search: str = Query(default=""),
):
    username = require_token(authorization)
    require_admin(username)

    history = read_history()
    users = []
    for user in read_users().values():
        users.append(
            AdminUserSummary(
                username=user["username"],
                full_name=user["full_name"],
                role=user["role"],
                created_at=user["created_at"],
                total_predictions=len(history.get(user["username"], [])),
            )
        )

    if search.strip():
        query = search.strip().lower()
        users = [
            user for user in users
            if query in user.username.lower() or query in user.full_name.lower() or query in user.role.lower()
        ]

    users.sort(key=lambda user: (user.role != "admin", user.username))
    return AdminUsersResponse(users=users)


@app.get("/admin/analytics", response_model=AdminAnalyticsResponse)
def get_admin_analytics(authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    require_staff(username)

    users = read_users()
    history = read_history()

    role_counter = Counter(user.get("role", "student") for user in users.values())
    interest_counter: Counter[str] = Counter()
    recommendation_counter: Counter[str] = Counter()
    total_predictions = 0

    for entries in history.values():
      total_predictions += len(entries)
      for entry in entries:
          form = entry.get("form", {})
          interest = str(form.get("interest", "")).strip()
          if interest:
              interest_counter[interest] += 1
          top_career = str(entry.get("top_career", "")).strip()
          if top_career:
              recommendation_counter[top_career] += 1

    return AdminAnalyticsResponse(
        total_users=len(users),
        total_predictions=total_predictions,
        role_counts=[{"label": key, "count": value} for key, value in role_counter.items()],
        interest_counts=[{"label": key, "count": value} for key, value in interest_counter.most_common(5)],
        top_recommendations=[{"label": key, "count": value} for key, value in recommendation_counter.most_common(5)],
    )


@app.delete("/admin/users/{target_username}", response_model=DeleteUserResponse)
def delete_admin_user(target_username: str, authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    require_admin(username)
    normalized = target_username.strip().lower()
    if normalized == "admin":
        raise HTTPException(status_code=400, detail="Primary admin account cannot be deleted")

    users = read_users()
    if normalized not in users:
        raise HTTPException(status_code=404, detail="User not found")

    del users[normalized]
    write_users(users)

    history = read_history()
    history.pop(normalized, None)
    write_history(history)

    return DeleteUserResponse(deleted=True, username=normalized)


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, http_request: Request, authorization: str | None = Header(default=None)):
    enforce_rate_limit(http_request, "predict")
    username = require_token(authorization)

    if request.communication not in set(display_data["Communication"]):
        raise HTTPException(status_code=400, detail="Invalid communication level")
    if request.coding not in set(display_data["Coding"]):
        raise HTTPException(status_code=400, detail="Invalid coding value")
    if request.interest not in set(display_data["Interest"]):
        raise HTTPException(status_code=400, detail="Invalid interest area")

    input_df = pd.DataFrame(
        {
            "Maths": [request.maths],
            "Science": [request.science],
            "Communication": [le_comm.transform([request.communication])[0]],
            "Coding": [le_coding.transform([request.coding])[0]],
            "Interest": [le_interest.transform([request.interest])[0]],
        }
    )

    probabilities = model.predict_proba(input_df)[0]
    top_indices = np.argsort(probabilities)[-3:][::-1]
    careers = le_career.inverse_transform(top_indices)

    predictions = []
    for index in range(len(careers)):
        career = careers[index]
        guidance = build_career_guidance(career, request)
        market_insights = build_market_insights(career, request)
        live_market = get_live_market_signal(career)
        courses, colleges = apply_preference_filters(guidance["courses"], guidance["colleges"], request)
        predictions.append(
            CareerPrediction(
                career=career,
                confidence=float(probabilities[top_indices[index]]),
                match_label=get_match_label(float(probabilities[top_indices[index]])),
                reason=build_reason_for_career(career, request),
                roadmap=guidance["roadmap"],
                courses=courses,
                colleges=colleges,
                skill_tips=guidance["skill_tips"],
                salary_range_inr_lpa=str(market_insights["salary_range_inr_lpa"]),
                future_demand=str(market_insights["future_demand"]),
                key_exams=list(market_insights["key_exams"]),
                estimated_years_to_enter=str(market_insights["estimated_years_to_enter"]),
                skill_gap_score=int(market_insights["skill_gap_score"]),
                live_market=live_market,
            )
        )

    feature_insights = [
        FeatureInsight(feature=feature_names[index], importance=float(importance))
        for index, importance in sorted(
            enumerate(model.feature_importances_),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    response = PredictResponse(
        accuracy=float(accuracy),
        generated_at=datetime.now(timezone.utc).isoformat(),
        profile_summary=build_profile_summary(request),
        feature_insights=feature_insights,
        predictions=predictions,
    )

    history = read_history()
    entry = build_history_entry(request, response)
    history.setdefault(username, [])
    history[username] = [entry.model_dump()] + history[username][:19]
    write_history(history)

    return response


@app.get("/model/metrics", response_model=ModelMetricsResponse)
def get_model_metrics(authorization: str | None = Header(default=None)):
    username = require_token(authorization)
    require_admin(username)
    return ModelMetricsResponse(
        accuracy=float(accuracy),
        precision_weighted=float(precision_weighted),
        recall_weighted=float(recall_weighted),
        f1_weighted=float(f1_weighted),
        cv_accuracy_mean=float(np.mean(cv_scores)),
        cv_accuracy_std=float(np.std(cv_scores)),
        confusion_matrix=conf_matrix.tolist(),
    )
