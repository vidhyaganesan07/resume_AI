import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "resumescout.db"

# Auth
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is not set.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# Admin panel
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# AI
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
