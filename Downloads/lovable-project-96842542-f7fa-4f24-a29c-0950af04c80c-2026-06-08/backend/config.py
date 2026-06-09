import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "resumescout.db"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


# Auth — required; rotate immediately if previously exposed
JWT_SECRET = _require_env("JWT_SECRET")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must be at least 32 characters")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# Admin panel — required; no insecure defaults
ADMIN_USERNAME = _require_env("ADMIN_USERNAME")
ADMIN_PASSWORD = _require_env("ADMIN_PASSWORD")

# AI (optional — app works in mock mode without these)
AI_GATEWAY_URL = os.getenv("AI_GATEWAY_URL", "https://ai.gateway.resume.dev/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "google/gemini-2.5-flash")
LOVABLE_API_KEY = os.getenv("LOVABLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# CORS origins
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
