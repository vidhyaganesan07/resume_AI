"""
Run the ResumeScout backend.
Usage:  python run.py
        python run.py --port 8080 --reload
"""
import argparse
import subprocess
import sys
from pathlib import Path

# Load .env from project root automatically
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            import os
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

parser = argparse.ArgumentParser(description="Start ResumeScout backend")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default="8000")
parser.add_argument("--reload", action="store_true", default=True)
args = parser.parse_args()

cmd = [
    sys.executable, "-m", "uvicorn", "main:app",
    "--host", args.host,
    "--port", str(args.port),
]
if args.reload:
    cmd.append("--reload")

print(f"\n🚀  ResumeScout backend starting on http://{args.host}:{args.port}")
print(f"📊  Admin panel → http://{args.host}:{args.port}/admin")
print(f"📖  API docs    → http://{args.host}:{args.port}/docs\n")

subprocess.run(cmd, cwd=Path(__file__).parent)
