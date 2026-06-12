from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import ai_service
import database as db
from admin import router as admin_router
from auth import create_access_token, get_current_user, hash_password, verify_password
from config import ALLOWED_ORIGINS
from schemas import (
    AnalyzeRequest,
    AssistantRequest,
    AuthResponse,
    ImportUrlRequest,
    MatchRequest,
    RankRequest,
    RoleRequest,
    SignInRequest,
    SignUpRequest,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="ResumeScout API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(admin_router)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(body: SignUpRequest):
    if db.get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = db.create_user(body.email, hash_password(body.password), body.full_name)
    token = create_access_token(user["id"], user["email"])
    return {"access_token": token, "user": user}


@app.post("/api/auth/signin", response_model=AuthResponse)
def signin(body: SignInRequest):
    row = db.get_user_by_email(body.email)
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}
    token = create_access_token(row["id"], row["email"])
    return {"access_token": token, "user": user}


@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    row = db.get_user_by_id(user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}


# ── Resumes ───────────────────────────────────────────────────────────────────

@app.get("/api/resumes")
def list_my_resumes(user: dict = Depends(get_current_user)):
    return db.list_resumes(user["id"])


@app.get("/api/resumes/{resume_id}")
def get_resume(resume_id: str, user: dict = Depends(get_current_user)):
    row = db.get_resume(resume_id, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    return row


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str, user: dict = Depends(get_current_user)):
    db.delete_resume(resume_id, user["id"])
    return {"ok": True}


@app.post("/api/resumes/analyze")
async def analyze_resume(body: AnalyzeRequest, user: dict = Depends(get_current_user)):
    result = await ai_service.analyze_resume_text(body.rawText)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "title": body.title,
        "raw_text": body.rawText,
        "file_name": body.fileName,
        "ats_score": int(result.get("ats_score", 0)),
        "health_score": int(result.get("health_score", 0)),
        "summary": str(result.get("summary", "")),
        "skills": result.get("skills", []),
        "experience": result.get("experience", []),
        "education": result.get("education", []),
        "missing_keywords": result.get("missing_keywords", []),
        "suggestions": result.get("suggestions", []),
        "analyzed_at": now,
    }
    return db.upsert_resume(user["id"], payload, body.resumeId)


@app.post("/api/resumes/import-url")
async def import_resume_from_url(body: ImportUrlRequest, user: dict = Depends(get_current_user)):
    url = str(body.url)
    markdown, page_title = await ai_service.scrape_url(url)
    hostname = urlparse(url).hostname or "imported"
    hostname = hostname.removeprefix("www.")
    final_title = (body.title or page_title or f"Imported · {hostname}")[:200]
    result = await ai_service.analyze_resume_text(markdown)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "title": final_title,
        "raw_text": markdown[:50000],
        "file_name": url,
        "ats_score": int(result.get("ats_score", 0)),
        "health_score": int(result.get("health_score", 0)),
        "summary": str(result.get("summary", "")),
        "skills": result.get("skills", []),
        "experience": result.get("experience", []),
        "education": result.get("education", []),
        "missing_keywords": result.get("missing_keywords", []),
        "suggestions": result.get("suggestions", []),
        "analyzed_at": now,
    }
    return db.upsert_resume(user["id"], payload)


# ── Matches ───────────────────────────────────────────────────────────────────

@app.get("/api/matches")
def get_my_matches(user: dict = Depends(get_current_user)):
    return db.list_matches(user["id"])


@app.post("/api/matches")
async def match_resume_to_jd(body: MatchRequest, user: dict = Depends(get_current_user)):
    resume = db.get_resume(body.resumeId, user["id"])
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    jd = db.create_job_description(user["id"], body.jdTitle, body.jdCompany, body.jdText)
    result = await ai_service.match_resume_jd(resume["raw_text"], body.jdText)
    match = db.create_match_result(user["id"], resume["id"], jd["id"], {
        "match_score": int(result.get("match_score", 0)),
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "skill_match": result.get("skill_match", {}),
        "recommendation": str(result.get("recommendation", "")),
    })
    return {"match": match, "jd": jd}


# ── Assistant ─────────────────────────────────────────────────────────────────

@app.post("/api/assistant")
async def ask_assistant(body: AssistantRequest, user: dict = Depends(get_current_user)):
    resume_context = ""
    if body.resumeId:
        resume = db.get_resume(body.resumeId, user["id"])
        if resume:
            resume_context = f'\n\nUser\'s resume titled "{resume["title"]}":\n{resume["raw_text"]}'
    answer = await ai_service.ask_assistant(body.question, resume_context)
    return {"answer": answer}


# ── Roles ─────────────────────────────────────────────────────────────────────

@app.get("/api/role")
def get_my_role(user: dict = Depends(get_current_user)):
    roles = db.get_user_roles(user["id"])
    return {"roles": roles, "isRecruiter": "recruiter" in roles, "isAdmin": "admin" in roles}


@app.post("/api/role")
def set_my_role(body: RoleRequest, user: dict = Depends(get_current_user)):
    db.set_user_role(user["id"], body.role)
    return {"ok": True}


# ── Recruiter ─────────────────────────────────────────────────────────────────

@app.get("/api/candidates")
def list_candidates(user: dict = Depends(get_current_user)):
    roles = db.get_user_roles(user["id"])
    if "recruiter" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return db.list_candidates()


@app.post("/api/ranking")
async def rank_candidates_for_jd(body: RankRequest, user: dict = Depends(get_current_user)):
    roles = db.get_user_roles(user["id"])
    if "recruiter" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    candidates = db.list_analyzed_resumes(body.limit or 30)
    if not candidates:
        return []
    filters = body.filters.model_dump() if body.filters else {}
    return await ai_service.rank_candidates(body.jdTitle, body.jdText, candidates, filters)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
