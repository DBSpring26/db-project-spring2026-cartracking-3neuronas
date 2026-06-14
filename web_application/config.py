import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
