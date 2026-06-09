import os
from pathlib import Path

# ── Auto-load .env from project root ─────────────────────────────────────────
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip().strip('"').strip("'"))

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "resumescout.db"

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set. Add it to your .env file.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# ── Admin panel ───────────────────────────────────────────────────────────────
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ── AI services (optional) ────────────────────────────────────────────────────
AI_GATEWAY_URL = os.environ.get("AI_GATEWAY_URL", "https://ai.gateway.resume.dev/v1/chat/completions")
AI_MODEL = os.environ.get("AI_MODEL", "google/gemini-2.5-flash")
LOVABLE_API_KEY = os.environ.get("LOVABLE_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://172.19.15.41:8080",
]
