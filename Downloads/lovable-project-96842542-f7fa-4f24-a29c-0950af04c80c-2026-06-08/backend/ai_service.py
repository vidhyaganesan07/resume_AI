import json
import re

import httpx

from config import AI_GATEWAY_URL as GATEWAY_URL, AI_MODEL as MODEL, FIRECRAWL_API_KEY, LOVABLE_API_KEY


def _get_key() -> str | None:
    return LOVABLE_API_KEY


def _extract_skills(text: str) -> list[str]:
    keywords = [
        "python", "javascript", "typescript", "react", "node", "sql", "aws", "docker",
        "kubernetes", "java", "leadership", "communication", "agile", "git", "api",
        "machine learning", "data", "cloud", "html", "css", "fastapi", "postgres",
    ]
    lower = text.lower()
    found = [k.title() if k != "api" else "API" for k in keywords if k in lower]
    return found[:15] if found else ["Communication", "Problem Solving", "Teamwork", "Adaptability"]


def _mock_analyze(raw_text: str) -> dict:
    words = len(raw_text.split())
    ats = min(95, 55 + words // 20)
    health = min(92, 50 + words // 25)
    skills = _extract_skills(raw_text)
    return {
        "ats_score": ats,
        "health_score": health,
        "summary": f"Resume with ~{words} words. Solid foundation with room to strengthen impact statements and keyword alignment.",
        "skills": skills,
        "experience": [{"role": "Professional", "company": "Previous Employer", "duration": "2+ years"}],
        "education": [{"degree": "Bachelor's Degree", "institution": "University", "year": "2020"}],
        "missing_keywords": ["CI/CD", "Stakeholder Management", "Metrics", "Cross-functional", "Scalability"],
        "suggestions": [
            {"category": "impact", "title": "Quantify achievements", "detail": "Add metrics (%, $, time saved) to bullet points."},
            {"category": "keywords", "title": "Align with JD keywords", "detail": "Mirror terminology from target job descriptions."},
            {"category": "formatting", "title": "Consistent sections", "detail": "Use clear headings: Experience, Education, Skills."},
        ],
    }


def _mock_match(resume_text: str, jd_text: str) -> dict:
    resume_skills = set(s.lower() for s in _extract_skills(resume_text))
    jd_skills = set(s.lower() for s in _extract_skills(jd_text))
    matched = [s.title() for s in resume_skills & jd_skills] or ["Communication", "Problem Solving"]
    missing = [s.title() for s in jd_skills - resume_skills][:6] or ["Kubernetes", "GraphQL"]
    score = min(95, 40 + len(matched) * 8)
    return {
        "match_score": score,
        "matched_skills": matched[:8],
        "missing_skills": missing,
        "skill_match": {"technical": score, "experience": max(50, score - 10), "education": 70},
        "recommendation": f"Candidate shows {score}% fit. Strong on {', '.join(matched[:3])}. Consider upskilling in {', '.join(missing[:2]) or 'advanced tooling'}.",
    }


def _mock_rank(candidates: list[dict], jd_text: str) -> list[dict]:
    jd_skills = set(s.lower() for s in _extract_skills(jd_text))
    rankings = []
    for c in candidates:
        c_skills = set(s.lower() for s in (c.get("skills") or []))
        matched = list(c_skills & jd_skills)[:8]
        missing = list(jd_skills - c_skills)[:6]
        match_score = min(95, 35 + len(matched) * 10)
        rankings.append({
            "id": c["id"],
            "match_score": match_score,
            "matched_skills": [s.title() for s in matched],
            "missing_skills": [s.title() for s in missing],
            "reason": f"{'Strong' if match_score > 70 else 'Moderate'} fit based on skill overlap.",
        })
    return rankings


async def call_ai_json(system_prompt: str, user_prompt: str, mock_fn=None) -> dict:
    key = _get_key()
    if not key:
        return mock_fn(user_prompt) if mock_fn else {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            GATEWAY_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code == 429:
            raise ValueError("AI rate limit hit. Please try again in a moment.")
        if res.status_code == 402:
            raise ValueError("AI credits exhausted. Please top up Lovable AI credits.")
        if not res.is_success:
            raise ValueError(f"AI request failed ({res.status_code}): {res.text}")

        data = res.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            clean = re.sub(r"```json\s*|\s*```", "", text).strip()
            try:
                return json.loads(clean)
            except json.JSONDecodeError as exc:
                raise ValueError(f"AI returned invalid JSON: {clean[:200]}") from exc


async def analyze_resume_text(raw_text: str) -> dict:
    key = _get_key()
    if not key:
        return _mock_analyze(raw_text)

    return await call_ai_json(
        """You are a senior ATS and resume expert. Analyze the resume and return STRICT JSON with this exact schema:
{
  "ats_score": number (0-100),
  "health_score": number (0-100),
  "summary": string (2-3 sentences),
  "skills": string[] (top 15 technical + soft skills found),
  "experience": [{"role": string, "company": string, "duration": string}],
  "education": [{"degree": string, "institution": string, "year": string}],
  "missing_keywords": string[] (8-12 important keywords the resume lacks for general tech roles),
  "suggestions": [{"category": "formatting"|"content"|"keywords"|"impact", "title": string, "detail": string}]
}
Be concise. Return ONLY valid JSON, no markdown.""",
        f"Analyze this resume:\n\n{raw_text}",
        mock_fn=_mock_analyze,
    )


async def match_resume_jd(resume_text: str, jd_text: str) -> dict:
    key = _get_key()
    if not key:
        return _mock_match(resume_text, jd_text)

    result = await call_ai_json(
        """You are an expert recruiter AI. Compare the resume vs the job description and return STRICT JSON:
{
  "match_score": number (0-100),
  "matched_skills": string[],
  "missing_skills": string[],
  "skill_match": {"technical": number, "experience": number, "education": number} (each 0-100),
  "recommendation": string (concise hiring recommendation, 2-3 sentences)
}
Return ONLY valid JSON, no markdown.""",
        f"RESUME:\n{resume_text}\n\n---\n\nJOB DESCRIPTION:\n{jd_text}",
        mock_fn=lambda _: _mock_match(resume_text, jd_text),
    )
    return result


async def ask_assistant(question: str, resume_context: str = "") -> str:
    key = _get_key()
    system = f"You are a friendly, expert AI career assistant. Help users with resume improvements, interview prep, career advice, and job search. Be concise, actionable, and warm.{resume_context}"

    if not key:
        return (
            f"Great question! Based on your resume context, I'd suggest focusing on quantified achievements "
            f"and tailoring keywords to each role. Regarding \"{question[:80]}...\" — prioritize clarity, "
            f"impact metrics, and alignment with the job description. (Running in local mock mode — set LOVABLE_API_KEY for live AI.)"
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            GATEWAY_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
            },
        )
        if res.status_code == 429:
            raise ValueError("AI rate limit hit. Please try again shortly.")
        if res.status_code == 402:
            raise ValueError("AI credits exhausted.")
        if not res.is_success:
            raise ValueError(f"AI failed: {res.status_code}")
        data = res.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def rank_candidates(jd_title: str, jd_text: str, candidates: list[dict], filters: dict) -> list[dict]:
    key = _get_key()
    trimmed = [
        {
            "id": c["id"],
            "title": c["title"],
            "ats_score": c.get("ats_score", 0),
            "health_score": c.get("health_score", 0),
            "skills": c.get("skills", []),
            "excerpt": (c.get("raw_text") or "")[:3500],
        }
        for c in candidates
    ]

    if not key:
        parsed = {"rankings": _mock_rank(trimmed, jd_text)}
    else:
        filter_lines = [
            filters.get("seniority") and f"Seniority target: {filters['seniority']}",
            filters.get("mustHaveSkills") and f"MUST-HAVE skills: {filters['mustHaveSkills']}",
            filters.get("niceToHaveSkills") and f"Nice-to-have skills: {filters['niceToHaveSkills']}",
            isinstance(filters.get("minYears"), (int, float)) and f"Minimum years: {filters['minYears']}",
            filters.get("workMode") and f"Work mode: {filters['workMode']}",
            filters.get("domain") and f"Domain: {filters['domain']}",
            filters.get("cultureNotes") and f"Culture notes: {filters['cultureNotes']}",
        ]
        filter_block = "\n".join(line for line in filter_lines if line) or "(none)"
        user_prompt = f"JOB TITLE: {jd_title}\n\nJOB DESCRIPTION:\n{jd_text}\n\nRECRUITER FILTERS:\n{filter_block}\n\nCANDIDATES (JSON):\n{json.dumps(trimmed)}"

        parsed = await call_ai_json(
            """You are an expert technical recruiter. Return STRICT JSON:
{
  "rankings": [
    {"id": string, "match_score": number (0-100), "matched_skills": string[], "missing_skills": string[], "reason": string}
  ]
}
Score every candidate. Return ONLY valid JSON.""",
            user_prompt,
            mock_fn=lambda _: {"rankings": _mock_rank(trimmed, jd_text)},
        )

    rank_map = {r["id"]: r for r in parsed.get("rankings", [])}
    ranked = []
    for c in trimmed:
        r = rank_map.get(c["id"], {})
        match = max(0, min(100, int(r.get("match_score", 0))))
        combined = round(match * 0.6 + c["ats_score"] * 0.3 + c["health_score"] * 0.1)
        ranked.append({
            "resume_id": c["id"],
            "title": c["title"],
            "ats_score": c["ats_score"],
            "health_score": c["health_score"],
            "match_score": match,
            "combined_score": combined,
            "matched_skills": (r.get("matched_skills") or [])[:8],
            "missing_skills": (r.get("missing_skills") or [])[:6],
            "reason": r.get("reason", ""),
        })
    ranked.sort(key=lambda x: x["combined_score"], reverse=True)
    return ranked


async def scrape_url(url: str) -> tuple[str, str]:
    key = FIRECRAWL_API_KEY
    if not key:
        mock_md = f"""# Imported Profile

Source: {url}

## Summary
Experienced professional with a strong background in software development and team collaboration.

## Experience
**Software Engineer** — Tech Company (2020–Present)
- Built web applications using React, TypeScript, and Python
- Collaborated with cross-functional teams on product delivery

## Skills
Python, JavaScript, React, SQL, Git, Agile, Communication

## Education
B.S. Computer Science — State University (2020)
"""
        return mock_md, f"Imported · {url.split('//')[-1].split('/')[0]}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            "https://api.firecrawl.dev/v2/scrape",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True, "waitFor": 1500},
        )
        if res.status_code == 402:
            raise ValueError("Firecrawl credits exhausted. Please top up.")
        if not res.is_success:
            raise ValueError(f"Failed to fetch URL ({res.status_code})")
        data = res.json()
        md = data.get("data", {}).get("markdown") or data.get("markdown") or ""
        title = data.get("data", {}).get("metadata", {}).get("title") or data.get("metadata", {}).get("title") or ""
        if not md or len(md) < 80:
            raise ValueError(
                "Couldn't extract enough content. Try a public profile or paste text manually."
            )
        return md, title
