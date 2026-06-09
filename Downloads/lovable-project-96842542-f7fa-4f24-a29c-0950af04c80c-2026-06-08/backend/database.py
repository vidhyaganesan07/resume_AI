import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('job_seeker', 'recruiter', 'admin')),
                created_at TEXT NOT NULL,
                UNIQUE(user_id, role)
            );

            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                file_name TEXT,
                ats_score INTEGER,
                health_score INTEGER,
                skills TEXT DEFAULT '[]',
                experience TEXT DEFAULT '[]',
                education TEXT DEFAULT '[]',
                suggestions TEXT DEFAULT '[]',
                missing_keywords TEXT DEFAULT '[]',
                summary TEXT,
                analyzed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_descriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                company TEXT,
                raw_text TEXT NOT NULL,
                required_skills TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS match_results (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                resume_id TEXT NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                job_description_id TEXT NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
                match_score INTEGER NOT NULL,
                skill_match TEXT DEFAULT '{}',
                matched_skills TEXT DEFAULT '[]',
                missing_skills TEXT DEFAULT '[]',
                recommendation TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def _parse_json(val, default):
    if val is None:
        return default
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default


def row_to_resume(row: sqlite3.Row, full: bool = False) -> dict:
    base = {
        "id": row["id"],
        "title": row["title"],
        "ats_score": row["ats_score"],
        "health_score": row["health_score"],
        "file_name": row["file_name"],
        "analyzed_at": row["analyzed_at"],
        "created_at": row["created_at"],
        "summary": row["summary"],
    }
    if full:
        base.update(
            {
                "user_id": row["user_id"],
                "raw_text": row["raw_text"],
                "skills": _parse_json(row["skills"], []),
                "experience": _parse_json(row["experience"], []),
                "education": _parse_json(row["education"], []),
                "suggestions": _parse_json(row["suggestions"], []),
                "missing_keywords": _parse_json(row["missing_keywords"], []),
                "updated_at": row["updated_at"],
            }
        )
    else:
        if "skills" in row.keys():
            base["skills"] = _parse_json(row["skills"], [])
        if "user_id" in row.keys():
            base["user_id"] = row["user_id"]
    return base


def create_user(email: str, password_hash: str, full_name: str | None) -> dict:
    user_id = str(uuid.uuid4())
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email.lower(), password_hash, full_name, now),
        )
        conn.execute(
            "INSERT INTO user_roles (id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, "job_seeker", now),
        )
    return {"id": user_id, "email": email.lower(), "full_name": full_name}


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()


def get_user_by_id(user_id: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_roles(user_id: str) -> list[str]:
    with get_db() as conn:
        rows = conn.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,)).fetchall()
        return [r["role"] for r in rows]


def set_user_role(user_id: str, role: str):
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_roles (id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, role, now),
        )


