import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# let us import db.py / scraper.py that sit next to manage.py
sys.path.insert(0, str(BASE_DIR))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["corsheaders"]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = []

# the react app (on vercel) calls this api, so allow cross-origin requests
CORS_ALLOW_ALL_ORIGINS = True

# no local database - all data lives in supabase, reached over https
DATABASES = {}
USE_TZ = True