def list_resumes(user_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, title, ats_score, health_score, file_name, analyzed_at, created_at, summary
               FROM resumes WHERE user_id = ? ORDER BY created_at DESC""",
            (user_id,),
        ).fetchall()
        return [row_to_resume(r) for r in rows]


def get_resume(resume_id: str, user_id: str | None = None) -> dict | None:
    with get_db() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
        return row_to_resume(row, full=True) if row else None


def delete_resume(resume_id: str, user_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id))


def upsert_resume(user_id: str, payload: dict, resume_id: str | None = None) -> dict:
    now = _now()
    with get_db() as conn:
        if resume_id:
            cursor = conn.execute(
                """UPDATE resumes SET title=?, raw_text=?, file_name=?, ats_score=?, health_score=?,
                   summary=?, skills=?, experience=?, education=?, missing_keywords=?, suggestions=?,
                   analyzed_at=?, updated_at=? WHERE id=? AND user_id=?""",
                (
                    payload["title"],
                    payload["raw_text"],
                    payload.get("file_name"),
                    payload["ats_score"],
                    payload["health_score"],
                    payload["summary"],
                    json.dumps(payload.get("skills", [])),
                    json.dumps(payload.get("experience", [])),
                    json.dumps(payload.get("education", [])),
                    json.dumps(payload.get("missing_keywords", [])),
                    json.dumps(payload.get("suggestions", [])),
                    payload["analyzed_at"],
                    now,
                    resume_id,
                    user_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Resume {resume_id} not found or access denied")
            row = conn.execute(
                "SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
            ).fetchone()
        else:
            new_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO resumes (id, user_id, title, raw_text, file_name, ats_score, health_score,
                   summary, skills, experience, education, missing_keywords, suggestions, analyzed_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id,
                    user_id,
                    payload["title"],
                    payload["raw_text"],
                    payload.get("file_name"),
                    payload["ats_score"],
                    payload["health_score"],
                    payload["summary"],
                    json.dumps(payload.get("skills", [])),
                    json.dumps(payload.get("experience", [])),
                    json.dumps(payload.get("education", [])),
                    json.dumps(payload.get("missing_keywords", [])),
                    json.dumps(payload.get("suggestions", [])),
                    payload["analyzed_at"],
                    now,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM resumes WHERE id = ?", (new_id,)).fetchone()
    return row_to_resume(row, full=True)


def list_matches(user_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT m.id, m.match_score, m.recommendation, m.created_at, m.matched_skills,
                      m.missing_skills, m.resume_id, m.job_description_id,
                      j.title as jd_title, j.company as jd_company,
                      r.title as resume_title
               FROM match_results m
               JOIN job_descriptions j ON j.id = m.job_description_id
               JOIN resumes r ON r.id = m.resume_id
               WHERE m.user_id = ?
               ORDER BY m.created_at DESC LIMIT 50""",
            (user_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "match_score": row["match_score"],
                "recommendation": row["recommendation"],
                "created_at": row["created_at"],
                "matched_skills": _parse_json(row["matched_skills"], []),
                "missing_skills": _parse_json(row["missing_skills"], []),
                "resume_id": row["resume_id"],
                "job_description_id": row["job_description_id"],
                "job_descriptions": {"title": row["jd_title"], "company": row["jd_company"]},
                "resumes": {"title": row["resume_title"]},
            }
            for row in rows
        ]


def create_job_description(user_id: str, title: str, company: str | None, raw_text: str) -> dict:
    jd_id = str(uuid.uuid4())
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO job_descriptions (id, user_id, title, company, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (jd_id, user_id, title, company, raw_text, now),
        )
    return {"id": jd_id, "user_id": user_id, "title": title, "company": company, "raw_text": raw_text, "created_at": now}


def create_match_result(user_id: str, resume_id: str, jd_id: str, result: dict) -> dict:
    match_id = str(uuid.uuid4())
    now = _now()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO match_results (id, user_id, resume_id, job_description_id, match_score,
               skill_match, matched_skills, missing_skills, recommendation, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                match_id,
                user_id,
                resume_id,
                jd_id,
                result["match_score"],
                json.dumps(result.get("skill_match", {})),
                json.dumps(result.get("matched_skills", [])),
                json.dumps(result.get("missing_skills", [])),
                result.get("recommendation", ""),
                now,
            ),
        )
    return {
        "id": match_id,
        "user_id": user_id,
        "resume_id": resume_id,
        "job_description_id": jd_id,
        "match_score": result["match_score"],
        "skill_match": result.get("skill_match", {}),
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "recommendation": result.get("recommendation", ""),
        "created_at": now,
    }


def list_candidates() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, title, ats_score, health_score, summary, skills, created_at   
               FROM resumes WHERE analyzed_at IS NOT NULL
               ORDER BY ats_score DESC LIMIT 200"""
        ).fetchall()
        return [row_to_resume(r) for r in rows]


def list_analyzed_resumes(limit: int = 30) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, title, ats_score, health_score, raw_text, skills, summary
               FROM resumes WHERE analyzed_at IS NOT NULL
               ORDER BY ats_score DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "ats_score": r["ats_score"] or 0,
                "health_score": r["health_score"] or 0,
                "raw_text": r["raw_text"] or "",
                "skills": _parse_json(r["skills"], []),
                "summary": r["summary"],
            }
            for r in rows
        ]
